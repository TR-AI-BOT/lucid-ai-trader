"""
LucidFlex $25K — FAST PASS (target: 1-2 weeks)
================================================
Same rules, new approach:
  - Risk $200/trade (0.8% of account) — 5x previous simulation
  - ALL strategies at ALL timeframes to maximize daily signal count
  - Dynamic risk reduction as account approaches the $24K floor
  - Target: pass in 5-10 trading days

LucidFlex $25K Rules:
  - Profit target: $1,200
  - Max loss:      $1,000 (floor = $24,000)
  - No daily loss limit
  - Consistency:   No single day > 50% of total cumulative profit
  - Min days:      2 trading days
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta
from collections import defaultdict

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")

def start(days):
    return (TODAY - timedelta(days=days)).strftime("%Y-%m-%d")

TF_DAYS = {"5m": 58, "15m": 58, "30m": 58, "1h": 700, "4h": 700}

INSTRUMENTS = [
    ("MNQ=F", "MNQ", 2.0),
    ("MES=F", "MES", 5.0),
    ("MYM=F", "MYM", 0.50),
]

# Full roster — ALL strategies at their best TF
ROSTER = [
    # S class
    ("trend_gap_fill",       "5m",  "S", 2.5),
    ("trend_gap_fill",       "15m", "S", 2.5),
    ("trend_gap_fill",       "30m", "S", 2.5),
    ("trend_gap_fill",       "1h",  "S", 2.5),
    ("gap_fill",             "5m",  "S", 2.5),
    ("gap_fill",             "15m", "S", 2.5),
    ("silver_bullet_strict", "30m", "S", 2.5),
    ("monday_gap_fill",      "15m", "S", 2.5),
    # A class
    ("order_block",          "1h",  "A", 2.0),
    ("bb_squeeze",           "30m", "A", 2.0),
    ("smc",                  "30m", "A", 2.0),
    # B class
    ("supertrend",           "30m", "B", 1.5),
    ("ema_cross",            "1h",  "B", 1.5),
    ("orb",                  "1h",  "B", 1.5),
    ("trend_follow",         "30m", "B", 1.5),
    ("inside_bar",           "15m", "B", 1.5),
    ("fvg",                  "30m", "B", 1.5),
    ("momentum",             "30m", "B", 1.5),
    ("donchian_break",       "30m", "B", 1.5),
    ("monthly_open",         "15m", "B", 1.5),
]

BASE_RISK     = 250.0    # $ risk per trade (0.5% of $50K)
ACCOUNT_START = 50_000.0
MAX_LOSS      = 2_000.0
FLOOR         = ACCOUNT_START - MAX_LOSS   # $48,000
PROFIT_TARGET = 3_000.0
MIN_DAYS      = 2


def collect_trades():
    all_trades = []
    print("\nCollecting trades...")
    seen = set()

    for sym, label, mult in INSTRUMENTS:
        for sid, tf, grade, rr in ROSTER:
            days = TF_DAYS.get(tf, 58)
            key  = (sid, tf, sym)
            if key in seen:
                continue
            seen.add(key)
            try:
                r = run_backtest(sid, sym, start(days), END, tf,
                                 starting_balance=100_000, qty=1)
                trades  = r.get("trades", [])
                metrics = r.get("metrics", {})
                if metrics.get("total_trades", 0) < 5 or not trades:
                    continue

                losses_pts = [abs(t["pnl"]) for t in trades if t["pnl"] < 0]
                if not losses_pts:
                    continue
                avg_loss_usd = (sum(losses_pts) / len(losses_pts)) * mult
                if avg_loss_usd <= 0:
                    continue

                scale = BASE_RISK / avg_loss_usd
                wr    = metrics.get("win_rate", 0)
                print(f"  {label} {sid:<22} {tf:<4}  trades={metrics['total_trades']:>3}  WR={wr:.1f}%")

                for t in trades:
                    ts_raw = str(t.get("timestamp", ""))
                    if not ts_raw or ts_raw == "None":
                        continue
                    try:
                        ts = datetime.fromisoformat(ts_raw.split("+")[0].split(".")[0])
                    except Exception:
                        continue
                    pnl = t["pnl"] * mult * scale
                    pnl = max(pnl, -BASE_RISK * 2.0)
                    pnl = min(pnl,  BASE_RISK * rr * 2.5)
                    all_trades.append({
                        "ts":    ts,
                        "date":  ts.date(),
                        "sym":   label,
                        "sid":   sid,
                        "tf":    tf,
                        "grade": grade,
                        "side":  t["side"],
                        "pnl":   round(pnl, 2),
                    })
            except Exception:
                continue

    all_trades.sort(key=lambda x: x["ts"])
    return all_trades


def simulate(trades):
    account    = ACCOUNT_START
    cum_pnl    = 0.0
    daily_pnl  = defaultdict(float)
    days_set   = set()
    log        = []
    passed = breached = False
    pass_date = breach_date = None
    consecutive_losses = 0

    print()
    print("=" * 80)
    print("  LUCIDFLEX $50K — CHALLENGE SIMULATION")
    print(f"  Risk ${BASE_RISK:.0f}/trade | Floor ${FLOOR:,.0f} | Target +${PROFIT_TARGET:,.0f}")
    print("=" * 80)
    print(f"  {'Date':<12} {'Sym':<4} {'Strategy':<22} {'TF':<4} {'Side':<5}"
          f"  {'P&L':>8}  {'Account':>10}  {'Total':>9}")
    print("-" * 80)

    for t in trades:
        if passed or breached:
            break

        d = t["date"]

        # Dynamic risk: reduce risk as we approach the floor
        headroom = account - FLOOR
        if headroom <= 200:
            risk_this_trade = min(50, headroom * 0.4)
        elif headroom <= 400:
            risk_this_trade = BASE_RISK * 0.5
        else:
            risk_this_trade = BASE_RISK

        # Scale P&L by adjusted risk ratio
        risk_ratio = risk_this_trade / BASE_RISK
        pnl = t["pnl"] * risk_ratio

        account   += pnl
        cum_pnl   += pnl
        daily_pnl[d] += pnl
        days_set.add(d)
        consecutive_losses = 0 if pnl > 0 else consecutive_losses + 1

        note = ""
        if account <= FLOOR:
            breached    = True
            breach_date = d
            note = "  <<< MAX LOSS HIT"
        elif cum_pnl >= PROFIT_TARGET and len(days_set) >= MIN_DAYS:
            best_day = max(daily_pnl.values())
            if best_day <= 0.50 * cum_pnl:
                passed    = True
                pass_date = d
                note = "  *** CHALLENGE PASSED ***"
            else:
                note = f"  (consistency: day ${best_day:.0f} > 50% of ${cum_pnl:.0f})"
        elif cum_pnl >= PROFIT_TARGET:
            note = "  (target hit — need 1 more day)"

        sign = "+" if pnl >= 0 else ""
        log.append({**t, "pnl": round(pnl,2), "account": account, "cum_pnl": cum_pnl})
        print(f"  {str(d):<12} {t['sym']:<4} {t['sid']:<22} {t['tf']:<4} {t['side']:<5}"
              f"  {sign}{pnl:>7.2f}  ${account:>9,.2f}  {sign}{cum_pnl:>7.2f}{note}")

    return log, passed, breached, pass_date, breach_date, daily_pnl, days_set, account, cum_pnl


def summary(log, passed, breached, pass_date, breach_date,
            daily_pnl, days_set, account, cum_pnl):

    # Group trades by date
    from collections import defaultdict as dd2
    by_day = dd2(list)
    for t in log:
        by_day[t["date"]].append(t)

    print()
    print("=" * 80)
    print("  DAY-BY-DAY BREAKDOWN  (every trade shown)")
    print("=" * 80)

    running = 0.0
    for d in sorted(by_day.keys()):
        day_trades = by_day[d]
        day_total  = sum(t["pnl"] for t in day_trades)
        running   += day_total
        wins_d     = sum(1 for t in day_trades if t["pnl"] > 0)
        loss_d     = sum(1 for t in day_trades if t["pnl"] <= 0)
        sign       = "+" if day_total >= 0 else ""
        rsign      = "+" if running >= 0 else ""
        print(f"\n  -- {str(d)}  |  {wins_d}W / {loss_d}L  |  Day P&L: {sign}${day_total:,.2f}"
              f"  |  Running: {rsign}${running:,.2f}")
        print(f"  {'Sym':<4} {'Strategy':<22} {'TF':<4} {'Side':<5}  {'Result':>7}  {'Acct':>10}")
        print(f"  {'-'*58}")
        for t in day_trades:
            result = "WIN  " if t["pnl"] > 0 else "LOSS "
            sign_t = "+" if t["pnl"] >= 0 else ""
            print(f"  {t['sym']:<4} {t['sid']:<22} {t['tf']:<4} {t['side']:<5}"
                  f"  {result} {sign_t}${abs(t['pnl']):>7.2f}  ${t['account']:>9,.2f}")

    wins  = [t for t in log if t["pnl"] > 0]
    loss  = [t for t in log if t["pnl"] <= 0]
    total = len(log)
    wr    = round(len(wins)/total*100, 1) if total else 0

    print()
    print("=" * 80)
    print("  FINAL VERDICT")
    print("=" * 80)

    if passed:
        first  = log[0]["date"]
        cal    = (pass_date - first).days
        max_dd = ACCOUNT_START - min(t["account"] for t in log)
        best   = max(daily_pnl.values())
        worst  = min(daily_pnl.values())
        pct50  = round(best / cum_pnl * 100, 1)

        print(f"  STATUS:           CHALLENGE PASSED")
        print(f"  Passed on:        {pass_date}")
        print(f"  Calendar days:    {cal}")
        print(f"  Trading days:     {len(days_set)}")
        print(f"  Total trades:     {total}  ({len(wins)}W / {len(loss)}L, {wr}% WR)")
        print(f"  Final account:    ${account:,.2f}")
        print(f"  Profit made:      +${cum_pnl:,.2f}  (needed ${PROFIT_TARGET:,.0f})")
        print(f"  Max drawdown:     -${max_dd:,.2f}  (limit was ${MAX_LOSS:,.0f})")
        print(f"  Max loss cushion: ${MAX_LOSS - max_dd:,.2f} remaining")
        print(f"  Best day:         +${best:,.2f}  ({pct50}% of total -- under 50% rule)")
        print(f"  Worst day:        ${worst:,.2f}")
        print()
        print(f"  RISK MANAGEMENT:")
        print(f"    Base risk/trade:  ${BASE_RISK:.0f} (0.5% of $50K)")
        print(f"    Dynamic scaling:  risk reduced as account approaches $24K floor")
        print(f"    Instruments:      MNQ ($2/pt), MES ($5/pt), MYM ($0.50/pt)")
        print(f"    Strategies used:  {len(set(t['sid'] for t in log))} unique strategies")
        print(f"    Avg trades/day:   {total/len(days_set):.1f}")
        print(f"    Avg daily profit: ${cum_pnl/len(days_set):,.2f}")

    elif breached:
        print(f"  STATUS:       FAILED — max loss breached on {breach_date}")
        print(f"  Account:      ${account:,.2f}  (lost ${ACCOUNT_START-account:,.2f})")
        print(f"  Trades:       {total} ({len(wins)}W / {len(loss)}L, {wr}%)")

    else:
        print(f"  STATUS:       IN PROGRESS — ${cum_pnl:,.2f} of ${PROFIT_TARGET:,.0f}")
    print()


def main():
    trades = collect_trades()
    if not trades:
        print("No trades — check connection.")
        return
    print(f"\n{len(trades)} trades collected across all strategies/instruments.")

    log, passed, breached, pd_, bd_, daily_pnl, days_set, acct, cum = simulate(trades)
    summary(log, passed, breached, pd_, bd_, daily_pnl, days_set, acct, cum)


main()
