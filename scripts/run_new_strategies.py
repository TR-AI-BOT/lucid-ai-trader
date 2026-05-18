"""
scripts/run_new_strategies.py
==============================
Backtests the 6 brand-new strategies on all 6 real trading pairs.
MNQ/MES/MYM = futures (1H + 1D)   |   ^GSPC/^NDX/^DJI = indices (1D only)
"""
from __future__ import annotations

import sys, time
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from backtesting.data_fetcher import fetch_ohlcv
from backtesting.engine import run_backtest

# ── symbols ────────────────────────────────────────────────────────────────────
FUTURES  = [("MNQ=F","MNQ"), ("MES=F","MES"), ("MYM=F","MYM")]
INDICES  = [("^GSPC","SPX"), ("^NDX","NAS"), ("^DJI","US30")]

END       = datetime.today().strftime("%Y-%m-%d")
START_1D  = "2019-01-01"
START_1H  = (datetime.today() - timedelta(days=700)).strftime("%Y-%m-%d")
START_30M = (datetime.today() - timedelta(days=58)).strftime("%Y-%m-%d")

# ── new strategies & their best timeframes ─────────────────────────────────────
#  order_block  → 1H futures, 1D indices
#  silver_bullet → 1H futures only (kill-zone windows)
#  supply_demand → 1D all
#  inside_bar   → 1D all
#  vwap_bands   → 1H futures only (intraday VWAP)
#  wyckoff      → 1D all

STRATEGIES = {
    "order_block":   {"label":"ICT Order Block",            "ft_tf":"1h","idx_tf":"1d"},
    "silver_bullet": {"label":"ICT Silver Bullet",          "ft_tf":"1h","idx_tf":None},
    "supply_demand": {"label":"Supply & Demand Zones",      "ft_tf":"1d","idx_tf":"1d"},
    "inside_bar":    {"label":"Inside Bar Breakout",        "ft_tf":"1d","idx_tf":"1d"},
    "vwap_bands":    {"label":"VWAP +/-2SD Bands",          "ft_tf":"1h","idx_tf":None},
    "wyckoff":       {"label":"Wyckoff Spring/Upthrust",    "ft_tf":"1d","idx_tf":"1d"},
}

def safe_run(name, symbol, start, end, tf):
    try:
        r = run_backtest(name, symbol, start, end, tf, starting_balance=100_000, qty=1)
        m = r["metrics"]
        return m["total_trades"], round(m["win_rate"],1), round(m["profit_factor"],2)
    except Exception as e:
        return 0, None, None

print("="*100)
print("Downloading data for 6 pairs …")
print("="*100)

# pre-warm downloads
for sym, lbl in FUTURES:
    for tf,st in [("1d",START_1D),("1h",START_1H)]:
        try:
            df = fetch_ohlcv(sym, st, END, tf)
            print(f"  {lbl} ({sym}) {tf}: {len(df)} bars")
        except Exception as e:
            print(f"  {lbl} ({sym}) {tf}: ERROR — {e}")

for sym, lbl in INDICES:
    try:
        df = fetch_ohlcv(sym, START_1D, END, "1d")
        print(f"  {lbl} ({sym}) 1d: {len(df)} bars")
    except Exception as e:
        print(f"  {lbl} ({sym}) 1d: ERROR — {e}")

print()
print("="*100)
print("Running 6 NEW strategies × 6 pairs …")
print("="*100)

