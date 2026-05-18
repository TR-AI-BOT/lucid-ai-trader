"""Test the 4 new high-precision strategies + compare fvg_strict vs fvg."""
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

def test(sid, tf, days):
    wrs, pfs, total = [], [], 0
    for sym, _ in ALL:
        try:
            r = run_backtest(sid, sym, start(days), END, tf, starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= 5:
                wrs.append(m["win_rate"]); pfs.append(m["profit_factor"])
                total += m["total_trades"]
        except: pass
    if not wrs: return None, None, 0
    return round(sum(wrs)/len(wrs),1), round(min(sum(pfs)/len(pfs),9.99),2), total

TESTS = [
    ("fvg",               "FVG (original)",            "1h",  700),
    ("fvg_strict",        "FVG Strict (EMA200+KZ)",    "1h",  700),
    ("fvg_strict",        "FVG Strict (EMA200+KZ)",    "30m",  59),
    ("fvg_strict",        "FVG Strict (EMA200+KZ)",    "15m",  58),
    ("silver_bullet_strict","ICT Silver Bullet Strict","5m",   58),
    ("silver_bullet_strict","ICT Silver Bullet Strict","15m",  58),
    ("silver_bullet_strict","ICT Silver Bullet Strict","30m",  59),
    ("ote_entry",         "ICT OTE Entry",              "1h",  700),
    ("ote_entry",         "ICT OTE Entry",              "30m",  59),
    ("ote_entry",         "ICT OTE Entry",              "15m",  58),
    ("two_leg_pullback",  "Two-Leg Pullback (Brooks)",  "1h",  700),
    ("two_leg_pullback",  "Two-Leg Pullback (Brooks)",  "30m",  59),
]

print()
print("="*75)
print("  NEW PRECISION STRATEGIES TEST")
print("="*75)
print("  {:<35} {:>4}  {:>7}  {:>6}  {:>7}  GR".format("Strategy","TF","WR","PF","Trades"))
print("-"*75)

best = {}
for sid, label, tf, days in TESTS:
    wr, pf, trades = test(sid, tf, days)
    key = sid
    if wr:
        g = grade(wr, pf)
        print("  {:<35} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}".format(label, tf, wr, pf, trades, g))
        if key not in best or (best[key][2] is None or wr > best[key][2]):
            best[key] = (label, tf, wr, pf, trades, g)
    else:
        print("  {:<35} {:>4}  N/A".format(label, tf))

print()
print("  BEST TF PER NEW STRATEGY:")
for sid, (label, tf, wr, pf, trades, g) in best.items():
    if wr: print("  [{}] {:<35} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}".format(g,label,tf,wr,pf,trades))
print()
