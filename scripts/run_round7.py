"""
scripts/run_round7.py
=====================
Backtests the 10 Round-7 strategies across all 6 pairs and key timeframes.
Target: find strategies with individual WR >= 70% to push combined portfolio
        from 62.3% toward the 70% goal.

Best TF tested per strategy:
  trend_gap_fill   → 5m (intraday), 1d (daily)
  monday_gap_fill  → 5m (intraday), 1d (daily)
  quarterly_open   → 1d
  weekly_open      → 1d, 1h
  turtle_soup      → 1d, 1h
  three_push_fade  → 1d, 1h
  failed_breakdown → 1d, 1h
  eom_rebalance    → 1d
  overnight_drift  → 1d only
  kijun_bounce     → 1d, 1h
"""
from __future__ import annotations

import sys, time
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from backtesting.data_fetcher import fetch_ohlcv
from backtesting.engine import run_backtest

FUTURES = [("MNQ=F", "MNQ"), ("MES=F", "MES"), ("MYM=F", "MYM")]
INDICES = [("^GSPC", "SPX"), ("^NDX",  "NAS"), ("^DJI",  "US30")]

END      = datetime.today().strftime("%Y-%m-%d")
START_1D = "2019-01-01"
START_1H = (datetime.today() - timedelta(days=700)).strftime("%Y-%m-%d")
START_5M = (datetime.today() - timedelta(days=58)).strftime("%Y-%m-%d")

# strategy_name → {"ft_tf": timeframe_for_futures, "idx_tf": timeframe_for_indices_or_None}
STRATEGIES = {
    "trend_gap_fill":  {"label": "Trend-Filtered Gap Fill",       "ft_tf": "5m",  "idx_tf": "1d"},
    "monday_gap_fill": {"label": "Monday Gap Fill",                "ft_tf": "5m",  "idx_tf": "1d"},
    "quarterly_open":  {"label": "Quarterly Open Level",           "ft_tf": "1d",  "idx_tf": "1d"},
    "weekly_open":     {"label": "Weekly Open Level",              "ft_tf": "1h",  "idx_tf": "1d"},
    "turtle_soup":     {"label": "Turtle Soup Reversal",           "ft_tf": "1h",  "idx_tf": "1d"},
    "three_push_fade": {"label": "Three Push Fade",                "ft_tf": "1h",  "idx_tf": "1d"},
    "failed_breakdown":{"label": "Failed Breakdown Reversal",      "ft_tf": "1h",  "idx_tf": "1d"},
    "eom_rebalance":   {"label": "End-of-Month Rebalance",         "ft_tf": "1d",  "idx_tf": "1d"},
    "overnight_drift": {"label": "Overnight Positive Drift",       "ft_tf": "1d",  "idx_tf": "1d"},
    "kijun_bounce":    {"label": "Kijun-Sen Bounce",               "ft_tf": "1h",  "idx_tf": "1d"},
}

MIN_TRADES = 3  # below this = statistically invalid, report N/A

def grade(wr, pf):
    if wr is None or pf is None:
        return "—"
    if wr >= 70 and pf >= 2.0:  return "S"
    if wr >= 62 and pf >= 1.3:  return "A"
    if wr >= 55 and pf >= 1.1:  return "B"
    if wr >= 48 and pf >= 1.0:  return "C"
    return "D+"

def safe_run(name, symbol, start, end, tf):
    try:
        r = run_backtest(name, symbol, start, end, tf, starting_balance=100_000, qty=1)
        m = r["metrics"]
        t = m["total_trades"]
        if t < MIN_TRADES:
            return t, None, None
        return t, round(m["win_rate"], 1), round(m["profit_factor"], 2)
    except Exception:
        return 0, None, None

print("=" * 110)
print("ROUND 7 BACKTEST  —  10 new 70%+ WR candidates  —  6 pairs")
print("=" * 110)

