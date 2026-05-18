"""
scripts/run_final_2.py
======================
Backtests PDH/PDL Rejection (1H) and EMA200 Pullback (1D) on all 6 pairs.
"""
from __future__ import annotations
import sys, time
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from backtesting.data_fetcher import fetch_ohlcv
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

print("=" * 80)
print("BACKTESTING: PDH/PDL Rejection + EMA200 Pullback")
print("=" * 80)

# --- PDH/PDL on 1H (futures) and 1D (indices) ---
print("\n[1] PDH/PDL Rejection (pdh_pdl)")
pdh_results = {}
for sym, lbl in FUTURES:
    t, wr, pf = safe_run("pdh_pdl", sym, START_1H, END, "1h")
    pdh_results[lbl] = (t, wr, pf)
    print(f"    {lbl:6} 1H : trades={t:4}  WR={wr}%  PF={pf}")
for sym, lbl in INDICES:
    t, wr, pf = safe_run("pdh_pdl", sym, START_1D, END, "1d")
    pdh_results[lbl] = (t, wr, pf)
    print(f"    {lbl:6} 1D : trades={t:4}  WR={wr}%  PF={pf}")

pdh_wrs = [v[1] for v in pdh_results.values() if v[1] is not None]
pdh_pfs = [v[2] for v in pdh_results.values() if v[2] is not None]
pdh_avg_wr = round(sum(pdh_wrs) / len(pdh_wrs), 1) if pdh_wrs else 0
pdh_avg_pf = round(sum(pdh_pfs) / len(pdh_pfs), 2) if pdh_pfs else 0
print(f"    --- AVG WR: {pdh_avg_wr}%   AVG PF: {pdh_avg_pf}")

# --- EMA200 Pullback on 1D (all pairs) ---
print("\n[2] EMA200 Pullback (ema200_pullback)")
ema_results = {}
for sym, lbl in FUTURES:
    t, wr, pf = safe_run("ema200_pullback", sym, START_1D, END, "1d")
    ema_results[lbl] = (t, wr, pf)
    print(f"    {lbl:6} 1D : trades={t:4}  WR={wr}%  PF={pf}")
for sym, lbl in INDICES:
    t, wr, pf = safe_run("ema200_pullback", sym, START_1D, END, "1d")
    ema_results[lbl] = (t, wr, pf)
    print(f"    {lbl:6} 1D : trades={t:4}  WR={wr}%  PF={pf}")

ema_wrs = [v[1] for v in ema_results.values() if v[1] is not None]
ema_pfs = [v[2] for v in ema_results.values() if v[2] is not None]
ema_avg_wr = round(sum(ema_wrs) / len(ema_wrs), 1) if ema_wrs else 0
ema_avg_pf = round(sum(ema_pfs) / len(ema_pfs), 2) if ema_pfs else 0
print(f"    --- AVG WR: {ema_avg_wr}%   AVG PF: {ema_avg_pf}")

# Grade
def grade(wr, pf):
    if wr >= 62 and pf >= 1.3: return "A"
    elif wr >= 55 and pf >= 1.1: return "B"
    elif wr >= 48 and pf >= 1.0: return "C"
    else: return "D"

print("\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)
g1 = grade(pdh_avg_wr, pdh_avg_pf)
g2 = grade(ema_avg_wr, ema_avg_pf)
profitable1 = pdh_avg_pf >= 1.0
profitable2 = ema_avg_pf >= 1.0
print(f"  PDH/PDL Rejection   : AVG WR={pdh_avg_wr}%  PF={pdh_avg_pf}  Grade={g1}  {'ACTIVATE' if profitable1 else 'SKIP (PF<1.0)'}")
print(f"  EMA200 Pullback     : AVG WR={ema_avg_wr}%  PF={ema_avg_pf}  Grade={g2}  {'ACTIVATE' if profitable2 else 'SKIP (PF<1.0)'}")
print()
