"""
scripts/run_final_master.py
============================
Final 20-strategy master list using verified BEST timeframes.
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
START_15M = (datetime.today() - timedelta(days=58)).strftime("%Y-%m-%d")
START_30M = (datetime.today() - timedelta(days=58)).strftime("%Y-%m-%d")

def safe_run(name, symbol, start, end, tf):
    try:
        r = run_backtest(name, symbol, start, end, tf, starting_balance=100_000, qty=1)
        m = r["metrics"]
        if m["total_trades"] < 3:
            return 0, None, None
        return m["total_trades"], round(m["win_rate"], 1), round(m["profit_factor"], 2)
    except Exception:
        return 0, None, None

def grade(wr, pf):
    if wr >= 62 and pf >= 1.3:   return "A"
    elif wr >= 55 and pf >= 1.1: return "B"
    elif wr >= 48 and pf >= 1.0: return "C"
    else:                        return "D"

def run_strat(sname, ft_tf, idx_tf, ft_start, idx_start=START_1D):
    results = {}
    for sym, lbl in FUTURES:
        results[lbl] = safe_run(sname, sym, ft_start, END, ft_tf)
    for sym, lbl in INDICES:
        if idx_tf is None:
            results[lbl] = (0, None, None)
        else:
            results[lbl] = safe_run(sname, sym, idx_start, END, idx_tf)
    wrs = [v[1] for v in results.values() if v[1] is not None]
    pfs = [v[2] for v in results.values() if v[2] is not None and v[0] >= 3]
    avg_wr = round(sum(wrs)/len(wrs), 1) if wrs else 0
    avg_pf = min(round(sum(pfs)/len(pfs), 2), 5.0) if pfs else 0
    return results, avg_wr, avg_pf, grade(avg_wr, avg_pf)

# (num, display_name, backtest_key, ft_tf, idx_tf, ft_start, idx_start, note)
MASTER = [
    ( 1, "Opening Range Breakout (ORB)", "orb",              "15m", "15m",  START_15M, START_15M, ""),
    ( 2, "Break & Retest",               "break_retest",     "1h",  "1d",   START_1H,  START_1D,  ""),
    ( 3, "Mean Reversion",               "mean_reversion",   "1h",  "1d",   START_1H,  START_1D,  ""),
    ( 4, "Fair Value Gap (FVG)",         "fvg",              "15m", "1h",   START_15M, START_1H,  ""),
    ( 5, "Inverse FVG (IFVG)",           "ifvg",             "1h",  "1h",   START_1H,  START_1H,  ""),
    ( 6, "Fibonacci Retracement",        "fibonacci",        "1h",  "1d",   START_1H,  START_1D,  ""),
    ( 7, "Fade (Counter-Trend)",         "fade",             "1h",  "1d",   START_1H,  START_1D,  ""),
    ( 8, "Asia Range Bull/Bear",         "asia_range",       "30m", None,   START_30M, None,      "live-only"),
    ( 9, "News Continuation",            "news_continuation","15m", None,   START_15M, None,      ""),
    (10, "Break of Structure (BOS)",     "bos",              "15m", "1h",   START_15M, START_1H,  ""),
    (11, "Smart Money Concept (SMC)",    "smc",              "1h",  "1h",   START_1H,  START_1H,  ""),
    (12, "Scalp (Momentum Burst)",       "scalp",            "1h",  None,   START_1H,  None,      ""),
    (13, "Trend Follow (EMA Stack)",     "trend_follow",     "1d",  "1d",   START_1D,  START_1D,  ""),
    (14, "ICT Order Block",              "order_block",      "15m", "1h",   START_15M, START_1H,  ""),
    (15, "Supply Zone (Short)",          "supply_demand",    "1d",  "1d",   START_1D,  START_1D,  ""),
    (16, "Demand Zone (Long)",           None,               "1d",  "1d",   START_1D,  START_1D,  "combined with #15"),
    (17, "Inside Bar Breakout",          "inside_bar",       "1d",  "1d",   START_1D,  START_1D,  ""),
    (18, "VWAP Std-Dev Bands",           "vwap_bands",       "1h",  None,   START_1H,  None,      ""),
    (19, "Dual EMA Cross (20/50)",       "ema_cross",        "1d",  "1d",   START_1D,  START_1D,  ""),
    (20, "BB Squeeze Breakout",          "bb_squeeze",       "1d",  "1d",   START_1D,  START_1D,  ""),
]

rows = []
print("Backtesting all 20 strategies on best timeframes ...\n")
for num, name, key, ft_tf, idx_tf, ft_start, idx_start, note in MASTER:
    if key is None or note == "combined with #15":
        rows.append({"num": num, "name": name, "tf": "1d", "combined": True,
                     "MNQ":(0,None,None),"MES":(0,None,None),"MYM":(0,None,None),
                     "SPX":(0,None,None),"NAS":(0,None,None),"US30":(0,None,None),
                     "avg_wr": 0, "avg_pf": 0, "grade": "—"})
        continue
    results, avg_wr, avg_pf, g = run_strat(key, ft_tf, idx_tf, ft_start,
                                            idx_start if idx_start else START_1D)
    tf_display = ft_tf if (idx_tf == ft_tf or idx_tf is None) else f"{ft_tf}/{idx_tf}"
    rows.append({"num": num, "name": name, "tf": tf_display,
                 "MNQ": results["MNQ"], "MES": results["MES"], "MYM": results["MYM"],
                 "SPX": results["SPX"], "NAS": results["NAS"], "US30": results["US30"],
                 "avg_wr": avg_wr, "avg_pf": avg_pf, "grade": g,
                 "note": note})
    print(f"  [{num:2}] {name:<32} WR={avg_wr:5.1f}%  PF={avg_pf:.2f}  Grade={g}")

def fmt(pair_data):
    t, wr, pf = pair_data
    if wr is None or t == 0: return "  N/A"
    return f" {wr:.0f}%"

print()
print("=" * 125)
print("  LUCID AI TRADER  —  COMPLETE STRATEGY MASTER LIST  (20 Strategies, Correct Timeframes)")
print("=" * 125)
print(f"  {'#':>2}  {'Strategy':<32} {'TF':>8} | {'MNQ':>6} | {'MES':>6} | {'MYM':>6} | {'SPX':>6} | {'NAS':>6} | {'US30':>6} | {'AVG WR':>7} | {'PF':>5} | GR")
print("-" * 125)

for row in rows:
    if row.get("combined"):
        print(f"  {row['num']:>2}  {row['name']:<32} {'1d':>8}   (see #15 — same backtest, long-side signals)")
        continue
    print(f"  {row['num']:>2}  {row['name']:<32} {row['tf']:>8} | {fmt(row['MNQ']):>6} | {fmt(row['MES']):>6} | {fmt(row['MYM']):>6} | {fmt(row['SPX']):>6} | {fmt(row['NAS']):>6} | {fmt(row['US30']):>6} | {row['avg_wr']:>6.1f}% | {row['avg_pf']:>5.2f} | {row['grade']}")

print("=" * 125)
print()
print("  GRADE: A = WR>=62%+PF>=1.3  B = WR>=55%+PF>=1.1  C = WR>=48%+PF>=1.0  D = below C (but may still be profitable via R:R)")
print()

grade_map = {"A":[], "B":[], "C":[], "D":[], "—":[]}
for row in rows:
    if not row.get("combined"):
        grade_map[row["grade"]].append(f"#{row['num']} {row['name']}")
for g in ["A","B","C","D"]:
    if grade_map[g]:
        print(f"  Grade {g}: {', '.join(grade_map[g])}")

profitable_d = [r for r in rows if r.get("grade") == "D" and r.get("avg_pf", 0) >= 1.0 and not r.get("combined")]
losing_d = [r for r in rows if r.get("grade") == "D" and 0 < r.get("avg_pf", 0) < 1.0 and not r.get("combined")]
print()
if profitable_d:
    prof_str = ", ".join(f"#{r['num']}" for r in profitable_d)
    print(f"  Grade D but PROFITABLE (PF>=1): {prof_str}")
if losing_d:
    lose_str = ", ".join(f"#{r['num']} {r['name']} PF={r['avg_pf']}" for r in losing_d)
    print(f"  Grade D and below PF 1.0: {lose_str}")
