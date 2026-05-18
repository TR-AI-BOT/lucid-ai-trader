"""Backtest all 5 harmonic pattern strategies across 6 pairs on 1H timeframe."""
from __future__ import annotations
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from backtesting.engine import run_backtest

FUTURES  = [("MNQ=F","MNQ"), ("MES=F","MES"), ("MYM=F","MYM")]
INDICES  = [("^GSPC","SPX"), ("^NDX","NAS"), ("^DJI","US30")]
ALL_SYMS = FUTURES + INDICES
END      = datetime.today().strftime("%Y-%m-%d")
START_1H = (datetime.today() - timedelta(days=700)).strftime("%Y-%m-%d")

HARMONICS = ["abcd", "gartley", "bat", "butterfly", "crab"]

def safe_run(name, symbol, start, tf):
    try:
        r = run_backtest(name, symbol, start, END, tf, starting_balance=100_000, qty=1)
        m = r["metrics"]
        if m["total_trades"] < 3:
            return None
        return (m["total_trades"], round(m["win_rate"], 1), round(m["profit_factor"], 2))
    except Exception:
        return None

def grade(wr, pf):
    if wr >= 62 and pf >= 1.3:   return "A"
    elif wr >= 55 and pf >= 1.1: return "B"
    elif wr >= 48 and pf >= 1.0: return "C"
    else:                        return "D"

def fmt(v):
    return f"{v[1]}%" if v else " N/A"

print()
print("=" * 92)
print("  HARMONIC PATTERN BACKTESTS  (1H, 700 days, MNQ/MES/MYM/SPX/NAS/US30)")
print("=" * 92)
print(f"  {'Strategy':<12} | {'MNQ':>6} | {'MES':>6} | {'MYM':>6} | {'SPX':>6} | {'NAS':>6} | {'US30':>6} | {'AVG WR':>8} | {'PF':>5} | GR")
print("-" * 92)

all_wrs = []
all_pfs = []

for strat in HARMONICS:
    row = {}
    for sym, lbl in ALL_SYMS:
        row[lbl] = safe_run(strat, sym, START_1H, "1h")

    wrs = [v[1] for v in row.values() if v]
    pfs = [v[2] for v in row.values() if v and v[0] >= 3]
    avg_wr = round(sum(wrs) / len(wrs), 1) if wrs else 0
    avg_pf = round(sum(pfs) / len(pfs), 2) if pfs else 0
    gr     = grade(avg_wr, avg_pf)

    if avg_wr > 0:
        all_wrs.append(avg_wr)
    if avg_pf > 0:
        all_pfs.append(avg_pf)

    print(
        f"  {strat.upper():<12} | {fmt(row['MNQ']):>6} | {fmt(row['MES']):>6} | "
        f"{fmt(row['MYM']):>6} | {fmt(row['SPX']):>6} | {fmt(row['NAS']):>6} | "
        f"{fmt(row['US30']):>6} | {avg_wr:>7}% | {avg_pf:>5} | {gr}"
    )

print("=" * 92)
overall_wr = round(sum(all_wrs) / len(all_wrs), 1) if all_wrs else 0
overall_pf = round(sum(all_pfs) / len(all_pfs), 2) if all_pfs else 0
print(f"  Combined avg WR: {overall_wr}%   Avg PF: {overall_pf}")
print()
