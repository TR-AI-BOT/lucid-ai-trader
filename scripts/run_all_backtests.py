# -*- coding: utf-8 -*-
"""
scripts/run_all_backtests.py
============================
Runs every registered backtest strategy on the SIX exact trading pairs the user
trades on TradingView, at each strategy's research-optimal timeframe:

  MNQ1!  -> MNQ=F   Micro Nasdaq 100 Futures   (1H, 24h market)
  MES1!  -> MES=F   Micro S&P 500 Futures      (1H, 24h market)
  MYM1!  -> MYM=F   Micro Dow Jones Futures    (1H, 24h market)
  SPX    -> ^GSPC   S&P 500 Index              (1D only, no volume)
  NAS100 -> ^NDX    Nasdaq 100 Index           (1D only, no volume)
  US30   -> ^DJI    Dow Jones Industrial Avg   (1D only, no volume)

Futures trade ~24h so AMD / Asia Range strategies have session data on the 1H
feed. Index tickers carry no volume from yfinance so volume is forced to a
neutral 1.0-ratio (filled with a synthetic constant) before strategies run.

1H strategies : orb, vwap, fvg, ifvg, sweep_reversal, break_retest, bos, smc,
                amd, asia_range, news_continuation, scalp
1D strategies : mean_reversion, fibonacci, fade, range_bound, gap_go,
                momentum, breakout, trend_follow, reversal

Intraday-only strategies (orb, vwap, amd, asia_range) run on the futures 1H
feed only -> index columns show N/A.
1D strategies run on all 6 (futures 1D resample + index 1D).

Dates:
  1D : 2019-01-01 -> today
  1H : last 700 days (yfinance ~730-day intraday limit)

Usage:
    cd C:\\Users\\soule\\OneDrive\\Desktop\\lucid-ai-trader
    python scripts/run_all_backtests.py
"""
from __future__ import annotations

import os
import sys
import time
import traceback
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

from backtesting.data_fetcher import fetch_ohlcv
from backtesting.engine import _simulate, _metrics
from backtesting.strategies import BACKTEST_STRATEGIES

# --- Configuration ----------------------------------------------------------

# label -> (yf ticker, kind)  kind in {"fut", "idx"}
SYMBOLS = {
    "MNQ":  ("MNQ=F", "fut"),
    "MES":  ("MES=F", "fut"),
    "MYM":  ("MYM=F", "fut"),
    "SPX":  ("^GSPC", "idx"),
    "NAS":  ("^NDX",  "idx"),
    "US30": ("^DJI",  "idx"),
}
SYM_ORDER = ["MNQ", "MES", "MYM", "SPX", "NAS", "US30"]

DAILY_START = "2019-01-01"

_today = datetime.now()
DAILY_END   = _today.strftime("%Y-%m-%d")
INTRA_END   = _today.strftime("%Y-%m-%d")
INTRA_START = (_today - timedelta(days=700)).strftime("%Y-%m-%d")
# 30m feed: yfinance caps 30m history at ~60 days. Used for session
# strategies (amd, asia_range, orb, vwap) which need >=6-8 bars inside the
# 4-hour Asia window -- impossible at 1H resolution (max 4 bars/4h).
M30_START = (_today - timedelta(days=59)).strftime("%Y-%m-%d")

STARTING_BALANCE = 100_000.0
QTY = 1

# Only the 6 NEW research-backed strategies are run by this script.
NEW_STRATEGIES = [
    "order_block", "silver_bullet", "supply_demand",
    "inside_bar", "vwap_bands", "wyckoff",
]

# order_block -> 1H futures / 1D indices ; silver_bullet & vwap_bands -> 1H
# (intraday) ; supply_demand, inside_bar, wyckoff -> 1D all.
ONE_HOUR = {"order_block", "silver_bullet", "vwap_bands"}
ONE_DAY = {"supply_demand", "inside_bar", "wyckoff"}

# Strategies that need true intraday structure.
# These only run on the futures 1H feed; index columns -> N/A.
INTRADAY_ONLY = {"silver_bullet", "vwap_bands"}


def tf_for(name: str) -> str:
    return "1H" if name in ONE_HOUR else "1D"


