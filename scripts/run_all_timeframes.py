"""
scripts/run_all_timeframes.py
==============================
Backtest EVERY registered strategy on EVERY timeframe:
  1d · 4h · 1h · 30m · 15m · 5m · 1m

Data windows (yfinance limits):
  1m  = last 7 days    (futures only)
  5m  = last 58 days
  15m = last 58 days
  30m = last 59 days
  1h  = last 700 days
  4h  = last 700 days  (resampled from 1h)
  1d  = 2019-01-01

Pairs: MNQ / MES / MYM / SPX / NAS / US30
Output: master ranked table + per-TF top-5
"""
from __future__ import annotations
import sys, time, warnings
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

from backtesting.engine import run_backtest
from backtesting.strategies import BACKTEST_STRATEGIES

TODAY  = datetime.today()
END    = TODAY.strftime("%Y-%m-%d")
START  = {
    "1m":  (TODAY - timedelta(days=7)).strftime("%Y-%m-%d"),
    "5m":  (TODAY - timedelta(days=58)).strftime("%Y-%m-%d"),
    "15m": (TODAY - timedelta(days=58)).strftime("%Y-%m-%d"),
    "30m": (TODAY - timedelta(days=59)).strftime("%Y-%m-%d"),
    "1h":  (TODAY - timedelta(days=700)).strftime("%Y-%m-%d"),
    "4h":  (TODAY - timedelta(days=700)).strftime("%Y-%m-%d"),
    "1d":  "2019-01-01",
}
TIMEFRAMES = ["1d", "4h", "1h", "30m", "15m", "5m", "1m"]

FUTURES   = [("MNQ=F", "MNQ"), ("MES=F", "MES"), ("MYM=F", "MYM")]
INDICES   = [("^GSPC", "SPX"), ("^NDX",  "NAS"), ("^DJI",  "US30")]
MIN_TRADES = 5

def grade(wr, pf):
    if wr is None or pf is None: return "-"
    if wr >= 70 and pf >= 1.2:  return "S"
    if wr >= 62 and pf >= 1.3:  return "A"
    if wr >= 55 and pf >= 1.1:  return "B"
    if wr >= 48 and pf >= 1.0:  return "C"
    if pf >= 1.0:               return "D"
    return "F"

def safe_run(strat, sym, start, tf):
    try:
        r = run_backtest(strat, sym, start, END, tf, starting_balance=100_000, qty=1)
        m = r["metrics"]
        if m["total_trades"] < MIN_TRADES:
            return None
        return (m["total_trades"], round(m["win_rate"], 1), round(m["profit_factor"], 2))
    except Exception:
        return None

def run_on_tf(strat, tf):
    pairs = FUTURES if tf == "1m" else FUTURES + INDICES
    wrs, pfs, trades = [], [], 0
    for sym, _ in pairs:
        res = safe_run(strat, sym, START[tf], tf)
        if res:
            trades += res[0]
            wrs.append(res[1])
            pfs.append(res[2])
    if not wrs:
        return None, None, 0
    wr = round(sum(wrs) / len(wrs), 1)
    pf = round(min(sum(pfs) / len(pfs), 9.99), 2)
    return wr, pf, trades

# ── Run everything ─────────────────────────────────────────────────────────────

all_strats = sorted(BACKTEST_STRATEGIES.keys())
n = len(all_strats)
results: dict[str, dict] = {}

print()
print("=" * 115)
print(f"  FULL BACKTEST: {n} strategies x {len(TIMEFRAMES)} timeframes x 6 pairs")
print("=" * 115)

for si, strat in enumerate(all_strats, 1):
    label = BACKTEST_STRATEGIES[strat].get("label", strat)
    print(f"\n[{si:02d}/{n}] {label}")
    results[strat] = {}
    for tf in TIMEFRAMES:
        t0 = time.time()
        wr, pf, trades = run_on_tf(strat, tf)
        elapsed = time.time() - t0
        gr = grade(wr, pf)
        if wr is not None:
            print(f"        {tf:>4}  WR={wr:5.1f}%  PF={pf:5.2f}  trades={trades:5d}  [{gr}]  ({elapsed:.1f}s)")
        else:
            print(f"        {tf:>4}  N/A  ({elapsed:.1f}s)")
        results[strat][tf] = (wr, pf, trades) if wr is not None else None

# ── Master summary ranked by best WR ──────────────────────────────────────────

print()
print("=" * 115)
print("  MASTER RESULTS — Best timeframe per strategy, ranked by WR")
print("  Grade: S=WR>=70%+PF>=1.2  A=WR>=62%+PF>=1.3  B=WR>=55%+PF>=1.1  C=WR>=48%+PF>=1.0  D=PF>=1.0  F=losing")
print("=" * 115)
print(f"  {'Strategy':<28} {'Best TF':>7}  {'WR':>7}  {'PF':>6}  {'Trades':>7}  GR")
print("-" * 115)

summary = []
for strat in all_strats:
    label = BACKTEST_STRATEGIES[strat].get("label", strat)
    best_wr, best_data = -1, None
    for tf in TIMEFRAMES:
        r = results[strat][tf]
        if r and r[0] is not None and r[0] > best_wr:
            best_wr = r[0]
            best_data = (tf, r[0], r[1], r[2])
    if best_data:
        summary.append((label, *best_data, grade(best_data[1], best_data[2])))

summary.sort(key=lambda x: x[2], reverse=True)

for label, tf, wr, pf, trades, gr in summary:
    print(f"  {label:<28} {tf:>7}  {wr:>6.1f}%  {pf:>6.2f}  {trades:>7}   {gr}")

print("=" * 115)

# ── Per-TF top 5 ──────────────────────────────────────────────────────────────
print()
print("  TOP 5 PER TIMEFRAME")
print("=" * 115)
for tf in TIMEFRAMES:
    tf_rows = []
    for strat in all_strats:
        r = results[strat][tf]
        if r:
            label = BACKTEST_STRATEGIES[strat].get("label", strat)
            tf_rows.append((label, r[0], r[1], r[2], grade(r[0], r[1])))
    tf_rows.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  [{tf}]")
    for label, wr, pf, trades, gr in tf_rows[:5]:
        print(f"    {label:<28}  WR={wr:5.1f}%  PF={pf:5.2f}  trades={trades:5d}  [{gr}]")

print()
print("  NOTE: 1m = 7 days only. 5m/15m/30m = ~58 days. 4h resampled from 1h.")
print()
