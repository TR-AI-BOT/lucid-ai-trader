"""
scripts/run_candidates.py
=========================
Tests wyckoff + silver_bullet to find 2 profitable strategies for the 20-strategy target.
"""
from __future__ import annotations
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from backtesting.engine import run_backtest

FUTURES = [("MNQ=F", "MNQ"), ("MES=F", "MES"), ("MYM=F", "MYM")]
INDICES = [("^GSPC", "SPX"), ("^NDX", "NAS"), ("^DJI", "US30")]

END = datetime.today().strftime("%Y-%m-%d")
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
    if wr >= 62 and pf >= 1.3: return "A"
    elif wr >= 55 and pf >= 1.1: return "B"
    elif wr >= 48 and pf >= 1.0: return "C"
    else: return "D"

def run_strategy(sname, tf_futures, tf_indices, label):
    print(f"\n[{label}] {sname}  (futures={tf_futures}, indices={tf_indices or 'N/A'})")
    results = {}
    start_ft = START_1H if tf_futures == "1h" else START_1D
    for sym, lbl in FUTURES:
        t, wr, pf = safe_run(sname, sym, start_ft, END, tf_futures)
        results[lbl] = (t, wr, pf)
        print(f"    {lbl:6} {tf_futures} : trades={t:4}  WR={wr}%  PF={pf}")
    if tf_indices:
        for sym, lbl in INDICES:
            t, wr, pf = safe_run(sname, sym, START_1D, END, tf_indices)
            results[lbl] = (t, wr, pf)
            print(f"    {lbl:6} {tf_indices} : trades={t:4}  WR={wr}%  PF={pf}")
    wrs = [v[1] for v in results.values() if v[1] is not None]
    pfs = [v[2] for v in results.values() if v[2] is not None]
    avg_wr = round(sum(wrs)/len(wrs), 1) if wrs else 0
    avg_pf = round(sum(pfs)/len(pfs), 2) if pfs else 0
    g = grade(avg_wr, avg_pf)
    print(f"    --- AVG WR: {avg_wr}%   AVG PF: {avg_pf}   Grade: {g}   {'ACTIVATE' if avg_pf >= 1.0 else 'SKIP'}")
    return avg_wr, avg_pf, g

print("=" * 70)
print("CANDIDATE STRATEGY BACKTESTS")
print("=" * 70)

wy_wr, wy_pf, wy_g  = run_strategy("wyckoff",       "1d", "1d", "A")
sb_wr, sb_pf, sb_g  = run_strategy("silver_bullet",  "1h", None, "B")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Wyckoff Spring/Upthrust : WR={wy_wr}%  PF={wy_pf}  Grade={wy_g}")
print(f"  ICT Silver Bullet       : WR={sb_wr}%  PF={sb_pf}  Grade={sb_g}")
