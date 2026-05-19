"""
Round 2: target strategies that individually hit >= 72.1% WR.
Only those can be added without pulling combined below 72.1%.
"""
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

BASE_TRADES = 13919
BASE_WINS   = round(BASE_TRADES * 0.721)

# Only strategies we haven't added yet that might hit 72%+ WR
CANDIDATES = [
    # Gap fill family -- only ones above 72% WR are safe
    ("gap_fill",       "OGF (30m)",            "30m",  59),
    ("gap_fill",       "OGF (4h)",             "4h",  700),
    ("trend_gap_fill", "TGF (5m) — already in roster, confirm", "5m", 58),
    # Silver Bullet on new TFs
    ("silver_bullet_strict","ICT SB (15m)",    "15m",  58),
    ("silver_bullet_strict","ICT SB (1h)",     "1h",  700),
    # Order Block on new TFs
    ("order_block",    "Order Block (30m)",    "30m",  59),
    ("order_block",    "Order Block (15m)",    "15m",  58),
    # BB Squeeze on new TFs
    ("bb_squeeze",     "BB Squeeze (1h)",      "1h",  700),
    ("bb_squeeze",     "BB Squeeze (15m)",     "15m",  58),
    # Monday GF on 4h
    ("monday_gap_fill","Monday GF (4h)",       "4h",  700),
    # SMC on 1h
    ("smc",            "Smart Money (1h)",     "1h",  700),
    # Supertrend on 1h
    ("supertrend",     "SuperTrend (1h)",      "1h",  700),
]

print()
print("="*78)
print("  ROUND 2 — Strategies that individually hit >= 72.1% WR")
print("  (mathematical requirement to not drag combined below 72.1%)")
print("="*78)
print("  {:<35} {:>4}  {:>7}  {:>6}  {:>7}  {:>8}  GR".format(
      "Strategy","TF","WR","PF","Trades","PortWR"))
print("-"*78)

qualifies = []
for sid, label, tf, days in CANDIDATES:
    wr, pf, trades = test(sid, tf, days)
    if wr:
        g = grade(wr, pf)
        new_wins = round(trades * wr / 100)
        port_wr  = round((BASE_WINS + new_wins) / (BASE_TRADES + trades) * 100, 1)
        ok = wr >= 72.1 and pf >= 1.0 and trades >= 10
        flag = " *** QUALIFIES" if ok else ""
        print("  {:<35} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}  {:>7.1f}%   {}{}".format(
              label, tf, wr, pf, trades, port_wr, g, flag))
        if ok:
            qualifies.append((label, sid, tf, wr, pf, trades, g, port_wr))
    else:
        print("  {:<35} {:>4}  N/A".format(label, tf))

qualifies.sort(key=lambda x: x[3], reverse=True)
print()
print("="*78)
print("  QUALIFIERS (WR >= 72.1%, profitable, sufficient trades):")
for label, sid, tf, wr, pf, trades, g, port_wr in qualifies:
    print("  [{}] {:<35} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}  PortWR={:.1f}%".format(
          g, label, tf, wr, pf, trades, port_wr))
if not qualifies:
    print("  None with WR >= 72.1%. Best alternatives shown above.")
print()
