"""Round 3 — near-misses on alt TFs + untested 1d strategies."""
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

# Near-misses from round 2 — try different TFs
RETRIES = [
    ("bull_flag",      "Bull/Bear Flag",       "1h",  700),
    ("bull_flag",      "Bull/Bear Flag",       "30m",  59),
    ("bos",            "Break of Structure",    "1h",  700),
    ("bos",            "Break of Structure",    "30m",  59),
    ("scalp",          "Scalp",                "30m",  59),
    ("fvg",            "Fair Value Gap",        "1h",  700),
    ("holy_grail",     "Holy Grail Pullback",   "30m",  59),
    ("ema_pullback",   "EMA Trend Pullback",    "1h",  700),
    ("ema200_pullback","EMA 200 Pullback",      "1h",  700),
    ("prev_day_hl",    "Prev Day HL Break",     "30m",  59),
    ("prev_day_hl",    "Prev Day HL Break",     "1h",  700),
    ("pin_bar",        "Pin Bar Reversal",      "15m",  58),
    ("engulfing",      "Engulfing at POI",      "15m",  58),
    ("failed_breakout","Failed Breakout",       "1h",  700),
    ("failed_breakout","Failed Breakout",       "30m",  59),
    # 1d tests (daily is great for some strategies)
    ("mean_reversion", "Mean Reversion",        "1d",  700),
    ("bos",            "BOS",                   "1d",  700),
    ("pin_bar",        "Pin Bar",               "1d",  700),
    ("engulfing",      "Engulfing",             "1d",  700),
    ("bull_flag",      "Bull Flag",             "1d",  700),
]

print()
print("="*72)
print("  ROUND 3 — Near-miss alt TF retries")
print("="*72)
best = {}
for sid, label, tf, days in RETRIES:
    wr, pf, trades = test(sid, tf, days)
    key = (sid, tf)
    if wr is not None:
        g = grade(wr, pf)
        marker = " <-- QUALIFIES" if g in ("S","A","B") and trades >= 20 else ""
        print("  {:<28} {:>4}  WR={:5.1f}%  PF={:5.2f}  trades={:5d}  [{}]{}".format(
            label, tf, wr, pf, trades, g, marker))
        if g in ("S","A","B") and trades >= 20:
            best[sid] = (label, tf, wr, pf, trades, g)
    else:
        print("  {:<28} {:>4}  N/A".format(label, tf))

print()
if best:
    print("  NEW QUALIFIERS:")
    for sid, (label, tf, wr, pf, trades, g) in best.items():
        print("  [{}] {} on {} — WR={:.1f}%  PF={:.2f}  trades={}".format(g, label, tf, wr, pf, trades))
print()
