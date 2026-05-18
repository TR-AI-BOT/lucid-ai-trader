"""Test gap fill variants on multiple TFs + trend_gap_fill on shorter TFs."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")
def start(d): return (TODAY - timedelta(days=d)).strftime("%Y-%m-%d")

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

def test(sid, tf, days, min_trades=5):
    wrs, pfs, total = [], [], 0
    for sym, _ in ALL:
        try:
            r = run_backtest(sid, sym, start(days), END, tf, starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= min_trades:
                wrs.append(m["win_rate"]); pfs.append(m["profit_factor"])
                total += m["total_trades"]
        except: pass
    if not wrs: return None, None, 0
    return round(sum(wrs)/len(wrs),1), round(min(sum(pfs)/len(pfs),9.99),2), total

TESTS = [
    ("trend_gap_fill", "Trend Gap Fill",       "30m",  59),
    ("trend_gap_fill", "Trend Gap Fill",       "15m",  58),
    ("trend_gap_fill", "Trend Gap Fill",       "4h",  700),
    ("gap_fill",       "Opening Gap Fill",     "15m",  58),
    ("gap_fill",       "Opening Gap Fill",     "1h",  700),
    ("gap_fill",       "Opening Gap Fill",     "30m",  59),
    ("monday_gap_fill","Monday Gap Fill",      "30m",  59),
    ("monday_gap_fill","Monday Gap Fill",      "15m",  58),
    ("silver_bullet_strict","ICT SB Strict",   "30m",  59),
    ("silver_bullet_strict","ICT SB Strict",   "1h",  700),
    ("fvg",            "FVG",                  "5m",   58),
    ("fvg",            "FVG",                  "15m",  58),
    ("smc",            "SMC",                  "1h",  700),
    ("smc",            "SMC",                  "15m",  58),
    ("order_block",    "Order Block",           "1h",  700),
    ("order_block",    "Order Block",           "15m",  58),
    ("bb_squeeze",     "BB Squeeze",            "1h",  700),
    ("bb_squeeze",     "BB Squeeze",            "15m",  58),
]

print()
print("="*72)
print("  GAP FILL VARIANTS + STRATEGY TF SWEEP")
print("="*72)
print("  {:<28} {:>4}  {:>7}  {:>6}  {:>7}  GR".format("Strategy","TF","WR","PF","Trades"))
print("-"*72)

for sid, label, tf, days in TESTS:
    wr, pf, trades = test(sid, tf, days)
    if wr:
        g = grade(wr, pf)
        flag = " ***" if g in ("S","A") and trades >= 30 else ""
        print("  {:<28} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}{}".format(label, tf, wr, pf, trades, g, flag))
    else:
        print("  {:<28} {:>4}  N/A".format(label, tf))
print()
