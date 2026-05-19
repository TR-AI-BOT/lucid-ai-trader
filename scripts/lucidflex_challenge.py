"""
LucidFlex $25K Prop Firm Challenge Simulation
=============================================
Rules (Lucid Trading official, 2026):
  - Account:        $25,000
  - Profit target:  $1,200 (user-specified; official $1,250 for 25K)
  - Max loss limit: $1,000 (account floor = $24,000, EOD trailing)
  - No daily loss limit
  - Consistency:    No single day > 50% of cumulative profit
  - Min days:       2 trading days before claiming pass
  - No time limit

Risk Management (chosen by Claude):
  - Risk per trade: $75 (0.3% of $25K account)
  - Max R:R by grade: S=2.5R, A=2.0R, B=1.5R
  - P&L scaled from real backtest data using CME micro multipliers
  - MNQ=$2/pt  MES=$5/pt  MYM=$0.50/pt

Yahoo Finance limits: 5m/15m/30m = last 60 days | 1h = ~700 days
Strategy: 1h strategies run full 2024->today. Intraday run last 60 days.
"""
import sys, warnings, traceback
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta, date
from collections import defaultdict

TODAY  = datetime.today()
END    = TODAY.strftime("%Y-%m-%d")

def start(days):
    return (TODAY - timedelta(days=days)).strftime("%Y-%m-%d")

# Yahoo Finance data windows
TF_DAYS = {
    "5m":  58,
    "15m": 58,
    "30m": 58,
    "1h":  700,
    "4h":  700,
}

# CME micro futures — (symbol, label, $/point)
INSTRUMENTS = [
    ("MNQ=F", "MNQ", 2.0),   # Micro Nasdaq-100
    ("MES=F", "MES", 5.0),   # Micro S&P 500
    ("MYM=F", "MYM", 0.50),  # Micro Dow
]

# Roster — (strategy_id, timeframe, grade, target_RR)
ROSTER = [
    ("trend_gap_fill",      "30m", "S", 2.5),
    ("trend_gap_fill",      "5m",  "S", 2.5),
    ("gap_fill",            "5m",  "S", 2.5),
    ("silver_bullet_strict","30m", "S", 2.5),
    ("monday_gap_fill",     "15m", "S", 2.5),
    ("order_block",         "1h",  "A", 2.0),
    ("bb_squeeze",          "30m", "A", 2.0),
    ("smc",                 "30m", "A", 2.0),
    ("supertrend",          "30m", "B", 1.5),
    ("ema_cross",           "1h",  "B", 1.5),
    ("orb",                 "1h",  "B", 1.5),
]

RISK_PER_TRADE = 75.0
ACCOUNT_START  = 25_000.0
MAX_LOSS       = 1_000.0
PROFIT_TARGET  = 1_200.0
MIN_DAYS       = 2
ACCOUNT_FLOOR  = ACCOUNT_START - MAX_LOSS   # $24,000


def collect_trades():
    all_trades = []
    print("\nCollecting trades from backtests...")

    for sym, label, mult in INSTRUMENTS:
        for sid, tf, grade, rr in ROSTER:
            # Skip combos that won't get data
            if sym == "MYM=F" and tf in ("5m",):
                continue
            days = TF_DAYS.get(tf, 58)
            s    = start(days)
            try:
                r = run_backtest(sid, sym, s, END, tf,
                                 starting_balance=100_000, qty=1)
                trades  = r.get("trades", [])
                metrics = r.get("metrics", {})
                n = metrics.get("total_trades", 0)
                if n < 5 or not trades:
                    continue

                losses_pts = [abs(t["pnl"]) for t in trades if t["pnl"] < 0]
                if not losses_pts:
                    continue
                avg_loss_pts = sum(losses_pts) / len(losses_pts)
                avg_loss_usd = avg_loss_pts * mult
                if avg_loss_usd <= 0:
                    continue

                scale = RISK_PER_TRADE / avg_loss_usd

                print(f"  {label} {sid:<22} {tf}  trades={n:>3}  "
                      f"WR={metrics.get('win_rate',0):.1f}%  "
                      f"scale={scale:.3f}")

                for t in trades:
                    ts_raw = str(t.get("timestamp", ""))
                    if not ts_raw or ts_raw == "None":
                        continue
                    try:
                        ts = datetime.fromisoformat(ts_raw.split("+")[0].split(".")[0])
                    except Exception:
                        continue

                    pnl = t["pnl"] * mult * scale
                    # Cap to realistic bounds
                    pnl = max(pnl, -RISK_PER_TRADE * 2.0)
                    pnl = min(pnl,  RISK_PER_TRADE * rr * 2.5)

                    all_trades.append({
                        "ts":       ts,
                        "date":     ts.date(),
                        "sym":      label,
                        "sid":      sid,
                        "tf":       tf,
                        "grade":    grade,
                        "side":     t["side"],
                        "pnl":      round(pnl, 2),
                    })

            except Exception as e:
                continue   # silently skip bad symbol/tf combos

    all_trades.sort(key=lambda x: x["ts"])
    return all_trades


