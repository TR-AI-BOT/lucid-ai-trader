"""
Combined WR of all 20 Claude bot strategies.
Each tested on its best-performing timeframe.
Weighted average = total wins / total trades across all strategies.
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")
def start(d): return (TODAY - timedelta(days=d)).strftime("%Y-%m-%d")

# JS strategy -> (python_id, best_TF, days)
TWENTY = [
    ("Trend Gap Fill",       "trend_gap_fill",  "1h",  700),
    ("Opening Gap Fill",     "gap_fill",        "5m",   58),
    ("ICT/SMC (FVG)",        "fvg",             "1h",  700),
    ("ICT Order Block",      "order_block",     "30m",  59),
    ("BB Squeeze",           "bb_squeeze",      "30m",  59),
    ("Monday Gap Fill",      "monday_gap_fill", "1h",  700),
    ("Smart Money Concepts", "smc",             "30m",  59),
    ("SuperTrend",           "supertrend",      "30m",  59),
    ("Dual EMA Cross",       "ema_cross",       "1h",  700),
    ("ORB Breakout",         "orb",             "1h",  700),
    ("Prev Day H/L Break",   "pdh_pdl",         "1h",  700),
    ("Trend Following",      "trend_follow",    "30m",  59),
    ("Inside Bar Breakout",  "inside_bar",      "15m",  58),
    ("Fair Value Gap",       "fvg",             "30m",  59),   # different TF from ICT_SMC
    ("Momentum",             "momentum",        "30m",  59),
    ("Donchian Breakout",    "donchian_break",  "30m",  59),
    ("Mean Reversion",       "mean_reversion",  "1h",  700),
    ("Monthly Open",         "monthly_open",    "15m",  58),
    ("Break of Structure",   "bos",             "15m",  58),
    ("Scalp",                "scalp",           "1h",  700),
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
print("="*78)
print("  20-STRATEGY COMBINED BACKTEST — Claude Trading Bot")
print("="*78)
print("  {:<26} {:>4}  {:>7}  {:>6}  {:>7}  GR".format("Strategy","TF","WR","PF","Trades"))
print("-"*78)

total_wins   = 0
total_trades_all = 0
all_wrs = []
all_pfs = []

for label, sid, tf, days in TWENTY:
    wrs, pfs, trades = [], [], 0
    for sym, _ in ALL:
        try:
            r = run_backtest(sid, sym, start(days), END, tf, starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= 5:
                wrs.append(m["win_rate"])
                pfs.append(m["profit_factor"])
                trades += m["total_trades"]
        except: pass
    if wrs:
        wr = round(sum(wrs)/len(wrs), 1)
        pf = round(min(sum(pfs)/len(pfs), 9.99), 2)
        g  = grade(wr, pf)
        wins = round(trades * wr / 100)
        total_wins       += wins
        total_trades_all += trades
        all_wrs.append(wr)
        all_pfs.append(pf)
        print("  {:<26} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}".format(
            label, tf, wr, pf, trades, g))
    else:
        print("  {:<26} {:>4}  N/A".format(label, tf))

print("="*78)

if total_trades_all > 0:
    combined_wr  = round(total_wins / total_trades_all * 100, 1)
    simple_avg   = round(sum(all_wrs) / len(all_wrs), 1)
    avg_pf       = round(sum(all_pfs) / len(all_pfs), 2)
    combined_g   = grade(combined_wr, avg_pf)

    print()
    print("  COMBINED RESULTS ({} strategies, {:,} total trades)".format(
        len(all_wrs), total_trades_all))
    print()
    print("  Weighted Win Rate :  {:.1f}%  (total wins / total trades)".format(combined_wr))
    print("  Simple Avg WR     :  {:.1f}%  (avg across strategies)".format(simple_avg))
    print("  Avg Profit Factor :  {:.2f}".format(avg_pf))
    print("  Portfolio Grade   :  {}".format(combined_g))
    print()
    print("  Highest WR: {}".format(max(all_wrs)))
    print("  Lowest  WR: {}".format(min(all_wrs)))
    print("  WR Range  : {:.1f}%  spread".format(max(all_wrs) - min(all_wrs)))
print()
