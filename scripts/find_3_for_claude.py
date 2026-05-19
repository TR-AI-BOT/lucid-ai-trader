"""Find 3 strategies to add to Claude bot: must keep combined WR >= 72.1%."""
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

CANDIDATES = [
    # Wyckoff concepts (from books)
    ("wyckoff",        "Wyckoff Spring",      "1h",  700),
    ("wyckoff",        "Wyckoff Spring",      "30m",  59),
    # ICT/SMC concepts
    ("turtle_soup",    "Turtle Soup Reversal","1h",  700),
    ("turtle_soup",    "Turtle Soup Reversal","30m",  59),
    # Brooks price action
    ("three_push_fade","Three Push Fade",     "1h",  700),
    ("three_push_fade","Three Push Fade",     "30m",  59),
    ("failed_breakdown","Failed Breakdown",   "1h",  700),
    ("failed_breakdown","Failed Breakdown",   "30m",  59),
    # Miner / rule-based
    ("rule_80_20",     "Rule of 80/20",       "1h",  700),
    ("rule_80_20",     "Rule of 80/20",       "4h",  700),
    # Kijun bounce (Japanese method)
    ("kijun_bounce",   "Kijun Bounce",        "1h",  700),
    ("kijun_bounce",   "Kijun Bounce",        "4h",  700),
    # Other untested
    ("overnight_drift","Overnight Drift",     "1h",  700),
    ("eom_rebalance",  "EOM Rebalance",       "1d",  700),
    ("livermore_pivot","Livermore Pivot",     "1h",  700),
    ("livermore_pivot","Livermore Pivot",     "4h",  700),
    ("vol_climax",     "Volume Climax",       "1h",  700),
    ("vol_climax",     "Volume Climax",       "30m",  59),
    ("three_bar_play", "Three Bar Play",      "30m",  59),
    ("rsi_div",        "RSI Divergence",      "1h",  700),
    ("macd_div",       "MACD Divergence",     "1h",  700),
    ("pin_bar",        "Pin Bar Reversal",    "1h",  700),
    ("pin_bar",        "Pin Bar Reversal",    "30m",  59),
    ("engulfing",      "Engulfing at POI",    "30m",  59),
]

print()
print("="*78)
print("  FINDING 3 MORE FOR CLAUDE BOT — must keep combined WR >= 72.1%")
print("="*78)
print("  {:<28} {:>4}  {:>7}  {:>6}  {:>7}  {:>8}  GR".format(
      "Strategy","TF","WR","PF","Trades","PortWR"))
print("-"*78)

qualifies = []
for sid, label, tf, days in CANDIDATES:
    wr, pf, trades = test(sid, tf, days)
    if wr:
        g = grade(wr, pf)
        new_wins = round(trades * wr / 100)
        port_wr  = round((BASE_WINS + new_wins) / (BASE_TRADES + trades) * 100, 1)
        ok = pf >= 1.0 and port_wr >= 72.1 and trades >= 15
        flag = " *** QUALIFIES" if ok else (" (drags WR)" if port_wr < 72.1 else " (losing)" if pf < 1.0 else "")
        print("  {:<28} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}  {:>7.1f}%   {}{}".format(
              label, tf, wr, pf, trades, port_wr, g, flag))
        if ok:
            qualifies.append((label, sid, tf, wr, pf, trades, g, port_wr))
    else:
        print("  {:<28} {:>4}  N/A".format(label, tf))

qualifies.sort(key=lambda x: x[3], reverse=True)
print()
print("="*78)
print("  TOP QUALIFIERS (ranked by WR):")
for label, sid, tf, wr, pf, trades, g, port_wr in qualifies:
    print("  [{}] {:<28} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}  PortWR={:.1f}%".format(
          g, label, tf, wr, pf, trades, port_wr))
if not qualifies:
    print("  None qualify yet.")
print()
