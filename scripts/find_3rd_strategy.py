"""Find a profitable 3rd new strategy that doesn't drag combined WR below 70.7%."""
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
            r = run_backtest(sid, sym, start(days), END, tf,
                             starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= 5:
                wrs.append(m["win_rate"]); pfs.append(m["profit_factor"])
                total += m["total_trades"]
        except: pass
    if not wrs: return None, None, 0
    return round(sum(wrs)/len(wrs),1), round(min(sum(pfs)/len(pfs),9.99),2), total

# Strategies not yet in the active roster, testing best TFs
CANDIDATES = [
    ("holy_grail",      "Holy Grail (20EMA pullback)",  "1h",  700),
    ("holy_grail",      "Holy Grail (20EMA pullback)",  "30m",  59),
    ("ema200_pullback", "EMA200 Pullback",               "1h",  700),
    ("ema200_pullback", "EMA200 Pullback",               "30m",  59),
    ("opening_drive",   "Opening Drive",                 "1h",  700),
    ("opening_drive",   "Opening Drive",                 "15m",  58),
    ("bull_flag",       "Bull Flag Pattern",             "1h",  700),
    ("bull_flag",       "Bull Flag Pattern",             "30m",  59),
    ("nwog_reaction",   "NWOG Reaction",                 "1h",  700),
    ("nwog_reaction",   "NWOG Reaction",                 "30m",  59),
    ("vwap",            "VWAP Mean Reversion",           "30m",  59),
    ("weekly_open",     "Weekly Open S/R",               "1h",  700),
    ("weekly_open",     "Weekly Open S/R",               "30m",  59),
    ("inside_bar",      "Inside Bar (30m)",              "30m",  59),
    ("keltner_squeeze", "Keltner Squeeze",               "30m",  59),
    ("williams_r_trend","Williams %R Trend",             "1h",  700),
    ("failed_breakout", "Failed Breakout",               "1h",  700),
    ("failed_breakout", "Failed Breakout",               "30m",  59),
    ("three_bar_play",  "Three Bar Play",                "1h",  700),
    ("engulfing",       "Engulfing at POI",              "1h",  700),
]

# Known 22-entry stats WITHOUT 3rd strategy (approximate)
BASE_TRADES = 10374
BASE_WINS   = round(BASE_TRADES * 0.709)  # ~70.9% WR without NWOG

print()
print("="*80)
print("  FINDING 3rd NEW STRATEGY — must be profitable (PF >= 1.0) AND not drag WR below 70.7%")
print("="*80)
print("  {:<30} {:>4}  {:>7}  {:>6}  {:>7}  {:>8}  GR".format(
      "Strategy","TF","WR","PF","Trades","PortWR"))
print("-"*80)

qualifiers = []
for sid, label, tf, days in CANDIDATES:
    wr, pf, trades = test(sid, tf, days)
    if wr:
        g = grade(wr, pf)
        # Projected portfolio WR if we add this strategy
        new_wins   = round(trades * wr / 100)
        port_wr    = round((BASE_WINS + new_wins) / (BASE_TRADES + trades) * 100, 1)
        profitable = pf >= 1.0
        keeps_wr   = port_wr >= 70.7
        flag = ""
        if profitable and keeps_wr and trades >= 20:
            flag = " *** QUALIFIES"
            qualifiers.append((label, sid, tf, wr, pf, trades, g, port_wr))
        elif not profitable:
            flag = " (losing)"
        elif not keeps_wr:
            flag = " (drags WR)"
        print("  {:<30} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}  {:>7.1f}%   {}{}".format(
            label, tf, wr, pf, trades, port_wr, g, flag))
    else:
        print("  {:<30} {:>4}  N/A".format(label, tf))

qualifiers.sort(key=lambda x: x[3], reverse=True)
print()
print("="*80)
print("  TOP QUALIFIERS (ranked by WR):")
for label, sid, tf, wr, pf, trades, g, port_wr in qualifiers:
    print("  [{}] {:<30} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}  PortWR={:.1f}%".format(
        g, label, tf, wr, pf, trades, port_wr))
print()
