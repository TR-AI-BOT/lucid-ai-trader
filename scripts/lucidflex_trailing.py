"""
LucidFlex Prop Firm Challenge — WITH PROPER EOD TRAILING DRAWDOWN
=================================================================
EOD Trailing Drawdown rules (Lucid Trading official):
  - MLL (Max Loss Limit / floor) starts at: account_start - max_loss
  - MLL TRAILS UP at end of each trading day based on highest EOD close
  - Formula: new_MLL = max(current_MLL, eod_close - max_loss)
  - Intraday highs do NOT move the MLL — only EOD closing balance
  - Once EOD close >= ITB (start + profit_target), MLL LOCKS permanently
  - Breach = account drops below current MLL at any point during session

$25K LucidFlex:
  - Start: $25,000  |  Target: $1,200  |  Max loss: $1,000
  - Initial MLL: $24,000  |  ITB lock point: $26,200

$50K LucidFlex:
  - Start: $50,000  |  Target: $3,000  |  Max loss: $2,000
  - Initial MLL: $48,000  |  ITB lock point: $53,000

Risk management chosen:
  - $25K: $150/trade | reduce to $75 when headroom < $400
  - $50K: $250/trade | reduce to $125 when headroom < $600
  - Dynamic risk reduction protects against trailing floor rising too fast
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

ROSTER = [
    ("trend_gap_fill",       "5m",  "S", 2.5),
    ("trend_gap_fill",       "15m", "S", 2.5),
    ("trend_gap_fill",       "30m", "S", 2.5),
    ("trend_gap_fill",       "1h",  "S", 2.5),
    ("gap_fill",             "5m",  "S", 2.5),
    ("gap_fill",             "15m", "S", 2.5),
    ("silver_bullet_strict", "30m", "S", 2.5),
    ("monday_gap_fill",      "15m", "S", 2.5),
    ("order_block",          "1h",  "A", 2.0),
    ("bb_squeeze",           "30m", "A", 2.0),
    ("smc",                  "30m", "A", 2.0),
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


def collect_trades():
    all_trades = []
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
                # store scale relative to $100 base (will rescale per challenge)
                base_scale = 100.0 / avg_loss_usd
                for t in trades:
                    ts_raw = str(t.get("timestamp", ""))
                    if not ts_raw or ts_raw == "None":
                        continue
                    try:
                        ts = datetime.fromisoformat(ts_raw.split("+")[0].split(".")[0])
                    except Exception:
                        continue
                    all_trades.append({
                        "ts":         ts,
                        "date":       ts.date(),
                        "sym":        label,
                        "sid":        sid,
                        "tf":         tf,
                        "grade":      grade,
                        "side":       t["side"],
                        "raw_pnl":    t["pnl"] * mult,   # in USD at qty=1
                        "base_scale": base_scale,
                        "rr":         rr,
                    })
            except Exception:
                continue
    all_trades.sort(key=lambda x: x["ts"])
    return all_trades


def simulate_challenge(trades, cfg):
    name          = cfg["name"]
    account       = cfg["start"]
    base_risk     = cfg["base_risk"]
    half_risk     = cfg["base_risk"] * 0.5
    max_loss      = cfg["max_loss"]
    target        = cfg["target"]
    min_headroom_full = cfg["base_risk"] * 3   # need 3× risk as headroom for full size
    mll           = cfg["start"] - max_loss     # initial floor
    itb           = cfg["start"] + target       # lock point
    mll_locked    = False
    min_days      = 2

    cum_pnl       = 0.0
    daily_pnl     = defaultdict(float)
    daily_trades  = defaultdict(list)
    days_traded   = set()
    log           = []
    passed = breached = False
    pass_date = breach_date = None
    eod_high      = account   # highest EOD close seen

    print()
    print("=" * 82)
    print(f"  {name} — WITH EOD TRAILING DRAWDOWN")
    print(f"  Risk: ${base_risk:.0f}/trade (half-size ${half_risk:.0f} when headroom < ${min_headroom_full:.0f})")
    print(f"  Target: +${target:,.0f} | Max Loss: ${max_loss:,.0f} | MLL starts: ${mll:,.0f} | ITB lock: ${itb:,.0f}")
    print("=" * 82)
    print(f"  {'Date':<12} {'Sym':<4} {'Strategy':<22} {'TF':<4} {'Side':<5}"
          f"  {'P&L':>8}  {'Account':>10}  {'MLL':>9}  {'Headroom':>9}")
    print("-" * 82)

    # Group trades by date for EOD MLL updates
    from itertools import groupby
    from operator import itemgetter
    trades_by_day = defaultdict(list)
    for t in trades:
        trades_by_day[t["date"]].append(t)

    for day in sorted(trades_by_day.keys()):
        if passed or breached:
            break

        day_trades = trades_by_day[day]
        days_traded.add(day)

        for t in day_trades:
            if passed or breached:
                break

            # Dynamic position sizing based on headroom above MLL
            headroom = account - mll
            if headroom < min_headroom_full:
                risk = half_risk
            else:
                risk = base_risk

            # Scale trade P&L to chosen risk
            scale = risk / 100.0 * t["base_scale"]  # base_scale was built on $100 risk
            pnl   = t["raw_pnl"] * scale
            pnl   = max(pnl, -risk * 2.0)
            pnl   = min(pnl,  risk * t["rr"] * 2.5)
            pnl   = round(pnl, 2)

            account    += pnl
            cum_pnl    += pnl
            daily_pnl[day] += pnl
            log.append({**t, "pnl": pnl, "account": account,
                        "cum_pnl": cum_pnl, "mll": mll, "headroom": headroom})
            daily_trades[day].append(log[-1])

            note = ""
            # Breach check — happens intraday
            if account <= mll:
                breached    = True
                breach_date = day
                note = "  <<< MLL BREACH"

            sign = "+" if pnl >= 0 else ""
            print(f"  {str(day):<12} {t['sym']:<4} {t['sid']:<22} {t['tf']:<4}"
                  f" {t['side']:<5}  {sign}{pnl:>7.2f}  ${account:>9,.2f}"
                  f"  ${mll:>8,.0f}  ${headroom:>8,.0f}{note}")

        if breached:
            break

        # ── EOD: update trailing MLL ──────────────────────────────────────────
        eod_close = account
        if not mll_locked:
            new_mll = max(mll, eod_close - max_loss)
            if new_mll != mll:
                print(f"  {'':12} {'--- EOD MLL UPDATE':50} "
                      f"${mll:,.0f} -> ${new_mll:,.0f}  (close: ${eod_close:,.2f})")
                mll = new_mll
            if eod_close >= itb:
                mll_locked = True
                print(f"  {'':12} {'*** MLL LOCKED at':38} ${mll:,.0f}"
                      f"  (account closed above ITB ${itb:,.0f})")

        # Check pass condition after EOD
        if cum_pnl >= target and len(days_traded) >= min_days and not passed:
            best_day = max(daily_pnl.values())
            if best_day <= 0.50 * cum_pnl:
                passed    = True
                pass_date = day
                print(f"\n  {'':12} *** CHALLENGE PASSED on {day} ***\n")
            else:
                print(f"  {'':12} (50% consistency: best day ${best_day:.0f}"
                      f" > 50% of ${cum_pnl:.0f} — keep trading)")

    return log, daily_pnl, daily_trades, days_traded, passed, breached, \
           pass_date, breach_date, account, cum_pnl, mll


def print_summary(cfg, log, daily_pnl, daily_trades, days_traded,
                  passed, breached, pass_date, breach_date, account, cum_pnl, mll):

    print()
    print("=" * 82)
    print(f"  DAY-BY-DAY BREAKDOWN — {cfg['name']}")
    print("=" * 82)

    running = 0.0
    for d in sorted(daily_trades.keys()):
        trades = daily_trades[d]
        day_p  = daily_pnl[d]
        running += day_p
        wins   = sum(1 for t in trades if t["pnl"] > 0)
        losses = sum(1 for t in trades if t["pnl"] <= 0)
        sign   = "+" if day_p >= 0 else ""
        rsign  = "+" if running >= 0 else ""
        pct    = f"  ({day_p/cum_pnl*100:.0f}% of total)" if cum_pnl > 0 else ""
        print(f"\n  -- {d}  |  {wins}W / {losses}L  |  "
              f"Day: {sign}${day_p:,.2f}  |  Running: {rsign}${running:,.2f}{pct}")
        print(f"  {'Sym':<4} {'Strategy':<22} {'TF':<4} {'Side':<5}  {'Result':<7}  {'P&L':>9}  {'Account':>10}  {'MLL':>9}")
        print(f"  {'-'*72}")
        for t in trades:
            res  = "WIN   " if t["pnl"] > 0 else "LOSS  "
            sign2 = "+" if t["pnl"] >= 0 else "-"
            print(f"  {t['sym']:<4} {t['sid']:<22} {t['tf']:<4} {t['side']:<5}"
                  f"  {res}  {sign2}${abs(t['pnl']):>8.2f}  ${t['account']:>9,.2f}  ${t['mll']:>8,.0f}")

    wins_total  = [t for t in log if t["pnl"] > 0]
    loss_total  = [t for t in log if t["pnl"] <= 0]
    total       = len(log)
    wr          = round(len(wins_total)/total*100, 1) if total else 0
    max_dd_from_start = cfg["start"] - min(t["account"] for t in log)
    best_day    = max(daily_pnl.values()) if daily_pnl else 0
    worst_day   = min(daily_pnl.values()) if daily_pnl else 0

    print()
    print("=" * 82)
    print(f"  FINAL VERDICT — {cfg['name']}")
    print("=" * 82)

    if passed:
        first  = log[0]["date"]
        cal    = (pass_date - first).days
        pct50  = round(best_day / cum_pnl * 100, 1) if cum_pnl > 0 else 0
        print(f"  STATUS:           CHALLENGE PASSED")
        print(f"  Passed on:        {pass_date}  ({cal} calendar days from first trade)")
        print(f"  Trading days:     {len(days_traded)}")
        print(f"  Total trades:     {total}  ({len(wins_total)}W / {len(loss_total)}L, {wr}% WR)")
        print(f"  Final account:    ${account:,.2f}")
        print(f"  Profit made:      +${cum_pnl:,.2f}  (target: ${cfg['target']:,.0f})")
        print(f"  Final MLL:        ${mll:,.0f}")
        print(f"  Max drawdown:     -${max_dd_from_start:,.2f}  (initial max was ${cfg['max_loss']:,.0f})")
        print(f"  Best day:         +${best_day:,.2f}  ({pct50}% of total — 50% rule: OK)")
        print(f"  Worst day:        ${worst_day:,.2f}")
        print()
        print(f"  TRAILING DRAWDOWN STATUS:")
        print(f"    The MLL rose from ${cfg['start']-cfg['max_loss']:,.0f} -> ${mll:,.0f} as profits built up.")
        print(f"    At no point did the account touch the trailing floor.")
    elif breached:
        print(f"  STATUS:           CHALLENGE FAILED — MLL BREACHED on {breach_date}")
        print(f"  Account dropped to: ${account:,.2f}")
        print(f"  MLL was:            ${mll:,.0f}")
        print(f"  Breach amount:      ${mll - account:,.2f} below floor")
        print(f"  Trades completed:   {total} ({len(wins_total)}W / {len(loss_total)}L, {wr}%)")
    else:
        print(f"  STATUS:           IN PROGRESS — ${cum_pnl:,.2f} of ${cfg['target']:,.0f}")

    print()


def main():
    print("Collecting all strategy trades...")
    trades = collect_trades()
    if not trades:
        print("No trades collected.")
        return
    print(f"{len(trades)} trades collected.\n")

    # ── $50K Challenge (fast pass attempt — target: 1 week) ──────────────────
    cfg_50k = {
        "name":      "LUCIDFLEX $50K",
        "start":     50_000.0,
        "max_loss":  2_000.0,
        "target":    3_000.0,
        "base_risk": 350.0,
    }
    r50 = simulate_challenge(trades, cfg_50k)
    print_summary(cfg_50k, *r50)


main()
