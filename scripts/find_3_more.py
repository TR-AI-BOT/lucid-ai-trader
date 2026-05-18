"""
Find 3 more unique strategies at 70%+ WR to complete the 20.
Tests: gap fill on more TFs, silver bullet variations, new implementations.
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
            r = run_backtest(sid, sym, start(days), END, tf,
                             starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= 5:
                wrs.append(m["win_rate"]); pfs.append(m["profit_factor"])
                total += m["total_trades"]
        except: pass
    if not wrs: return None, None, 0
    return round(sum(wrs)/len(wrs),1), round(min(sum(pfs)/len(pfs),9.99),2), total

# Already in roster (to skip duplicates):
SKIP = {
    ("trend_gap_fill","1h"), ("trend_gap_fill","4h"),
    ("trend_gap_fill","30m"),("trend_gap_fill","15m"),
    ("gap_fill","5m"),       ("gap_fill","1h"),
    ("monday_gap_fill","1h"),("silver_bullet_strict","30m"),
    ("order_block","1h"),    ("bb_squeeze","30m"),
    ("smc","30m"),           ("supertrend","30m"),
    ("ema_cross","1h"),      ("orb","1h"),
    ("trend_follow","30m"),  ("inside_bar","15m"),
    ("fvg","30m"),           ("momentum","30m"),
    ("donchian_break","30m"),("monthly_open","15m"),
}

CANDIDATES = [
    # Gap fill family — different TFs not yet used
    ("gap_fill",             "Opening Gap Fill",       "4h",  700),
    ("gap_fill",             "Opening Gap Fill",       "15m",  58),
    ("monday_gap_fill",      "Monday Gap Fill",        "15m",  58),
    ("monday_gap_fill",      "Monday Gap Fill",        "30m",  59),
    # Silver Bullet at 1h
    ("silver_bullet_strict", "ICT Silver Bullet",      "1h",  700),
    # OTE and new strategies we built
    ("ote_entry",            "ICT OTE Entry",          "1h",  700),
    ("two_leg_pullback",     "Two-Leg Pullback",       "1h",  700),
    # Other untested TFs for good strategies
    ("order_block",          "ICT Order Block",        "30m",  59),
    ("smc",                  "Smart Money",            "1h",  700),
    ("smc",                  "Smart Money",            "15m",  58),
    ("inside_bar",           "Inside Bar",             "1h",  700),
    ("inside_bar",           "Inside Bar",             "30m",  59),
    ("orb",                  "ORB Breakout",           "30m",  59),
    ("orb",                  "ORB Breakout",           "15m",  58),
    ("supertrend",           "SuperTrend",             "1h",  700),
    ("ema_cross",            "Dual EMA Cross",         "30m",  59),
    ("bb_squeeze",           "BB Squeeze",             "1h",  700),
    # Strategies not yet tried at any TF
    ("opening_drive",        "Opening Drive",          "1h",  700),
    ("opening_drive",        "Opening Drive",          "15m",  58),
    ("fvg",                  "FVG",                    "1h",  700),
    ("engulfing",            "Engulfing at POI",       "1h",  700),
    ("pin_bar",              "Pin Bar Reversal",       "30m",  59),
    ("wyckoff",              "Wyckoff Spring",         "30m",  59),
    ("pdh_pdl",              "Prev Day HL",            "30m",  59),
]

print()
print("="*72)
print("  SEARCHING FOR 3 MORE STRATEGIES (target: WR >= 70%)")
print("="*72)
print("  {:<30} {:>4}  {:>7}  {:>6}  {:>7}  GR".format("Strategy","TF","WR","PF","Trades"))
print("-"*72)

qualifiers = []
for sid, label, tf, days in CANDIDATES:
    if (sid, tf) in SKIP:
        continue
    wr, pf, trades = test(sid, tf, days)
    if wr:
        g = grade(wr, pf)
        flag = " *** QUALIFIES" if g in ("S","A","B") and trades >= 20 else ""
        print("  {:<30} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}{}".format(
            label, tf, wr, pf, trades, g, flag))
        if g in ("S","A","B") and trades >= 20:
            qualifiers.append((label, sid, tf, wr, pf, trades, g))
    else:
        print("  {:<30} {:>4}  N/A".format(label, tf))

qualifiers.sort(key=lambda x: x[3], reverse=True)
print()
print("="*72)
print("  NEW QUALIFIERS (ranked by WR):")
for label, sid, tf, wr, pf, trades, g in qualifiers:
    print("  [{}] {:<30} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}".format(
        g, label, tf, wr, pf, trades))
print()
