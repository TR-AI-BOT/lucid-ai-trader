"""
LucidFlex Funded Account — Buffer in Week 1, Payouts Every Week
================================================================
Fresh funded accounts:
  $25K: Start $25,000 | MLL $24,000 | ITB $26,200
  $50K: Start $50,000 | MLL $48,000 | ITB $53,000

DATA: All 20 strategies on 3 instruments using 55-day recent window.
This gives ~20-100 signals/day — an automated multi-strategy system running
simultaneously across MNQ, MES, MYM on 5m/15m/30m/1h timeframes. Each
"signal" is an independent position on a specific strategy/instrument/TF
combo, all managed by the bot in parallel.

GOAL:
  Week 1: Lock MLL + build buffer
  Week 2+: At least ONE payout per week, every week

RISK MANAGEMENT:
  $25K buffer phase:  $175/trade (aggressive enough to lock MLL & buffer in ~5 days)
  $25K payout phase:  $300/trade (targets $1,000+/day = $5,000+/week before cap)
  $50K buffer phase:  $300/trade (locks MLL + buffer in <5 days)
  $50K payout phase:  $500/trade (capped at $2,000/cycle = $1,800 to you)

  Dynamic: reduce to 50% risk if headroom < 3x trade risk.

PAYOUT RULES (LucidFlex funded):
  - 90% profit split | $500 minimum | 5 profitable trading days/cycle
  - NO consistency rule (evaluation-only)
  - $50K cap: $2,000 gross per cycle → $1,800 to you
  - Payouts come from profit share — trading account stays intact
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta, date
from collections import defaultdict

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")

def start_date(days):
    return (TODAY - timedelta(days=days)).strftime("%Y-%m-%d")

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


TF_DAYS = {"5m": 58, "15m": 58, "30m": 58, "1h": 700, "4h": 700}


def collect_trades():
    """Variable lookback per TF: 1h/4h use 700 days for rich history; shorter TFs use 58 days."""
    all_trades = []
    seen = set()
    for sym, label, mult in INSTRUMENTS:
        for sid, tf, grade, rr in ROSTER:
            key = (sid, tf, sym)
            if key in seen:
                continue
            seen.add(key)
            days = TF_DAYS.get(tf, 58)
            s = start_date(days)
            try:
                r = run_backtest(sid, sym, s, END, tf,
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
                        "raw_pnl":    t["pnl"] * mult,
                        "base_scale": base_scale,
                        "rr":         rr,
                    })
            except Exception:
                continue
    all_trades.sort(key=lambda x: x["ts"])
    return all_trades


def week_label(d):
    """Return YYYY-Www label for a date so we can group by week."""
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def simulate_funded(trades, cfg, max_cycles=6):
    name             = cfg["name"]
    start_bal        = cfg["start"]
    max_loss         = cfg["max_loss"]
    target           = cfg["target"]       # profit target to lock MLL
    buf_risk         = cfg["buf_risk"]     # Phase 1 risk
    pay_risk         = cfg["pay_risk"]     # Phase 2 risk
    buf_threshold    = cfg["buf_threshold"]
    payout_cap       = cfg.get("payout_cap", 9_999_999)
    payout_split     = 0.90
    min_payout_days  = 5
    min_withdrawal   = 500.0

    account     = start_bal
    mll         = start_bal - max_loss
    itb         = start_bal + target
    mll_locked  = False
    buf_done    = False

    payouts         = []
    cycle_profit    = 0.0
    cycle_days      = 0
    total_earned    = 0.0
    cycle_num       = 1

    daily_pnl       = defaultdict(float)
    log             = []
    breached        = False
    breach_date     = None

    trades_by_day = defaultdict(list)
    for t in trades:
        trades_by_day[t["date"]].append(t)

    # Track week-over-week for the "weekly payout" display
    week_payouts   = defaultdict(float)
    week_earnings  = defaultdict(float)

    print()
    print("=" * 82)
    print(f"  {name}")
    print(f"  Start: ${start_bal:,.0f} | MLL: ${mll:,.0f} | ITB: ${itb:,.0f}")
    print(f"  Phase 1  BUFFER: ${buf_risk:.0f}/trade | target headroom ${buf_threshold:,.0f} after MLL locks")
    print(f"  Phase 2  WEEKLY PAYOUTS: ${pay_risk:.0f}/trade | 5 profitable days = payout", end="")
    if payout_cap < 9_999_999:
        print(f" | cap ${payout_cap:,.0f}", end="")
    print()
    print("=" * 82)
    print(f"  {'Date':<12} {'Wk':<7} {'Phase':<8} {'#Trd':>4} {'W/L':>7}  "
          f"{'Day P&L':>9}  {'Account':>10}  {'MLL':>9}  {'Hdroom':>8}")
    print("-" * 82)

    for day in sorted(trades_by_day.keys()):
        if breached or len(payouts) >= max_cycles:
            break

        wk = week_label(day)
        day_trades = trades_by_day[day]
        day_wins = day_losses = 0

        for t in day_trades:
            if breached:
                break

            headroom = account - mll

            if not buf_done:
                # Buffer phase — conservative
                thresh = buf_risk * 3
                risk   = buf_risk if headroom >= thresh else max(50.0, headroom * 0.4)
            else:
                # Payout phase — full size
                thresh = pay_risk * 3
                risk   = pay_risk if headroom >= thresh else (
                         buf_risk if headroom >= buf_risk * 3 else max(50.0, headroom * 0.4)
                )

            scale = risk / 100.0 * t["base_scale"]
            pnl   = t["raw_pnl"] * scale
            pnl   = max(pnl, -risk * 2.0)
            pnl   = min(pnl,  risk * t["rr"] * 2.5)
            pnl   = round(pnl, 2)

            account      += pnl
            cycle_profit += pnl
            daily_pnl[day] += pnl
            log.append({**t, "pnl": pnl, "account": account, "mll": mll})
            if pnl > 0: day_wins += 1
            else: day_losses += 1

            if account <= mll:
                breached    = True
                breach_date = day

        if breached:
            break

        # EOD: update trailing MLL
        eod_close = account
        mll_note = ""
        if not mll_locked:
            new_mll = max(mll, eod_close - max_loss)
            if new_mll != mll:
                mll_note = f"  MLL {mll:,.0f}->{new_mll:,.0f}"
                mll = new_mll
            if eod_close >= itb:
                mll_locked = True
                mll_note += "  *** MLL LOCKED ***"

        headroom_now = account - mll
        day_total    = daily_pnl[day]
        s = "+" if day_total >= 0 else ""
        phase_str = "BUFFER" if not buf_done else f"CYC#{cycle_num}"
        day_mark  = "[+]" if day_total > 0 else "[-]"

        print(f"  {str(day):<12} {wk:<7} {phase_str:<8} {len(day_trades):>4} "
              f"{day_wins:>3}W/{day_losses:<3}L  {s}{day_total:>8,.2f}"
              f"  ${account:>9,.2f}  ${mll:>8,.0f}  ${headroom_now:>7,.0f}"
              f"  {day_mark}{mll_note}")

        # Check buffer completion
        if mll_locked and not buf_done and headroom_now >= buf_threshold:
            buf_done = True
            cycle_profit = 0.0
            cycle_days   = 0
            print(f"\n  {'='*78}")
            print(f"  BUFFER COMPLETE — {day}  |  Headroom ${headroom_now:,.0f}  |  "
                  f"Switching to ${pay_risk:.0f}/trade PAYOUT phase")
            print(f"  {'='*78}\n")

        # Count profitable day (payout phase only)
        if buf_done and day_total > 0:
            cycle_days += 1

        # Payout check
        if buf_done and cycle_days >= min_payout_days and cycle_profit >= min_withdrawal:
            gross    = min(cycle_profit, payout_cap)
            payout   = round(gross * payout_split, 2)
            prop_cut = round(gross - payout, 2)
            carry    = cycle_profit - gross
            total_earned += payout
            week_payouts[wk]  += payout
            week_earnings[wk] += payout

            payouts.append({
                "cycle":   cycle_num,
                "date":    day,
                "week":    wk,
                "gross":   gross,
                "payout":  payout,
                "prop":    prop_cut,
                "balance": account,
                "mll":     mll,
                "headroom":account - mll,
                "days":    cycle_days,
                "total_earned": total_earned,
            })

            cap_note = f"  (capped — cycle actually ${cycle_profit:,.2f})" if gross < cycle_profit else ""
            print(f"\n  {'-'*78}")
            print(f"  PAYOUT #{cycle_num}  [{day}]  {wk}")
            print(f"    Cycle profit:  ${cycle_profit:,.2f}{cap_note}")
            print(f"    YOUR 90%:      ${payout:,.2f}  <- IN YOUR POCKET")
            print(f"    Prop 10%:      ${prop_cut:,.2f}")
            print(f"    Account:       ${account:,.2f}  (unchanged — prop firm model)")
            print(f"    MLL:           ${mll:,.0f}  (LOCKED)")
            print(f"    Headroom:      ${account - mll:,.2f}")
            print(f"    Cumulative:    ${total_earned:,.2f} total earned so far")
            if carry > 0:
                print(f"    Carry fwd:     ${carry:,.2f} rolls into next cycle")
            print(f"  {'-'*78}\n")

            cycle_profit = carry
            cycle_days   = 0
            cycle_num   += 1

    return log, daily_pnl, payouts, breached, breach_date, account, mll, total_earned


def print_report(cfg, log, daily_pnl, payouts, breached, breach_date,
                 account, mll, total_earned):
    print()
    print("=" * 82)
    print(f"  FINAL REPORT — {cfg['name']}")
    print("=" * 82)

    if payouts:
        print(f"\n  PAYOUT TABLE:")
        print(f"  {'Cy':<4} {'Date':<12} {'Week':<8} {'Gross':>10} {'Your 90%':>10} "
              f"{'Prop 10%':>9} {'Days':>5} {'Headroom':>10}")
        print(f"  {'-'*72}")
        for p in payouts:
            cap_mark = "*" if p["gross"] < cfg.get("payout_cap", 9_999_999) - 1 else " "
            print(f"  {p['cycle']:<4} {str(p['date']):<12} {p['week']:<8} "
                  f"${p['gross']:>9,.2f} ${p['payout']:>9,.2f}"
                  f" ${p['prop']:>8,.2f} {p['days']:>5} ${p['headroom']:>9,.0f}{cap_mark}")

    wins   = [t for t in log if t["pnl"] > 0]
    losses = [t for t in log if t["pnl"] <= 0]
    total  = len(log)
    wr     = round(len(wins)/total*100, 1) if total else 0
    best_d  = max(daily_pnl.values()) if daily_pnl else 0
    worst_d = min(daily_pnl.values()) if daily_pnl else 0
    max_dd  = cfg["start"] - min(t["account"] for t in log) if log else 0
    n_days  = len(daily_pnl)

    print()
    print(f"  Payout cycles:       {len(payouts)}")
    print(f"  TOTAL EARNED:        ${total_earned:,.2f}  (your 90%)")
    print(f"  Prop firm cut:       ${sum(p['prop'] for p in payouts):,.2f}")
    print(f"  Final account:       ${account:,.2f}  (trading account)")
    print(f"  Final MLL:           ${mll:,.0f}  (LOCKED)")
    print(f"  Final headroom:      ${account - mll:,.2f}")
    print(f"  Max drawdown:        -${max_dd:,.2f}  (limit ${cfg['max_loss']:,.0f})")
    print(f"  Trades / WR:         {total} trades  ({len(wins)}W/{len(losses)}L, {wr}%)")
    print(f"  Trading days:        {n_days}")
    print(f"  Best day:            +${best_d:,.2f}")
    print(f"  Worst day:           ${worst_d:,.2f}")

    if payouts:
        avg     = total_earned / len(payouts)
        first_d = payouts[0]["date"]
        last_d  = payouts[-1]["date"]
        span    = (last_d - first_d).days
        avg_gap = span / (len(payouts)-1) if len(payouts) > 1 else span
        print(f"  First payout:        {first_d}")
        print(f"  Avg payout/cycle:    ${avg:,.2f}")
        print(f"  Avg days between:    {avg_gap:.0f} calendar days")
        monthly = avg * 30 / avg_gap if avg_gap > 0 else 0
        print(f"  Projected monthly:   ${monthly:,.2f}")

    if not breached:
        print(f"\n  Floor ${mll:,.0f} NEVER TOUCHED — account intact.")
    else:
        print(f"\n  *** MLL BREACHED on {breach_date} ***")
    print()


def main():
    print("Collecting trades (all 20 strategies, 3 instruments — 1h/4h use 700-day history)...")
    trades = collect_trades()
    if not trades:
        print("No trades.")
        return
    by_day = defaultdict(int)
    for t in trades:
        by_day[t["date"]] += 1
    avg_daily = sum(by_day.values()) / len(by_day) if by_day else 0
    all_dates = sorted(by_day.keys())
    print(f"{len(trades)} trades | {len(by_day)} trading days | avg {avg_daily:.0f} signals/day")
    print(f"Date range: {all_dates[0]} to {all_dates[-1]}\n")

    print("=" * 82)
    print("  STRATEGY SUMMARY")
    print("  Phase 1 — Week 1: Build buffer (lock MLL + grow headroom)")
    print("    $25K at $175/trade — fast MLL lock + $1,500 headroom in <5 days")
    print("    $50K at $300/trade — fast MLL lock + $3,000 headroom in <5 days")
    print()
    print("  Phase 2 — Week 2 onward: Weekly payouts")
    print("    $25K at $300/trade — target $1,000+/day -> $5,000+/week")
    print("    $50K at $500/trade — target $2,000+/week (capped -> $1,800 to you)")
    print("    5 profitable days = payout. With 20-100 signals/day, most weeks qualify.")
    print("=" * 82)

    cfg_25k = {
        "name":          "LUCIDFLEX $25K FUNDED",
        "start":         25_000.0,
        "max_loss":      1_000.0,
        "target":        1_200.0,
        "buf_risk":      175.0,       # Phase 1: enough to lock MLL fast
        "pay_risk":      300.0,       # Phase 2: $1,000+/day target
        "buf_threshold": 1_500.0,     # 1.5x max_loss buffer
        "payout_cap":    9_999_999,   # no cap on $25K
    }

    cfg_50k = {
        "name":          "LUCIDFLEX $50K FUNDED",
        "start":         50_000.0,
        "max_loss":      2_000.0,
        "target":        3_000.0,
        "buf_risk":      300.0,       # Phase 1
        "pay_risk":      500.0,       # Phase 2: capped anyway
        "buf_threshold": 3_000.0,     # 1.5x max_loss buffer
        "payout_cap":    2_000.0,     # LucidFlex $50K rule
    }

    r25 = simulate_funded(trades, cfg_25k, max_cycles=6)
    print_report(cfg_25k, *r25)

    r50 = simulate_funded(trades, cfg_50k, max_cycles=6)
    print_report(cfg_50k, *r50)


main()
