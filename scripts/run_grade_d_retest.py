"""
scripts/run_grade_d_retest.py
==============================
Re-tests Grade D strategies on their CORRECT timeframes.
"""
from __future__ import annotations
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from backtesting.engine import run_backtest

FUTURES = [("MNQ=F", "MNQ"), ("MES=F", "MES"), ("MYM=F", "MYM")]
INDICES = [("^GSPC", "SPX"), ("^NDX", "NAS"), ("^DJI", "US30")]

END       = datetime.today().strftime("%Y-%m-%d")
START_1D  = "2019-01-01"
START_1H  = (datetime.today() - timedelta(days=700)).strftime("%Y-%m-%d")
START_30M = (datetime.today() - timedelta(days=58)).strftime("%Y-%m-%d")
START_15M = (datetime.today() - timedelta(days=58)).strftime("%Y-%m-%d")

def safe_run(name, symbol, start, end, tf):
    try:
        r = run_backtest(name, symbol, start, end, tf, starting_balance=100_000, qty=1)
        m = r["metrics"]
        if m["total_trades"] < 3:
            return 0, None, None
        return m["total_trades"], round(m["win_rate"], 1), round(m["profit_factor"], 2)
    except Exception as e:
        print(f"    ERROR {name}/{symbol}/{tf}: {e}")
        return 0, None, None

def grade(wr, pf):
    if wr >= 62 and pf >= 1.3:   return "A"
    elif wr >= 55 and pf >= 1.1: return "B"
    elif wr >= 48 and pf >= 1.0: return "C"
    else:                        return "D"

def run_strat(sname, label, ft_tf, idx_tf, ft_start, idx_start=None):
    if idx_start is None:
        idx_start = START_1D
    print(f"\n  [{label}]  best TF: futures={ft_tf}  indices={idx_tf or 'N/A'}")
    results = {}
    for sym, lbl in FUTURES:
        t, wr, pf = safe_run(sname, sym, ft_start, END, ft_tf)
        results[lbl] = (t, wr, pf)
        status = f"WR={wr}%  PF={pf}  (n={t})" if wr is not None else f"n/a (n={t})"
        print(f"    {lbl:6} {ft_tf}: {status}")
    for sym, lbl in INDICES:
        if idx_tf is None:
            results[lbl] = (0, None, None)
            print(f"    {lbl:6}: (index — skipped, needs 24h session)")
        else:
            t, wr, pf = safe_run(sname, sym, idx_start, END, idx_tf)
            results[lbl] = (t, wr, pf)
            status = f"WR={wr}%  PF={pf}  (n={t})" if wr is not None else f"n/a (n={t})"
            print(f"    {lbl:6} {idx_tf}: {status}")
    wrs = [v[1] for v in results.values() if v[1] is not None]
    pfs = [v[2] for v in results.values() if v[2] is not None and v[0] >= 3]
    avg_wr = round(sum(wrs)/len(wrs), 1) if wrs else 0
    avg_pf = round(sum(pfs)/len(pfs), 2) if pfs else 0
    g = grade(avg_wr, avg_pf)
    print(f"    => AVG WR: {avg_wr}%   AVG PF: {avg_pf}   Grade: {g}")
    return avg_wr, avg_pf, g, ft_tf, idx_tf

print("=" * 72)
print("GRADE D RE-TEST — CORRECT TIMEFRAMES")
print("=" * 72)

results_table = {}

# Break & Retest — 15m intraday (breakout + confirmation on tight bars)
r = run_strat("break_retest",    "Break & Retest",             "15m", "1h",  START_15M, START_1H)
results_table["Break & Retest"] = r

# FVG — 15m (FVGs are intraday displacement gaps)
r = run_strat("fvg",             "Fair Value Gap (FVG)",       "15m", "1h",  START_15M, START_1H)
results_table["FVG"] = r

# IFVG — 15m
r = run_strat("ifvg",            "Inverse FVG (IFVG)",         "15m", "1h",  START_15M, START_1H)
results_table["IFVG"] = r

# Fibonacci — 1H (shows clear swing levels; 1D too coarse)
r = run_strat("fib_retracement", "Fibonacci Retracement",      "1h",  "1d",  START_1H)
results_table["Fibonacci"] = r

# Fade — 15m (counter-trend fades are intraday, mean-revert at extreme)
r = run_strat("fade",            "Fade (Counter-Trend)",       "15m", "1h",  START_15M, START_1H)
results_table["Fade"] = r

# Asia Range — 30m (needs sub-hour resolution to build Asia session range)
r = run_strat("asia_range",      "Asia Range Bull/Bear",       "30m", None,  START_30M)
results_table["Asia Range"] = r

# News Continuation — 15m (news momentum plays out fast, intraday)
r = run_strat("news_continuation","News Continuation",         "15m", None,  START_15M)
results_table["News Continuation"] = r

# BOS — 15m (structural breaks show clearly on intraday)
r = run_strat("bos",             "Break of Structure (BOS)",   "15m", "1h",  START_15M, START_1H)
results_table["BOS"] = r

# SMC — 15m (all ICT/SMC concepts designed for intraday timeframes)
r = run_strat("smc",             "Smart Money Concept (SMC)",  "15m", "1h",  START_15M, START_1H)
results_table["SMC"] = r

# ICT Order Block — 15m (OBs are intraday displacement last-candle POIs)
r = run_strat("order_block",     "ICT Order Block",            "15m", "1h",  START_15M, START_1H)
results_table["Order Block"] = r

# ── Final comparison table ─────────────────────────────────────────────────
print()
print("=" * 72)
print("FINAL COMPARISON — CORRECT TF vs OLD TF")
print("=" * 72)
old_grades = {
    "Break & Retest":     (35.3, 1.11, "D", "1h/1d"),
    "FVG":                (49.9, 0.78, "D", "1h/1d"),
    "IFVG":               (35.9, 1.04, "D", "1h/1d"),
    "Fibonacci":          ( 0.0, 0.00, "D", "1d"),
    "Fade":               (36.9, 1.83, "D", "1h/1d"),
    "Asia Range":         ( 0.0, 0.00, "D", "1h"),
    "News Continuation":  (36.2, 1.27, "D", "1h/1d"),
    "BOS":                (43.6, 1.09, "D", "1h/1d"),
    "SMC":                (54.0, 0.62, "D", "1h/1d"),
    "Order Block":        (49.1, 0.91, "D", "1h/1d"),
}
print(f"  {'Strategy':<25} | {'OLD TF':>6} {'OLD WR':>7} {'OLD GR':>6} | {'NEW TF':>8} {'NEW WR':>7} {'NEW GR':>6}")
print("-" * 72)
for name, (avg_wr, avg_pf, g, ft_tf, idx_tf) in results_table.items():
    old_wr, old_pf, old_g, old_tf = old_grades[name]
    new_tf = ft_tf if idx_tf is None else f"{ft_tf}/{idx_tf}"
    arrow = "=>" if g != old_g else "  "
    print(f"  {name:<25} | {old_tf:>6} {old_wr:>6.1f}% {old_g:>6} | {new_tf:>8} {avg_wr:>6.1f}% {g:>6}  {arrow}")
