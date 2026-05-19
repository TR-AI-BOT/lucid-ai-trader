"""
LucidFlex Full Journey — Challenge → Buffer → Weekly Payouts
=============================================================
Uses the same recent 58-day data (all strategies, all TFs) for every phase.
The challenge runs first. Funded account starts on the day after challenge passes.

TIMELINE TARGET:
  Challenge:  1 week (5-8 trading days)
  Buffer:     1 week (5-7 trading days) — lock MLL + build headroom
  Payouts:    every week after

EOD TRAILING DRAWDOWN (both phases):
  MLL = max(current_MLL, EOD_close - max_loss)  each night
  Once account closes >= ITB, MLL locks permanently

RISK:
  $25K challenge:  $150/trade | daily cap $400 | daily stop $100
  $25K buffer:     $75/trade  | daily stop $300
  $25K payout:     $150/trade | daily stop $500

  $50K challenge:  $300/trade | daily cap $800 | daily stop $200
  $50K buffer:     $150/trade | daily stop $600
  $50K payout:     $250/trade | daily stop $1,000
  $50K cap: $2,000 gross/cycle (LucidFlex rule) => $1,800 to you
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta
from collections import defaultdict, deque

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


# ─── Data ────────────────────────────────────────────────────────────────────

def collect_trades():
    """All TFs, 58-day lookback — full signal stream for challenge + funded."""
    out, seen = [], set()
    for sym, label, mult in INSTRUMENTS:
        for sid, tf, grade, rr in ROSTER:
            key = (sid, tf, sym)
            if key in seen:
                continue
            seen.add(key)
            s = start_date(58)
            try:
                r = run_backtest(sid, sym, s, END, tf,
                                 starting_balance=100_000, qty=1)
                trades  = r.get("trades", [])
                metrics = r.get("metrics", {})
                if metrics.get("total_trades", 0) < 5 or not trades:
                    continue
                losses = [abs(t["pnl"]) for t in trades if t["pnl"] < 0]
                if not losses:
                    continue
                avg_loss_usd = (sum(losses) / len(losses)) * mult
                if avg_loss_usd <= 0:
                    continue
                base_scale = 100.0 / avg_loss_usd
                for t in trades:
                    ts_raw = str(t.get("timestamp", ""))
                    if not ts_raw or ts_raw == "None":
                        continue
                    try:
                        ts = datetime.fromisoformat(
                            ts_raw.split("+")[0].split(".")[0])
                    except Exception:
                        continue
                    out.append({
                        "ts": ts, "date": ts.date(), "sym": label,
                        "sid": sid, "tf": tf, "grade": grade,
                        "side": t["side"], "raw_pnl": t["pnl"] * mult,
                        "base_scale": base_scale, "rr": rr,
                    })
            except Exception:
                continue
    out.sort(key=lambda x: x["ts"])
    return out


def week_label(d):
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _apply_risk(t, risk, mll, account):
    """Scale a trade to the chosen risk, respecting dynamic headroom reduction."""
    headroom = account - mll
    r = risk if headroom >= risk * 3 else max(30.0, headroom * 0.4)
    scale    = r / 100.0 * t["base_scale"]
    pnl      = t["raw_pnl"] * scale
    # Never lose more than 20% of remaining headroom on a single trade
    max_loss = min(r * 2.0, max(5.0, headroom * 0.20))
    pnl      = max(pnl, -max_loss)
    pnl      = min(pnl,  r * t["rr"] * 2.5)
    return round(pnl, 2)


# ─── Display helpers ─────────────────────────────────────────────────────────

def _box(label, lines, width=108):
    W = "=" * width
    S = "-" * width
    print(f"\n{W}")
    print(f"  {label}")
    for ln in lines:
        print(f"  {ln}")
    print(W)

def _chal_header():
    print(f"  {'Day':<5} | {'Result':<12} | {'Trd':>4} | {'W':>4} | {'L':>4} | {'WR%':>5} | {'Risk':>6} "
          f"| {'Day P&L':>10} | {'Total P&L':>10} | {'Account':>11} | {'MLL':>9} | {'Room':>8}")
    print("-" * 108)

def _fund_header():
    print(f"  {'Day':<5} | {'Phase':<9} | {'Result':<12} | {'Trd':>4} | {'W':>4} | {'L':>4} | {'WR%':>5} | {'Risk':>6} "
          f"| {'Day P&L':>10} | {'Account':>11} | {'MLL':>9} | {'Room':>8}")
    print("-" * 108)

def _adapt_mult(outcomes):
    """Rolling 10-trade WR → risk multiplier + display label."""
    if len(outcomes) < 5:
        return 1.0, ""
    wr = sum(1 for x in outcomes if x) / len(outcomes)
    if wr >= 0.60: return 1.0,  ""
    if wr >= 0.45: return 0.85, " [CAUTIOUS]"
    if wr >= 0.30: return 0.70, " [DEFENSIVE]"
    return 0.60,               " [SURVIVAL]"

def _result_tag(day_pnl, cap, stop, trades):
    if day_pnl >= cap:
        return "WIN [CAP]"
    if day_pnl <= -stop and trades > 0:
        return "LOSS [STP]"
    return "WIN" if day_pnl > 0 else "LOSS"


# ─── Challenge ───────────────────────────────────────────────────────────────

def run_challenge(trades_by_day, cfg):
    name     = cfg["name"]
    account  = cfg["start"]
    max_loss = cfg["max_loss"]
    target   = cfg["target"]
    risk     = cfg["risk"]
    day_cap  = cfg["day_cap"]
    day_stop = cfg["day_stop"]

    mll        = account - max_loss
    itb        = account + target
    mll_locked = False
    cum_pnl    = 0.0
    cum_w = cum_l = 0
    daily_pnl   = defaultdict(float)
    days_traded = set()
    passed = breached = False
    pass_date = breach_date = None
    day_num = 0

    _box(
        f"CHALLENGE  |  {name}",
        [f"Risk: ${risk:.0f}/trade (fixed)  |  Daily Cap: +${day_cap:.0f}  |  Daily Stop: -${day_stop:.0f}",
         f"Target: +${target:,.0f}  |  Max Loss: ${max_loss:,.0f}  |  Starting MLL: ${mll:,.0f}  |  ITB: ${itb:,.0f}"]
    )
    _chal_header()

    for day in sorted(trades_by_day.keys()):
        if passed or breached:
            break
        day_num += 1
        days_traded.add(day)
        day_pnl = 0.0
        w = l = 0

        for t in trades_by_day[day]:
            if passed or breached:
                break
            if day_pnl >= day_cap or day_pnl <= -day_stop:
                break
            pnl      = _apply_risk(t, risk, mll, account)
            account += pnl
            day_pnl += pnl
            cum_pnl += pnl
            daily_pnl[day] += pnl
            if pnl > 0: w += 1; cum_w += 1
            else:        l += 1; cum_l += 1
            if account <= mll:
                breached = True; breach_date = day

        if breached:
            break

        # EOD trailing MLL
        mll_note = ""
        if not mll_locked:
            new_mll = max(mll, account - max_loss)
            if new_mll != mll:
                mll_note = "  MLL UP"
                mll = new_mll
            if account >= itb:
                mll_locked = True
                mll_note  += " [LOCKED]"

        result = _result_tag(day_pnl, day_cap, day_stop, w + l)
        day_wr   = f"{w/(w+l)*100:.0f}%" if (w+l) > 0 else "---"
        ps, cs   = ("+" if day_pnl >= 0 else ""), ("+" if cum_pnl >= 0 else "")
        room     = account - mll

        print(f"  D{day_num:02d}   | {result:<12} | {w+l:>4} | {w:>4} | {l:>4} | {day_wr:>5} | ${risk:>5.0f} "
              f"| {ps}{day_pnl:>9,.2f} | {cs}{cum_pnl:>9,.2f} | ${account:>10,.2f} | ${mll:>8,.0f} | ${room:>7,.0f}"
              f"{mll_note}")

        # Pass check (target hit + min 2 days + 50% rule)
        if cum_pnl >= target and len(days_traded) >= 2 and not passed:
            best = max(daily_pnl.values())
            if best < 0.50 * cum_pnl:
                passed    = True
                pass_date = day
                tdays     = len(days_traded)
                overall_wr = f"{cum_w/(cum_w+cum_l)*100:.1f}%" if (cum_w+cum_l) > 0 else "--"
                print("-" * 108)
                print(f"  *** CHALLENGE PASSED — Day {tdays}  |  Profit: +${cum_pnl:,.2f}  "
                      f"|  Overall WR: {overall_wr} ({cum_w}W / {cum_l}L) ***")
            else:
                pct = round(best / cum_pnl * 100, 1)
                print(f"  -- 50% rule: best day ${best:,.0f} = {pct}% of total — keep going")

    status = "PASSED" if passed else ("BREACHED" if breached else "IN PROGRESS")
    overall_wr = f"{cum_w/(cum_w+cum_l)*100:.1f}%" if (cum_w+cum_l) > 0 else "--"
    print("-" * 108)
    print(f"  STATUS: {status}  |  Final: ${account:,.2f}  |  MLL: ${mll:,.0f}  "
          f"|  Overall WR: {overall_wr} ({cum_w}W / {cum_l}L  |  {cum_w+cum_l} trades)")
    print("=" * 108)
    print()
    return passed, pass_date, account, mll


# ─── Funded ──────────────────────────────────────────────────────────────────

def run_funded(trades_by_day, cfg, start_from, challenge_passed):
    name           = cfg["name"]
    start_bal      = cfg["fund_start"]
    max_loss       = cfg["max_loss"]
    target         = cfg["target"]
    buf_risk_base  = cfg["buf_risk"]
    pay_risk_base  = cfg["pay_risk"]
    buf_threshold  = cfg["buf_threshold"]
    buf_stop       = cfg["buf_stop"]
    pay_stop       = cfg["pay_stop"]
    payout_cap     = cfg.get("payout_cap", 9_999_999)
    # aliases kept for compat
    buf_risk = buf_risk_base
    pay_risk = pay_risk_base

    account    = start_bal
    mll        = start_bal - max_loss
    itb        = start_bal + target
    mll_locked = False
    buf_done   = False
    buf_trading_days = 0

    payouts      = []
    cycle_profit = 0.0
    cycle_days   = 0
    total_earned = 0.0
    cycle_num    = 1

    daily_pnl   = defaultdict(float)
    log         = []
    breached    = False
    breach_date = None
    cum_w = cum_l = 0

    # Dynamic risk — starts at buffer base, adjusts day-to-day
    current_risk     = buf_risk_base
    recent_outcomes  = deque(maxlen=15)   # True=win, False=loss — rolling WR tracker

    active_days = [d for d in sorted(trades_by_day.keys()) if d >= start_from]

    tag = "POST-CHALLENGE" if challenge_passed else "SIM ONLY"
    _box(
        f"FUNDED ACCOUNT  |  {name}  [{tag}]",
        [f"Start: ${start_bal:,.0f}  |  MLL: ${mll:,.0f}  |  ITB: ${itb:,.0f}",
         f"BUFFER  Base ${buf_risk_base:.0f}/trade (scales down on losses)  |  Stop -${buf_stop:.0f}  "
         f"|  Goal: ${buf_threshold:,.0f} headroom + MLL locked",
         f"PAYOUT  Base ${pay_risk_base:.0f}/trade (win=+10% up to 2x, loss=RESET to base)  |  Stop -${pay_stop:.0f}  "
         f"|  5 trading days/cycle  |  90% to you"]
    )
    _fund_header()

    fund_day_num = 0
    for day in active_days:
        if breached or len(payouts) >= 10:
            break

        fund_day_num += 1
        risk = current_risk
        stop = buf_stop if not buf_done else pay_stop

        # ── Adaptive market logic ─────────────────────────────────────────────
        adapt_mult, adapt_label = _adapt_mult(recent_outcomes)
        day_risk      = max(30.0, round(risk * adapt_mult / 5) * 5)
        strat_streaks = defaultdict(int)   # per-strategy loss streak, resets daily
        profit_locked = False

        day_pnl = 0.0
        w = l = 0

        # Cap daily stop to 80% of headroom — never blow the MLL in one day
        headroom_sod   = account - mll
        effective_stop = min(stop, max(10.0, headroom_sod * 0.80))

        for t in trades_by_day[day]:
            if breached:
                break
            if day_pnl <= -effective_stop:
                break

            # Per-strategy cooldown: skip if this strategy lost 3 in a row today
            if strat_streaks[t["sid"]] >= 3:
                continue

            # Intraday profit lock: once up 5× BASE risk, trade at 60% risk
            # Uses base risk (not adaptive day_risk) so threshold doesn't shrink in cautious mode
            trade_risk = day_risk
            if day_pnl >= risk * 5:
                profit_locked = True
                trade_risk = max(30.0, round(day_risk * 0.60 / 5) * 5)

            pnl      = _apply_risk(t, trade_risk, mll, account)
            account += pnl
            day_pnl += pnl
            daily_pnl[day] += pnl
            log.append({**t, "pnl": pnl, "account": account, "mll": mll})
            if pnl > 0:
                w += 1; cum_w += 1
                recent_outcomes.append(True)
                strat_streaks[t["sid"]] = 0
            else:
                l += 1; cum_l += 1
                recent_outcomes.append(False)
                strat_streaks[t["sid"]] += 1
            if account <= mll:
                breached = True; breach_date = day

        if breached:
            break

        # EOD trailing MLL
        mll_note = ""
        if not mll_locked:
            new_mll = max(mll, account - max_loss)
            if new_mll != mll:
                mll_note = "  MLL UP"
                mll = new_mll
            if account >= itb:
                mll_locked = True
                mll_note  += " [LOCKED]"

        headroom_now = account - mll
        day_total = daily_pnl[day]
        if day_total < 0 and day_pnl <= -effective_stop and (w+l) > 0:
            result = "LOSS [STP]"
        elif day_total >= 0:
            result = "WIN"
        else:
            result = "LOSS"

        phase    = "BUFFER" if not buf_done else f"CYC #{cycle_num}"
        day_wr   = f"{w/(w+l)*100:.0f}%" if (w+l) > 0 else "---"
        ps       = "+" if day_total >= 0 else ""
        lock_tag = " [LOCK]" if profit_locked else ""
        note     = mll_note + adapt_label + lock_tag

        print(f"  D{fund_day_num:02d}   | {phase:<9} | {result:<12} | {w+l:>4} | {w:>4} | {l:>4} | {day_wr:>5} | ${day_risk:>5.0f} "
              f"| {ps}{day_total:>9,.2f} | ${account:>10,.2f} | ${mll:>8,.0f} | ${headroom_now:>7,.0f}"
              f"{note}")

        # ── Dynamic risk for NEXT day ──────────────────────────────────────────
        if not buf_done:
            # Buffer: fixed at base — no scaling, pure protection phase
            next_r = buf_risk_base
        else:
            # Payout: win → ride the streak (+10%, cap 2× base)
            #         loss → reset IMMEDIATELY back to base (not scale down)
            if day_total > 0:
                next_r = min(pay_risk_base * 2.0, current_risk * 1.10)
            else:
                next_r = pay_risk_base   # straight reset, no gradual decline
        current_risk = max(30.0, round(next_r / 5) * 5)   # round to nearest $5

        # ── Buffer → payout transition ─────────────────────────────────────────
        if not buf_done:
            buf_trading_days += 1
            if mll_locked and headroom_now >= buf_threshold:
                buf_done     = True
                cycle_profit = cycle_days = 0
                current_risk = pay_risk_base  # reset to payout base risk
                print("-" * 108)
                print(f"  BUFFER COMPLETE  |  Day {fund_day_num}  ({buf_trading_days} trading days)"
                      f"  |  MLL LOCKED  |  Headroom: ${headroom_now:,.0f}")
                print(f"  >>> PAYOUT PHASE STARTS  |  Base: ${pay_risk_base:.0f}/trade  "
                      f"|  Dynamic scaling ON  |  Stop -${pay_stop:.0f}")
                print("-" * 108)
        else:
            cycle_profit += day_total
            cycle_days   += 1   # all trading days count, not just profitable ones

            if cycle_days >= 5 and cycle_profit >= 500.0:
                gross        = min(cycle_profit, payout_cap)
                payout       = round(gross * 0.90, 2)
                prop         = round(gross * 0.10, 2)
                carry        = cycle_profit - gross
                total_earned += payout

                payouts.append({
                    "cycle": cycle_num, "day_num": fund_day_num,
                    "gross": gross, "payout": payout, "days": cycle_days,
                    "headroom": headroom_now, "total": total_earned,
                    "risk_used": risk,
                })

                capped = f"  (cap — actual cycle ${cycle_profit:,.2f})" if gross < cycle_profit else ""
                print("=" * 108)
                print(f"  PAYOUT #{cycle_num}  |  Funded Day {fund_day_num}  |  {cycle_days} trading days in cycle")
                print(f"  Cycle Profit:   ${cycle_profit:,.2f}{capped}")
                print(f"  YOUR 90%:       ${payout:,.2f}   <<< PAID OUT TO YOU")
                print(f"  Prop firm 10%:  ${prop:,.2f}")
                print(f"  Account stays:  ${account:,.2f}  (untouched)")
                print(f"  MLL locked at:  ${mll:,.0f}")
                print(f"  Headroom:       ${headroom_now:,.0f}")
                print(f"  Total earned:   ${total_earned:,.2f}")
                if carry > 0:
                    print(f"  Carry forward:  ${carry:,.2f}  (rolls into next cycle)")
                print("=" * 108)
                _fund_header()

                cycle_profit = carry
                cycle_days   = 0
                cycle_num   += 1

    return log, daily_pnl, payouts, breached, breach_date, account, mll, total_earned, cum_w, cum_l


# ─── Summary ─────────────────────────────────────────────────────────────────

def print_summary(cfg, log, daily_pnl, payouts, breached, breach_date,
                  account, mll, total_earned, cum_w, cum_l):
    W = "=" * 108
    S = "-" * 108
    print(f"\n{W}")
    print(f"  FUNDED SUMMARY  |  {cfg['name']}")
    print(W)

    # Payout table
    if payouts:
        print(f"  {'#':<4} | {'Funded Day':>11} | {'Cycle Days':>10} | {'Gross Profit':>13}"
              f" | {'YOUR 90%':>11} | {'Risk Used':>10} | {'Headroom':>10}")
        print(S)
        for p in payouts:
            capped = " [CAP]" if p["gross"] >= cfg.get("payout_cap", 9_999_999) - 1 else ""
            print(f"  #{p['cycle']:<3} | {'Day '+str(p['day_num']):>11} | {p['days']:>10} "
                  f"| ${p['gross']:>12,.2f} | ${p['payout']:>10,.2f}"
                  f" | ${p.get('risk_used',0):>9,.0f} | ${p['headroom']:>9,.0f}{capped}")
        print(S)

    wins  = [t for t in log if t["pnl"] > 0]
    loss  = [t for t in log if t["pnl"] <= 0]
    total = len(log)
    wr    = round(len(wins) / total * 100, 1) if total else 0
    n_d   = len(daily_pnl)
    days_won  = sum(1 for v in daily_pnl.values() if v > 0)
    days_lost = sum(1 for v in daily_pnl.values() if v <= 0)
    best  = max(daily_pnl.values()) if daily_pnl else 0
    worst = min(daily_pnl.values()) if daily_pnl else 0
    max_dd = cfg["fund_start"] - min(t["account"] for t in log) if log else 0
    d500  = sum(1 for v in daily_pnl.values() if v >= 500)
    d1k   = sum(1 for v in daily_pnl.values() if v >= 1_000)
    d2k   = sum(1 for v in daily_pnl.values() if v >= 2_000)

    n_p = len(payouts)
    if n_p > 1:
        first_d = payouts[0]["day_num"]
        last_d  = payouts[-1]["day_num"]
        avg_gap = (last_d - first_d) / (n_p - 1)
        monthly_cycles = 22 / max(avg_gap, 1)
        monthly = (total_earned / n_p) * monthly_cycles
    else:
        avg_gap = 5
        monthly_cycles = 22 / 5
        monthly = total_earned * monthly_cycles if n_p else 0

    print(f"\n  PAYOUTS")
    print(f"    Cycles completed:        {n_p}")
    print(f"    Avg trading days/cycle:  {avg_gap:.1f}")
    print(f"    TOTAL EARNED:            ${total_earned:,.2f}")
    if n_p:
        print(f"    Avg per cycle:           ${total_earned/n_p:,.2f}")
        print(f"    Projected monthly:       ${monthly:,.2f}  (~{monthly_cycles:.1f} cycles/month)")
    print(f"\n  TRADING STATS")
    print(f"    Total trades:            {total}  ({len(wins)}W / {len(loss)}L)  —  WR: {wr}%")
    print(f"    Trading days:            {n_d}  ({days_won} WIN days / {days_lost} LOSS days)")
    print(f"    Best single day:         +${best:,.2f}")
    print(f"    Worst single day:         ${worst:,.2f}")
    print(f"    Days >= $500:            {d500}/{n_d}  ({d500/max(n_d,1)*100:.0f}%)")
    print(f"    Days >= $1,000:          {d1k}/{n_d}  ({d1k/max(n_d,1)*100:.0f}%)")
    print(f"    Days >= $2,000:          {d2k}/{n_d}  ({d2k/max(n_d,1)*100:.0f}%)")
    print(f"\n  ACCOUNT HEALTH")
    print(f"    Max drawdown:            -${max_dd:,.2f}  (limit ${cfg['max_loss']:,.0f})")
    print(f"    Final account:           ${account:,.2f}  (stays in funded account)")
    print(f"    MLL locked permanently:  ${mll:,.0f}")
    print(f"    Final headroom:          ${account-mll:,.2f}")
    safety = "MLL NEVER TOUCHED — account 100% safe" if not breached else f"*** MLL BREACHED ***"
    print(f"    Safety status:           {safety}")
    print(W)
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Loading trades (all TFs, 58-day recent data)...")
    all_trades = collect_trades()
    trades_by_day = defaultdict(list)
    for t in all_trades:
        trades_by_day[t["date"]].append(t)
    all_dates = sorted(trades_by_day.keys())
    avg = sum(len(v) for v in trades_by_day.values()) / max(len(all_dates), 1)
    print(f"  {len(all_trades)} trades  |  {len(all_dates)} days  "
          f"|  avg {avg:.0f}/day  |  {all_dates[0]} to {all_dates[-1]}\n")

    first_day = all_dates[0]

    from datetime import timedelta

    # ══════════════════════════════════════════════════════════════════════════
    #  $25K  —  challenge $200/tr  |  buffer $150/tr dynamic  |  payout $200/tr dynamic
    # ══════════════════════════════════════════════════════════════════════════
    cfg_25_chal = {
        "name":     "LUCIDFLEX $25K",
        "start":    25_000.0, "max_loss": 1_000.0, "target": 1_200.0,
        "risk":     200.0, "day_cap": 700.0, "day_stop": 150.0,
    }
    passed_25, pass_date_25, _, _ = run_challenge(trades_by_day, cfg_25_chal)
    fund_start_25 = (pass_date_25 + timedelta(days=1)) if pass_date_25 else first_day

    cfg_25_fund = {
        "name":          "LUCIDFLEX $25K",
        "fund_start":    25_000.0, "max_loss": 1_000.0, "target": 1_200.0,
        "buf_risk":      150.0,  "pay_risk":  200.0,     # user-specified
        "buf_threshold": 1_000.0,
        "buf_stop":      400.0,  "pay_stop":  600.0,
        "payout_cap":    9_999_999,
    }
    r25 = run_funded(trades_by_day, cfg_25_fund, fund_start_25, passed_25)
    print_summary(cfg_25_fund, *r25)

    # ══════════════════════════════════════════════════════════════════════════
    #  $50K  —  challenge $300/tr  |  buffer $200/tr dynamic  |  payout $250/tr dynamic
    # ══════════════════════════════════════════════════════════════════════════
    cfg_50_chal = {
        "name":     "LUCIDFLEX $50K",
        "start":    50_000.0, "max_loss": 2_000.0, "target": 3_000.0,
        "risk":     300.0, "day_cap": 1_100.0, "day_stop": 200.0,
    }
    passed_50, pass_date_50, _, _ = run_challenge(trades_by_day, cfg_50_chal)
    fund_start_50 = (pass_date_50 + timedelta(days=1)) if pass_date_50 else first_day

    cfg_50_fund = {
        "name":          "LUCIDFLEX $50K",
        "fund_start":    50_000.0, "max_loss": 2_000.0, "target": 3_000.0,
        "buf_risk":      200.0,  "pay_risk":  250.0,     # user-specified
        "buf_threshold": 2_000.0,
        "buf_stop":      600.0,  "pay_stop":  1_000.0,
        "payout_cap":    2_000.0,
    }
    r50 = run_funded(trades_by_day, cfg_50_fund, fund_start_50, passed_50)
    print_summary(cfg_50_fund, *r50)


main()
