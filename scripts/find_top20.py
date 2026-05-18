"""
Find best 14 candidates to bring Claude bot to 20 strategies.
Tests ~25 book-aligned strategies across their best TF, ranks by WR.
"""
import sys, warnings, time
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")

def start(days): return (TODAY - timedelta(days=days)).strftime("%Y-%m-%d")

# Candidates from the books — (strategy_id, label, best_TF, days_of_data)
# Derived from: Al Brooks, ICT/SMC books, Aziz, Miner, Hougaard, Gujral, Livermore
CANDIDATES = [
    # From ICT / SMC books
    ("order_block",       "ICT Order Block",          "30m",  59),
    ("turtle_soup",       "Liquidity Sweep Reversal",  "15m",  58),
    ("silver_bullet",     "ICT Silver Bullet",         "5m",   58),
    ("amd",               "AMD / Power of 3",          "1h",  700),
    ("smc",               "Smart Money Concepts",      "30m",  59),
    # From Al Brooks
    ("failed_breakout",   "Failed Breakout",           "15m",  58),
    ("three_push_fade",   "Three Push Fade (Wedge)",   "1h",  700),
    ("pin_bar",           "Pin Bar Reversal",          "1h",  700),
    ("engulfing",         "Engulfing at POI",          "30m",  59),
    # From Andrew Aziz
    ("gap_go",            "Gap & Go",                  "5m",   58),
    ("bull_flag",         "Bull/Bear Flag",            "15m",  58),
    ("opening_drive",     "Opening Drive",             "5m",   58),
    # From Robert Miner / high-probability
    ("rsi_div",           "RSI Divergence",            "1h",  700),
    ("macd_div",          "MACD Divergence",           "1h",  700),
    ("keltner_squeeze",   "Keltner+BB Squeeze",        "30m",  59),
    # From Livermore / Wyckoff / classic
    ("livermore_pivot",   "Livermore Pivotal Point",   "1d",  700),
    ("wyckoff",           "Wyckoff Spring/Upthrust",   "1h",  700),
    ("pdh_pdl",           "PDH/PDL Rejection",         "15m",  58),
    # From Hougaard / vol-based
    ("vol_climax",        "Volume Climax Reversal",    "5m",   58),
    ("rule_80_20",        "80-20 Reversal",            "15m",  58),
    # From Gujral / gap trading
    ("gap_fill",          "Opening Gap Fill",          "5m",   58),
    ("monday_gap_fill",   "Monday Gap Fill",           "1h",  700),
    # Others tested in full run
    ("inside_bar",        "Inside Bar Breakout",       "1h",  700),
    ("holy_grail",        "Holy Grail Pullback",       "1h",  700),
    ("ema200_pullback",   "EMA 200 Pullback",          "1h",  700),
]

FUTURES = [("MNQ=F","MNQ"),("MES=F","MES"),("MYM=F","MYM")]
INDICES = [("^GSPC","SPX"),("^NDX","NAS"),("^DJI","US30")]
ALL     = FUTURES + INDICES

def grade(wr, pf):
    if wr is None or pf is None: return "-"
    if wr >= 70 and pf >= 1.2: return "S"
    if wr >= 62 and pf >= 1.3: return "A"
    if wr >= 55 and pf >= 1.1: return "B"
    if wr >= 50 and pf >= 1.0: return "C"
    if pf >= 1.0:              return "D"
    return "F"

print()
print("="*80)
print("  BOOK-ALIGNED STRATEGY CANDIDATES — Finding top 14 for Claude bot")
print("="*80)
print("  {:<30} {:>4}  {:>7}  {:>6}  {:>7}  GR".format("Strategy","TF","WR","PF","Trades"))
print("-"*80)

results = []
for sid, label, tf, days in CANDIDATES:
    wrs, pfs, total = [], [], 0
    pairs = FUTURES if tf == "1m" else ALL
    for sym, _ in pairs:
        try:
            r = run_backtest(sid, sym, start(days), END, tf, starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= 5:
                wrs.append(m["win_rate"])
                pfs.append(m["profit_factor"])
                total += m["total_trades"]
        except:
            pass
    if wrs:
        wr = round(sum(wrs)/len(wrs), 1)
        pf = round(min(sum(pfs)/len(pfs), 9.99), 2)
        g  = grade(wr, pf)
        results.append((label, sid, tf, wr, pf, total, g))
        print("  {:<30} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}".format(label, tf, wr, pf, total, g))
    else:
        results.append((label, sid, tf, None, None, 0, "-"))
        print("  {:<30} {:>4}  N/A".format(label, tf))

# Rank by WR, filter S/A/B
ranked = [r for r in results if r[3] is not None]
ranked.sort(key=lambda x: x[3], reverse=True)
good   = [r for r in ranked if r[6] in ("S","A","B")]

print()
print("="*80)
print("  TOP S/A/B CLASS — Ready for Claude bot")
print("="*80)
for label, sid, tf, wr, pf, trades, g in good[:14]:
    print("  [{g}] {:<30} {tf:>4}  WR={wr:.1f}%  PF={pf:.2f}".format(
        label, g=g, tf=tf, wr=wr, pf=pf))

print()
print("  {} qualifying strategies found (need 14)".format(len(good)))
print()