rows = []
for sname, scfg in STRATEGIES.items():
    t0 = time.time()
    ft_tf  = scfg["ft_tf"]
    idx_tf = scfg["idx_tf"]
    ft_start  = START_1H if ft_tf == "1h" else START_1D
    idx_start = START_1D

    row = {"name": sname, "label": scfg["label"], "ft_tf": ft_tf, "idx_tf": idx_tf or "—"}
    totaltrades = 0

    # futures
    for sym, lbl in FUTURES:
        t, wr, pf = safe_run(sname, sym, ft_start, END, ft_tf)
        row[lbl] = (t, wr)
        totaltrades += t
        row["pf"] = pf  # last one wins, will average below

    # indices
    for sym, lbl in INDICES:
        if idx_tf is None:
            row[lbl] = (0, None)
        else:
            t, wr, pf = safe_run(sname, sym, idx_start, END, idx_tf)
            row[lbl] = (t, wr)
            totaltrades += t

    # avg win rate across all non-None
    wrs = [v[1] for v in [row["MNQ"],row["MES"],row["MYM"],row["SPX"],row["NAS"],row["US30"]] if v[1] is not None]
    row["avg_wr"] = round(sum(wrs)/len(wrs),1) if wrs else None
    row["total_trades"] = totaltrades

    # recompute combined PF
    all_pf = []
    for sym, lbl in FUTURES:
        try:
            r = run_backtest(sname, sym, ft_start, END, ft_tf)
            all_pf.append(r["metrics"]["profit_factor"])
        except: pass
    if idx_tf:
        for sym, lbl in INDICES:
            try:
                r = run_backtest(sname, sym, idx_start, END, idx_tf)
                all_pf.append(r["metrics"]["profit_factor"])
            except: pass
    row["avg_pf"] = round(sum(all_pf)/len(all_pf),2) if all_pf else 0

    # grade
    aw = row["avg_wr"] or 0
    ap = row["avg_pf"]
    if aw >= 62 and ap >= 1.3:   grade = "A"
    elif aw >= 55 and ap >= 1.1: grade = "B"
    elif aw >= 48 and ap >= 1.0: grade = "C"
    else:                        grade = "D"
    row["grade"] = grade

    elapsed = time.time() - t0
    print(f"  [{sname:<15}] avgWR={row['avg_wr']}%  PF={row['avg_pf']}  trades={totaltrades}  grade={grade}  [{elapsed:.1f}s]")
    rows.append(row)

rows.sort(key=lambda r: r["avg_wr"] or 0, reverse=True)

COL  = ["MNQ","MES","MYM","SPX","NAS","US30"]
COLS = " | ".join(f"{c:>10}" for c in COL)

print()
print("="*110)
print(f"NEW STRATEGY BACKTEST RESULTS  —  NAS100 / S&P500 / US30  (6 pairs)")
print("="*110)
print(f"{'Strategy':<22} {'TF':>4} | {'MNQ WR%':>8} | {'MES WR%':>8} | {'MYM WR%':>8} | {'SPX WR%':>8} | {'NAS WR%':>8} | {'US30 WR%':>9} | {'AVG WR':>7} | {'PF':>5} | {'GR':>4}")
print("-"*110)
for r in rows:
    def fmt(lbl):
        t, wr = r[lbl]
        return f"{wr:.1f}%" if wr is not None else "   N/A"
    tf_str = f"{r['ft_tf']}"
    aw = f"{r['avg_wr']:.1f}%" if r['avg_wr'] else "  N/A"
    print(f"  {r['label']:<20} {tf_str:>4} | {fmt('MNQ'):>8} | {fmt('MES'):>8} | {fmt('MYM'):>8} | {fmt('SPX'):>8} | {fmt('NAS'):>8} | {fmt('US30'):>9} | {aw:>7} | {r['avg_pf']:>5} | {r['grade']:>4}")

print("="*110)
print()
print("GRADE KEY:  A = WR≥62% + PF≥1.3  |  B = WR≥55% + PF≥1.1  |  C = WR≥48% + PF≥1.0  |  D = below C")
print()

# summary
grades = {"A":[],"B":[],"C":[],"D":[]}
for r in rows:
    grades[r["grade"]].append(r["label"])
print("SUMMARY")
print("-"*50)
for g in ["A","B","C","D"]:
    if grades[g]:
        print(f"  Grade {g}: {', '.join(grades[g])}")
best = max(rows, key=lambda r: r["avg_wr"] or 0)
print(f"\n  Best new strategy : {best['label']} @ {best['avg_wr']}% avg win rate (Grade {best['grade']})")
