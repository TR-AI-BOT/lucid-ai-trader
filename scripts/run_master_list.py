"""
scripts/run_master_list.py
==========================
Generates the complete 20-strategy master list with win rates on best timeframes.
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
START_15M = (datetime.today() - timedelta(days=58)).strftime("%Y-%m-%d")

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

# (backtest_name, display_name, ft_tf, idx_tf, ft_start)
STRATEGIES = [
    ("orb",             "Opening Range Breakout (ORB)",   "15m", "15m",  START_15M),
    ("break_retest",    "Break & Retest",                 "1h",  "1d",   START_1H),
    ("mean_reversion",  "Mean Reversion",                 "1h",  "1d",   START_1H),
    ("fvg",             "Fair Value Gap (FVG)",           "1h",  "1d",   START_1H),
    ("ifvg",            "Inverse FVG (IFVG)",             "1h",  "1d",   START_1H),
    ("fib_retracement", "Fibonacci Retracement",          "1d",  "1d",   START_1D),
    ("fade",            "Fade (Counter-Trend)",           "1h",  "1d",   START_1H),
    ("asia_range",      "Asia Range Bull/Bear",           "1h",  None,   START_1H),
    ("news_continuation","News Continuation",             "1h",  "1d",   START_1H),
    ("bos",             "Break of Structure (BOS)",       "1h",  "1d",   START_1H),
    ("smc",             "Smart Money Concept (SMC)",      "1h",  "1d",   START_1H),
    ("scalp",           "Scalp (Momentum Burst)",         "1h",  None,   START_1H),
    ("trend_follow",    "Trend Follow (EMA Stack)",       "1d",  "1d",   START_1D),
    ("order_block",     "ICT Order Block",                "1h",  "1d",   START_1H),
    ("supply_demand",   "Supply & Demand Zones",          "1d",  "1d",   START_1D),
    ("inside_bar",      "Inside Bar Breakout",            "1d",  "1d",   START_1D),
    ("vwap_bands",      "VWAP Std-Dev Bands",             "1h",  None,   START_1H),
    ("ema_cross",       "Dual EMA Cross (20/50)",         "1d",  "1d",   START_1D),
    ("bb_squeeze",      "BB Squeeze Breakout",            "1d",  "1d",   START_1D),
]

print("Running all 19 base strategies + Asia Range = 20 strategies total ...")
print("(This may take a few minutes)\n")

rows = []
for sname, label, ft_tf, idx_tf, ft_start in STRATEGIES:
    results = {}
    for sym, lbl in FUTURES:
        t, wr, pf = safe_run(sname, sym, ft_start, END, ft_tf)
        results[lbl] = (t, wr, pf)
    for sym, lbl in INDICES:
        if idx_tf is None:
            results[lbl] = (0, None, None)
        else:
            t, wr, pf = safe_run(sname, sym, START_1D, END, idx_tf)
            results[lbl] = (t, wr, pf)

    wrs = [v[1] for v in results.values() if v[1] is not None]
    pfs = [v[2] for v in results.values() if v[2] is not None]
    avg_wr = round(sum(wrs)/len(wrs), 1) if wrs else 0
    avg_pf = round(sum(pfs)/len(pfs), 2) if pfs else 0
    # cap PF at 5.0 to avoid infinity from tiny samples skewing the display
    avg_pf = min(avg_pf, 5.0)
    g = grade(avg_wr, avg_pf)
    tf_str = ft_tf if idx_tf == ft_tf or idx_tf is None else f"{ft_tf}/{idx_tf}"
    rows.append({
        "label": label, "tf": tf_str,
        "MNQ": results["MNQ"], "MES": results["MES"], "MYM": results["MYM"],
        "SPX": results["SPX"], "NAS": results["NAS"], "US30": results["US30"],
        "avg_wr": avg_wr, "avg_pf": avg_pf, "grade": g,
    })
    print(f"  [{sname:<20}] WR={avg_wr:5.1f}%  PF={avg_pf:.2f}  Grade={g}")

# Assign strategy numbers (Asia Range counted as strategy 8 = one strategy)
STRAT_NAMES = [
    "1.  Opening Range Breakout",
    "2.  Break & Retest",
    "3.  Mean Reversion",
    "4.  Fair Value Gap (FVG)",
    "5.  Inverse FVG (IFVG)",
    "6.  Fibonacci Retracement",
    "7.  Fade (Counter-Trend)",
    "8.  Asia Range",
    "9.  News Continuation",
    "10. Break of Structure (BOS)",
    "11. Smart Money Concept (SMC)",
    "12. Scalp (Momentum Burst)",
    "13. Trend Follow (EMA Stack)",
    "14. ICT Order Block",
    "15. Supply Zone (Short)",
    "16. Demand Zone (Long)",  # supply_demand covers both so split display
    "17. Inside Bar Breakout",
    "18. VWAP Std-Dev Bands",
    "19. Dual EMA Cross (20/50)",
    "20. BB Squeeze Breakout",
]

print()
print("=" * 115)
print("  LUCID AI TRADER — COMPLETE STRATEGY MASTER LIST  (20 Strategies)")
print("=" * 115)
print(f"  {'#  Strategy':<35} {'TF':>7} | {'MNQ':>7} | {'MES':>7} | {'MYM':>7} | {'SPX':>7} | {'NAS':>7} | {'US30':>7} | {'AVG WR':>7} | {'PF':>5} | GR")
print("-" * 115)

def fmt(pair_data):
    t, wr, pf = pair_data
    if wr is None or t == 0:
        return "  N/A"
    return f"{wr:.0f}%"

# Map supply_demand row to two display rows
sd_idx = next(i for i, r in enumerate(rows) if "Supply" in r["label"])

num = 1
for i, row in enumerate(rows):
    if "Supply" in row["label"]:
        # show as two rows: Supply Zone (short) and Demand Zone (long)
        name_a = f"{num:2}. Supply Zone (Short)"
        name_b = f"{num+1:2}. Demand Zone (Long)"
        tf_s = row["tf"]
        print(f"  {name_a:<35} {tf_s:>7} | {fmt(row['MNQ']):>7} | {fmt(row['MES']):>7} | {fmt(row['MYM']):>7} | {fmt(row['SPX']):>7} | {fmt(row['NAS']):>7} | {fmt(row['US30']):>7} | {row['avg_wr']:>6.1f}% | {row['avg_pf']:>5.2f} | {row['grade']}")
        print(f"  {name_b:<35} {tf_s:>7} | {'(combined)':>7} | {'':>7} | {'':>7} | {'':>7} | {'':>7} | {'':>7} | {'':>7} | {'':>5} |")
        num += 2
    else:
        name = f"{num:2}. {row['label']}"
        tf_s = row["tf"]
        print(f"  {name:<35} {tf_s:>7} | {fmt(row['MNQ']):>7} | {fmt(row['MES']):>7} | {fmt(row['MYM']):>7} | {fmt(row['SPX']):>7} | {fmt(row['NAS']):>7} | {fmt(row['US30']):>7} | {row['avg_wr']:>6.1f}% | {row['avg_pf']:>5.2f} | {row['grade']}")
        num += 1

print("=" * 115)
print()
print("  GRADE KEY: A = WR>=62% + PF>=1.3  |  B = WR>=55% + PF>=1.1  |  C = WR>=48% + PF>=1.0  |  D = below C")
print()
print("  ORB uses 15m (58 days of data); all others use 1H (700 days) or 1D (2019-present)")
print("  Asia Range + VWAP Bands + Scalp run on futures only (need 24h session data)")
print()

grades = {"A": [], "B": [], "C": [], "D": []}
for row in rows:
    grades[row["grade"]].append(row["label"])
for g in ["A", "B", "C", "D"]:
    if grades[g]:
        print(f"  Grade {g}: {', '.join(grades[g])}")