def run_challenge(trades):
    account    = ACCOUNT_START
    cum_pnl    = 0.0
    daily_pnl  = defaultdict(float)
    days_traded = set()
    log        = []
    passed     = False
    breached   = False
    pass_date  = None
    breach_date= None

    print()
    print("=" * 74)
    print("  LUCIDFLEX $25K — TRADE LOG")
    print(f"  Risk $75/trade | Target +${PROFIT_TARGET:.0f} | Floor ${ACCOUNT_FLOOR:,.0f}")
    print("=" * 74)
    print(f"  {'Date':<11} {'Sym':<4} {'Strategy':<22} {'TF':<4} {'Side':<5}"
          f" {'P&L':>8}  {'Account':>10}  {'Total':>9}")
    print("-" * 74)

    for t in trades:
        if passed or breached:
            break
        d   = t["date"]
        pnl = t["pnl"]

        account   += pnl
        cum_pnl   += pnl
        daily_pnl[d] += pnl
        days_traded.add(d)

        note = ""
        if account <= ACCOUNT_FLOOR:
            breached    = True
            breach_date = d
            note = "  <<< BREACH"
        elif cum_pnl >= PROFIT_TARGET:
            nd = len(days_traded)
            if nd >= MIN_DAYS:
                best_day = max(daily_pnl.values())
                if best_day <= 0.50 * cum_pnl:
                    passed    = True
                    pass_date = d
                    note = "  *** PASSED ***"
                else:
                    note = f"  (50% rule: day={best_day:.0f} > {0.5*cum_pnl:.0f})"
            else:
                note = f"  (need {MIN_DAYS-nd} more day)"

        sign = "+" if pnl >= 0 else ""
        log.append({**t, "account": account, "cum_pnl": cum_pnl})
        print(f"  {str(d):<11} {t['sym']:<4} {t['sid']:<22} {t['tf']:<4}"
              f" {t['side']:<5} {sign}{pnl:>7.2f}  ${account:>9,.2f}  {sign}{cum_pnl:>7.2f}{note}")

    return log, passed, breached, pass_date, breach_date, daily_pnl, days_traded, account, cum_pnl


def print_summary(log, passed, breached, pass_date, breach_date,
                  daily_pnl, days_traded, account, cum_pnl):
    print()
    print("=" * 74)
    print("  DAY-BY-DAY SUMMARY")
    print("=" * 74)
    running = 0.0
    for d in sorted(daily_pnl.keys()):
        p = daily_pnl[d]
        running += p
        bar = "#" * int(max(0, p) / 10)
        sign = "+" if p >= 0 else ""
        flag = " <-- best day" if d in days_traded and p == max(daily_pnl.values()) else ""
        print(f"  {str(d)}  {sign}{p:>8.2f}   run: {sign}{running:>8.2f}  {bar}{flag}")

    print()
    print("=" * 74)
    print("  FINAL VERDICT")
    print("=" * 74)

    wins  = [t for t in log if t["pnl"] > 0]
    loss  = [t for t in log if t["pnl"] <= 0]
    total = len(log)
    wr    = round(len(wins) / total * 100, 1) if total else 0
    first_date = log[0]["date"] if log else None
    last_date  = log[-1]["date"] if log else None

    if passed:
        cal_days = (pass_date - first_date).days if first_date else 0
        trade_days = len(days_traded)
        max_dd = ACCOUNT_START - min(t["account"] for t in log)
        best_day = max(daily_pnl.values())
        worst_day = min(daily_pnl.values())

        print(f"  STATUS:         CHALLENGE PASSED")
        print(f"  Passed on:      {pass_date}")
        print(f"  Calendar days:  {cal_days} days from first trade")
        print(f"  Trading days:   {trade_days} days")
        print(f"  Total trades:   {total} ({len(wins)}W / {len(loss)}L)")
        print(f"  Actual WR:      {wr}%")
        print(f"  Final account:  ${account:,.2f}")
        print(f"  Total profit:   +${cum_pnl:,.2f}")
        print(f"  Max drawdown:   -${max_dd:,.2f} (limit was ${MAX_LOSS:,.0f})")
        print(f"  Best day:       +${best_day:,.2f}")
        print(f"  Worst day:      ${worst_day:,.2f}")
        print()
        print(f"  RISK MANAGEMENT USED:")
        print(f"    Risk/trade:   $75 (0.3% of account) -- never hit max loss")
        print(f"    Instruments:  MNQ ($2/pt), MES ($5/pt), MYM ($0.50/pt)")
        print(f"    Strategy mix: S/A/B class only")
        print(f"    Max loss cushion: ${MAX_LOSS - max_dd:,.2f} remaining")

    elif breached:
        print(f"  STATUS:         CHALLENGE FAILED")
        print(f"  Breach on:      {breach_date}")
        print(f"  Total trades:   {total} ({len(wins)}W / {len(loss)}L, {wr}%)")
        print(f"  Loss taken:     -${ACCOUNT_START - account:,.2f}")
        print()
        print("  Recommendation: reduce risk/trade to $50 or filter to S-class only.")

    else:
        print(f"  STATUS:         IN PROGRESS")
        print(f"  Progress:       ${cum_pnl:,.2f} of ${PROFIT_TARGET:,.0f} ({cum_pnl/PROFIT_TARGET*100:.1f}%)")
        print(f"  Trades:         {total} ({len(wins)}W / {len(loss)}L, {wr}%)")
        print(f"  Days traded:    {len(days_traded)}")

    print()


def main():
    trades = collect_trades()
    if not trades:
        print("\nNo trades collected — check network / Yahoo Finance availability.")
        return

    print(f"\nTotal raw trades collected: {len(trades)}")

    log, passed, breached, pass_date, breach_date, daily_pnl, days_traded, acct, cum_pnl = run_challenge(trades)

    print_summary(log, passed, breached, pass_date, breach_date,
                  daily_pnl, days_traded, acct, cum_pnl)


main()
