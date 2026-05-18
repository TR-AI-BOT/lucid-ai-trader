"""
scripts/run_new2.py  —  EMA Cross + BB Squeeze backtest on all 6 pairs
"""
from __future__ import annotations
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from backtesting.engine import run_backtest

FUTURES = [("MNQ=F", "MNQ"), ("MES=F", "MES"), ("MYM=F", "MYM")]
INDICES = [("^GSPC", "SPX"), ("^NDX", "NAS"), ("^DJI", "US30")]

END      = datetime.today().strftime("%Y-%m-%d")
START_1D = "2019-01-01"
START_1H = (datetime.today() - timedelta(days=700)).strftime("%Y-%m-%d")

def safe_run(name, symbol, start, end, tf):
    try:
        r = run_backtest(name, symbol, start, end, tf, starting_balance=100_000, qty=1)
        m = r["metrics"]
        return m["total_trades"], round(m["win_rate"], 1), round(m["profit_factor"], 2)
    except Exception as e:
        print(f"    ERROR {name}/{symbol}/{tf}: {e}")
        return 0, None, None

def grade(wr, pf):
    if wr >= 62 and pf >= 1.3:   return "A"
    elif wr >= 55 and pf >= 1.1: return "B"
    elif wr >= 48 and pf >= 1.0: return "C"
    else:                        return "D"

def run_strat(sname, ft_tf, idx_tf, label):
    print(f"\n[{label}] {sname}  (futures={ft_tf}, indices={idx_tf})")
    results = {}
    ft_start = START_1H if ft_tf == "1h" else START_1D
    for sym, lbl in FUTURES:
        t, wr, pf = safe_run(sname, sym, ft_start, END, ft_tf)
        results[lbl] = (t, wr, pf)
        print(f"    {lbl:6} {ft_tf} : trades={t:4}  WR={wr}%  PF={pf}")
    for sym, lbl in INDICES:
        t, wr, pf = safe_run(sname, sym, START_1D, END, idx_tf)
        results[lbl] = (t, wr, pf)
        print(f"    {lbl:6} {idx_tf} : trades={t:4}  WR={wr}%  PF={pf}")
    wrs = [v[1] for v in results.values() if v[1] is not None and v[0] > 0]
    pfs = [v[2] for v in results.values() if v[2] is not None and v[0] > 0]
    avg_wr = round(sum(wrs)/len(wrs), 1) if wrs else 0
    avg_pf = round(sum(pfs)/len(pfs), 2) if pfs else 0
    g = grade(avg_wr, avg_pf)
    verdict = "ACTIVATE" if avg_pf >= 1.0 else "SKIP (PF<1.0)"
    print(f"    --- AVG WR: {avg_wr}%   AVG PF: {avg_pf}   Grade: {g}   {verdict}")
    return avg_wr, avg_pf, g

print("=" * 70)
print("NEW STRATEGY BACKTESTS: EMA Cross + BB Squeeze")
print("=" * 70)

ema_wr, ema_pf, ema_g = run_strat("ema_cross",  "1d", "1d", "1")
bb_wr,  bb_pf,  bb_g  = run_strat("bb_squeeze", "1d", "1d", "2")

print("\n" + "=" * 70)
print("VERDICT")
print("=" * 70)
print(f"  Dual EMA Cross (20/50)      : WR={ema_wr}%  PF={ema_pf}  Grade={ema_g}")
print(f"  BB Squeeze Breakout         : WR={bb_wr}%  PF={bb_pf}  Grade={bb_g}")
