"""Quick backtest of harmonic patterns to see if any qualify for Claude bot."""
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
            if m["total_trades"] >= 3:
                wrs.append(m["win_rate"]); pfs.append(m["profit_factor"])
                total += m["total_trades"]
        except: pass
    if not wrs: return None, None, 0
    return round(sum(wrs)/len(wrs),1), round(min(sum(pfs)/len(pfs),9.99),2), total

TESTS = [
    ("abcd",      "ABCD Pattern",     "1h",  700),
    ("abcd",      "ABCD Pattern",     "4h",  700),
    ("gartley",   "Gartley",          "1h",  700),
    ("gartley",   "Gartley",          "4h",  700),
    ("bat",       "Bat Pattern",      "1h",  700),
    ("bat",       "Bat Pattern",      "4h",  700),
    ("butterfly", "Butterfly",        "1h",  700),
    ("butterfly", "Butterfly",        "4h",  700),
    ("crab",      "Crab Pattern",     "1h",  700),
    ("crab",      "Crab Pattern",     "4h",  700),
]

# Current JS bot baseline: 13,919 trades at 72.1% WR
BASE_TRADES = 13919
BASE_WINS   = round(BASE_TRADES * 0.721)

print()
print("="*75)
print("  HARMONIC PATTERNS — backtest to verify quality for Claude bot")
print("="*75)
print("  {:<22} {:>4}  {:>7}  {:>6}  {:>7}  {:>8}  GR".format(
      "Strategy","TF","WR","PF","Trades","PortWR"))
print("-"*75)

qualifies = []
for sid, label, tf, days in TESTS:
    wr, pf, trades = test(sid, tf, days)
    if wr:
        g = grade(wr, pf)
        new_wins = round(trades * wr / 100)
        port_wr  = round((BASE_WINS + new_wins) / (BASE_TRADES + trades) * 100, 1)
        ok = pf >= 1.0 and port_wr >= 72.1 and trades >= 10
        flag = " OK" if ok else ""
        print("  {:<22} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}  {:>7.1f}%   {}{}".format(
              label, tf, wr, pf, trades, port_wr, g, flag))
        if ok:
            qualifies.append((label, sid, tf, wr, pf, trades, g, port_wr))
    else:
        print("  {:<22} {:>4}  N/A".format(label, tf))

print()
print("  Qualifiers (profitable + keeps PortWR >= 72.1%):")
for item in qualifies:
    label, sid, tf, wr, pf, trades, g, port_wr = item
    print("  [{}] {:<22} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}  PortWR={:.1f}%".format(
          g, label, tf, wr, pf, trades, port_wr))
if not qualifies:
    print("  None qualify. Need alternative strategies.")
print()