def _neutralize_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Index tickers have no volume from yfinance. Replace with a flat
    synthetic series so any volume-ratio check resolves to ~1.0 (neutral)."""
    if df is None or df.empty:
        return df
    out = df.copy()
    out["volume"] = 1_000_000.0
    return out


# --- Download all data ------------------------------------------------------

def download_all() -> dict:
    print("=" * 100)
    print("Downloading market data: MNQ/MES/MYM (1H+1D futures) + SPX/NAS/US30 (1D indices)...")
    print("=" * 100)
    data: dict = {}
    for label in SYM_ORDER:
        ticker, kind = SYMBOLS[label]
        data[label] = {"kind": kind, "1H": pd.DataFrame(),
                        "30M": pd.DataFrame(), "1D": pd.DataFrame()}

        # Daily for everyone
        try:
            d = fetch_ohlcv(ticker, DAILY_START, DAILY_END, "1d")
            if kind == "idx":
                d = _neutralize_volume(d)
            data[label]["1D"] = d
            print(f"  {label:<4} ({ticker:<6}) 1D : {len(d):>6} bars  ({DAILY_START} -> {DAILY_END})")
        except Exception as e:
            print(f"  {label:<4} ({ticker:<6}) 1D : FAILED ({e})")

        # Hourly only for futures (indices have no reliable intraday on yfinance)
        if kind == "fut":
            try:
                h = fetch_ohlcv(ticker, INTRA_START, INTRA_END, "1h")
                data[label]["1H"] = h
                print(f"  {label:<4} ({ticker:<6}) 1H : {len(h):>6} bars  ({INTRA_START} -> {INTRA_END})")
            except Exception as e:
                print(f"  {label:<4} ({ticker:<6}) 1H : FAILED ({e})")
            try:
                m = fetch_ohlcv(ticker, M30_START, INTRA_END, "30m")
                data[label]["30M"] = m
                print(f"  {label:<4} ({ticker:<6}) 30M: {len(m):>6} bars  ({M30_START} -> {INTRA_END})")
            except Exception as e:
                print(f"  {label:<4} ({ticker:<6}) 30M: FAILED ({e})")
        else:
            print(f"  {label:<4} ({ticker:<6}) 1H : N/A (index, daily only)")
    print()
    return data


# --- Run one strategy on one symbol ----------------------------------------

def run_one(name, df) -> dict:
    if df is None or df.empty:
        return {"trades": None, "wr": None, "pf": None, "pnl": None}
    fn = BACKTEST_STRATEGIES[name]["fn"]
    signals = fn(df)
    sim = _simulate(df, signals, STARTING_BALANCE, QTY)
    m = _metrics(sim["trades"], STARTING_BALANCE, sim["final_balance"])
    return {
        "trades": m["total_trades"],
        "wr":     m["win_rate"],
        "pf":     m["profit_factor"],
        "pnl":    m["total_pnl"],
    }


def data_for(label, tf, name, data) -> pd.DataFrame:
    """Pick the right frame for a (symbol, strategy)."""
    kind = data[label]["kind"]

    if name in INTRADAY_ONLY:
        # futures only; use 30M feed so the 1-hour ICT windows contain
        # enough bars for a 3-bar FVG (1H tops out at 1 bar/window).
        if kind != "fut":
            return pd.DataFrame()
        m = data[label]["30M"]
        return m if (m is not None and not m.empty) else data[label]["1H"]

    if tf == "1H":
        # 1H strategy: futures use the 1H feed; indices fall back to 1D
        if kind == "fut":
            return data[label]["1H"]
        return data[label]["1D"]

    # 1D strategy: everyone uses daily
    return data[label]["1D"]


def grade(avg_wr, pf):
    if avg_wr is None or pf is None:
        return "D"
    if avg_wr >= 62 and pf >= 1.3:
        return "A"
    if avg_wr >= 55 and pf >= 1.1:
        return "B"
    if avg_wr >= 48 and pf >= 1.0:
        return "C"
    return "D"


# --- Main -------------------------------------------------------------------

def main():
    t0 = time.time()
    data = download_all()
    names = [s for s in NEW_STRATEGIES if s in BACKTEST_STRATEGIES]

    print("=" * 100)
    print(f"Running {len(names)} NEW strategies x 6 symbols at optimal timeframes...")
    print(f"  -> {', '.join(names)}")
    print("=" * 100)

    rows = []
    for idx, name in enumerate(names, 1):
        tf = tf_for(name)
        print(f"  [{idx:02d}/{len(names)}] {name:<18} {tf}", end=" ... ", flush=True)
        per = {}
        try:
            for label in SYM_ORDER:
                df = data_for(label, tf, name, data)
                per[label] = run_one(name, df)
            wrs = [per[s]["wr"] for s in SYM_ORDER if per[s]["trades"]]
            pfs = [per[s]["pf"] for s in SYM_ORDER
                   if per[s]["trades"] and per[s]["pf"] not in (None, 999.0)]
            avg_wr = round(sum(wrs) / len(wrs), 1) if wrs else None
            avg_pf = round(sum(pfs) / len(pfs), 2) if pfs else (
                999.0 if any(per[s]["trades"] for s in SYM_ORDER) else None)
            g = grade(avg_wr, avg_pf if avg_pf and avg_pf != 999.0 else (
                1.3 if avg_pf == 999.0 else 0))
            rows.append({"name": name, "tf": tf, "per": per,
                         "avg_wr": avg_wr, "avg_pf": avg_pf, "grade": g,
                         "err": None})
            tt = sum((per[s]["trades"] or 0) for s in SYM_ORDER)
            print(f"trades={tt:<5} avgWR={avg_wr if avg_wr is not None else 'N/A'} "
                  f"PF={avg_pf} grade={g}")
        except Exception as e:
            traceback.print_exc()
            rows.append({"name": name, "tf": tf, "per": {}, "avg_wr": None,
                         "avg_pf": None, "grade": "-", "err": str(e)[:60]})
            print(f"ERROR: {e}")

    # sort by avg WR desc (None last)
    rows.sort(key=lambda r: (r["avg_wr"] is not None, r["avg_wr"] or -1), reverse=True)

    def cell_w(p):
        if p is None or p["trades"] is None or p["trades"] == 0:
            return "N/A"
        return f"{p['wr']:.1f}"

    print()
    W = 110
    print("=" * W)
    print("BACKTEST RESULTS  -  6 TradingView pairs  -  optimal timeframes  -  sorted by Avg Win Rate")
    print("=" * W)
    hdr = (f"{'STRATEGY':<18}{'TF':<5}| "
           f"{'MNQ WR%':>8} | {'MES WR%':>8} | {'MYM WR%':>8} | "
           f"{'SPX WR%':>8} | {'NAS WR%':>8} | {'US30 WR%':>9} | "
           f"{'AVG WR':>7} | {'PF':>6} | GRADE")
    print(hdr)
    print("=" * W)

    for r in rows:
        if r["err"]:
            print(f"{r['name']:<18}{r['tf']:<5}|  ERROR: {r['err']}")
            continue
        p = r["per"]
        awr = f"{r['avg_wr']:.1f}" if r["avg_wr"] is not None else "N/A"
        if r["avg_pf"] in (None,):
            pf = "N/A"
        elif r["avg_pf"] == 999.0:
            pf = "inf"
        else:
            pf = f"{r['avg_pf']:.2f}"
        print(f"{r['name']:<18}{r['tf']:<5}| "
              f"{cell_w(p.get('MNQ')):>8} | {cell_w(p.get('MES')):>8} | "
              f"{cell_w(p.get('MYM')):>8} | {cell_w(p.get('SPX')):>8} | "
              f"{cell_w(p.get('NAS')):>8} | {cell_w(p.get('US30')):>9} | "
              f"{awr:>7} | {pf:>6} | {r['grade']}")

    print("=" * W)
    print()
    print("SUMMARY")
    print("-" * 60)
    valid = [r for r in rows if r["avg_wr"] is not None]
    by_grade = {}
    for r in rows:
        by_grade.setdefault(r["grade"], []).append(r["name"])
    for g in ["A", "B", "C", "D", "-"]:
        if g in by_grade:
            print(f"  Grade {g}: {len(by_grade[g]):>2}  -> {', '.join(by_grade[g])}")
    if valid:
        avg = sum(r["avg_wr"] for r in valid) / len(valid)
        best = max(valid, key=lambda x: x["avg_wr"])
        print(f"\n  Strategies producing trades : {len(valid)}/{len(rows)}")
        print(f"  Mean avg win rate           : {avg:.1f}%")
        print(f"  Top strategy                : {best['name']} @ {best['avg_wr']:.1f}% (grade {best['grade']})")
    else:
        print("  No strategy produced trades.")

    print(f"\nTotal runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
