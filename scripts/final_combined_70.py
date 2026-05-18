"""
Final optimized 24-entry roster — 20 unique strategies, target 70%+ combined WR.

Unique strategy list (20):
  S: TGF (1 strategy, 5 TFs: 5m/15m/30m/1h/4h), OGF-5m, ICT Silver Bullet
  A: ICT Order Block, BB Squeeze
  B: OGF-1h, OGF-15m, Monday GF-1h, Monday GF-15m, Smart Money,
     SuperTrend, Dual EMA Cross, ORB, Trend Following,
     Inside Bar-15m, Inside Bar-30m, FVG, Momentum, Donchian, Monthly Open
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")
def start(d): return (TODAY - timedelta(days=d)).strftime("%Y-%m-%d")

ROSTER = [
    # ── S class ──────────────────────────────────────────────────────────────
    ("Trend Gap Fill (5m)",         "trend_gap_fill",       "5m",   58),   # NEW — S class
    ("Trend Gap Fill (15m)",        "trend_gap_fill",       "15m",  58),
    ("Trend Gap Fill (30m)",        "trend_gap_fill",       "30m",  59),
    ("Trend Gap Fill (1h)",         "trend_gap_fill",       "1h",  700),
    ("Trend Gap Fill (4h)",         "trend_gap_fill",       "4h",  700),
    ("Opening Gap Fill (5m)",       "gap_fill",             "5m",   58),
    ("ICT Silver Bullet (30m)",     "silver_bullet_strict", "30m",  59),
    # ── A class ──────────────────────────────────────────────────────────────
    ("ICT Order Block (1h)",        "order_block",          "1h",  700),
    ("BB Squeeze (30m)",            "bb_squeeze",           "30m",  59),
    # ── B class ──────────────────────────────────────────────────────────────
    ("Opening Gap Fill (1h)",       "gap_fill",             "1h",  700),
    ("Opening Gap Fill (15m)",      "gap_fill",             "15m",  58),   # NEW #1
    ("Monday Gap Fill (1h)",        "monday_gap_fill",      "1h",  700),
    ("Monday Gap Fill (15m)",       "monday_gap_fill",      "15m",  58),   # NEW #2
    ("Smart Money (30m)",           "smc",                  "30m",  59),
    ("SuperTrend (30m)",            "supertrend",           "30m",  59),
    ("Dual EMA Cross (1h)",         "ema_cross",            "1h",  700),
    ("ORB Breakout (1h)",           "orb",                  "1h",  700),
    ("Trend Following (30m)",       "trend_follow",         "30m",  59),
    ("Inside Bar (15m)",            "inside_bar",           "15m",  58),
    ("Inside Bar (30m)",            "inside_bar",           "30m",  59),   # NEW #3
    ("FVG (30m)",                   "fvg",                  "30m",  59),
    ("Momentum (30m)",              "momentum",             "30m",  59),
    ("Donchian (30m)",              "donchian_break",       "30m",  59),
    ("Monthly Open (15m)",          "monthly_open",         "15m",  58),
]

FUTURES = [("MNQ=F","MNQ"),("MES=F","MES"),("MYM=F","MYM")]
INDICES = [("^GSPC","SPX"),("^NDX","NAS"),("^DJI","US30")]
ALL     = FUTURES + INDICES

def grade(wr, pf):
    if wr is None: return "-"
    if wr >= 70 and pf >= 1.2: return "S"
    if wr >= 62 and pf >= 1.3: return "A"
    if wr >= 55 and pf >= 1.1: return "B"
    if wr >= 50 and pf >= 1.0: return "C"
    if pf >= 1.0:              return "D"
    return "F"

print()
print("="*80)
print("  FINAL 23-ENTRY ROSTER — 20 Unique Strategies, Target 70%+ Combined WR")
print("="*80)
print("  {:<30} {:>4}  {:>7}  {:>6}  {:>7}  GR".format("Strategy","TF","WR","PF","Trades"))
print("-"*80)

total_wins, total_trades_all = 0, 0
all_wrs, all_pfs = [], []

for label, sid, tf, days in ROSTER:
    wrs, pfs, trades = [], [], 0
    for sym, _ in ALL:
        try:
            r = run_backtest(sid, sym, start(days), END, tf, starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= 5:
                wrs.append(m["win_rate"]); pfs.append(m["profit_factor"])
                trades += m["total_trades"]
        except: pass
    if wrs:
        wr = round(sum(wrs)/len(wrs), 1)
        pf = round(min(sum(pfs)/len(pfs), 9.99), 2)
        g  = grade(wr, pf)
        wins = round(trades * wr / 100)
        total_wins += wins; total_trades_all += trades
        all_wrs.append(wr); all_pfs.append(pf)
        print("  {:<30} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}".format(label, tf, wr, pf, trades, g))
    else:
        print("  {:<30} {:>4}  N/A".format(label, tf))

print("="*80)
if total_trades_all > 0:
    combined_wr = round(total_wins / total_trades_all * 100, 1)
    simple_avg  = round(sum(all_wrs) / len(all_wrs), 1)
    avg_pf      = round(sum(all_pfs) / len(all_pfs), 2)
    g           = grade(combined_wr, avg_pf)
    print()
    print("  COMBINED RESULTS ({} entries / 20 unique strategies, {:,} trades)".format(len(all_wrs), total_trades_all))
    print()
    print("  Weighted Win Rate :  {:.1f}%".format(combined_wr))
    print("  Simple Avg WR     :  {:.1f}%".format(simple_avg))
    print("  Avg Profit Factor :  {:.2f}".format(avg_pf))
    print("  Portfolio Grade   :  {}".format(g))
    print()
    if combined_wr >= 70:
        print("  TARGET ACHIEVED: {:.1f}% combined WR (20 unique strategies)".format(combined_wr))
    else:
        print("  Still {:.1f}% short of 70% target.".format(70 - combined_wr))
print()