rows = []
for sname, scfg in STRATEGIES.items():
    t0 = time.time()
    ft_tf  = scfg["ft_tf"]
    idx_tf = scfg["idx_tf"]

    ft_start  = START_5M if ft_tf == "5m" else (START_1H if ft_tf == "1h" else START_1D)
    idx_start = START_1D

    row = {"name": sname, "label": scfg["label"], "ft_tf": ft_tf, "idx_tf": idx_tf or "—"}
    total_trades = 0

    for sym, lbl in FUTURES:
        t, wr, pf = safe_run(sname, sym, ft_start, END, ft_tf)
        row[lbl] = (t, wr, pf)
        total_trades += t

    for sym, lbl in INDICES:
        if idx_tf is None:
            row[lbl] = (0, None, None)
        else:
            t, wr, pf = safe_run(sname, sym, idx_start, END, idx_tf)
            row[lbl] = (t, wr, pf)
            total_trades += t

    all_labels = ["MNQ", "MES", "MYM", "SPX", "NAS", "US30"]
    wrs  = [row[l][1] for l in all_labels if row[l][1] is not None]
    pfs  = [row[l][2] for l in all_labels if row[l][2] is not None]
    avg_wr = round(sum(wrs) / len(wrs), 1) if wrs else None
    avg_pf = round(sum(pfs) / len(pfs), 2) if pfs else None

    row["avg_wr"]      = avg_wr
    row["avg_pf"]      = avg_pf
    row["total_trades"] = total_trades
    row["grade"]       = grade(avg_wr, avg_pf)

    elapsed = time.time() - t0
    print(f"  [{sname:<18}]  avgWR={avg_wr}%  PF={avg_pf}  trades={total_trades}  grade={row['grade']}  [{elapsed:.1f}s]")
    rows.append(row)

rows.sort(key=lambda r: r["avg_wr"] or 0, reverse=True)

print()
print("=" * 120)
print(f"{'Strategy':<26} {'TF':>4} | {'MNQ':>8} | {'MES':>8} | {'MYM':>8} | {'SPX':>8} | {'NAS':>8} | {'US30':>8} | {'AVG WR':>7} | {'PF':>5} | GR")
print("-" * 120)

for r in rows:
    def fmt(lbl):
        t, wr, pf = r[lbl]
        if wr is None:
            return "   N/A"
        return f"{wr:.1f}%"
    aw = f"{r['avg_wr']:.1f}%" if r["avg_wr"] else "  N/A"
    ap = f"{r['avg_pf']:.2f}"  if r["avg_pf"] else "  N/A"
    print(f"  {r['label']:<24} {r['ft_tf']:>4} | {fmt('MNQ'):>8} | {fmt('MES'):>8} | {fmt('MYM'):>8} | {fmt('SPX'):>8} | {fmt('NAS'):>8} | {fmt('US30'):>8} | {aw:>7} | {ap:>5} | {r['grade']}")

print("=" * 120)
print()
print("GRADE KEY:  S = WR≥70% + PF≥2.0  |  A = WR≥62% + PF≥1.3  |  B = WR≥55% + PF≥1.1  |  C = WR≥48% + PF≥1.0")
print()

# Portfolio impact calculator
passing = [r for r in rows if r["avg_wr"] is not None and r["avg_wr"] >= 70]
existing_sum   = 17 * 62.3   # current 17 S+A+B strategies at avg 62.3%
existing_count = 17

if passing:
    new_sum   = sum(r["avg_wr"] for r in passing)
    new_count = len(passing)
    combined_wr = (existing_sum + new_sum) / (existing_count + new_count)
    print(f"STRATEGIES PASSING 70%+ WR THRESHOLD: {new_count}")
    for r in passing:
        print(f"  + {r['label']:<28}  WR={r['avg_wr']}%  PF={r['avg_pf']}  Grade={r['grade']}")
    print()
    print(f"PROJECTED COMBINED PORTFOLIO WR: {combined_wr:.1f}%")
    print(f"  (existing 17 strategies @ 62.3% avg  +  {new_count} new @ {sum(r['avg_wr'] for r in passing)/new_count:.1f}% avg)")
else:
    print("No strategies reached the 70%+ WR threshold on this run.")
    print("Best candidates to re-tune or test on alternate timeframes:")
    for r in sorted(rows, key=lambda x: x["avg_wr"] or 0, reverse=True)[:3]:
        print(f"  {r['label']}: {r['avg_wr']}% WR, PF {r['avg_pf']}")
