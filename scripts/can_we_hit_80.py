"""
Feasibility study: can we reach 80% combined WR?

Approach 1: Prune — keep only entries above WR threshold
Approach 2: Test TGF on additional TFs (5m, 2h) — the highest-WR strategy
Approach 3: Find any strategy with 80%+ WR and enough volume
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

# ── APPROACH 1: Math — what does pruning achieve? ──────────────────────────
print()
print("="*70)
print("  APPROACH 1: MATHEMATICAL PRUNING ANALYSIS")
print("="*70)

# Current roster data (from last run)
FULL_ROSTER = [
    ("Trend Gap Fill (1h)",       75.9, 2507),
    ("Trend Gap Fill (4h)",       77.7,  815),
    ("Trend Gap Fill (30m)",      79.3,  425),
    ("Trend Gap Fill (15m)",      76.5,  958),
    ("Opening Gap Fill (5m)",     73.0,  174),
    ("ICT Silver Bullet (30m)",   70.5,   90),
    ("ICT Order Block (1h)",      62.4,  288),
    ("BB Squeeze (30m)",          63.1,   43),
    ("Opening Gap Fill (1h)",     69.0, 2704),
    ("Opening Gap Fill (15m)",    78.0,  201),
    ("Monday Gap Fill (1h)",      66.3,  676),
    ("Monday Gap Fill (15m)",     73.4,   62),
    ("Smart Money (30m)",         61.7,   78),
    ("SuperTrend (30m)",          60.6,   97),
    ("Dual EMA Cross (1h)",       58.9,  213),
    ("ORB Breakout (1h)",         59.4,  284),
    ("Trend Following (30m)",     57.6,  176),
    ("Inside Bar (15m)",          58.1,  205),
    ("Inside Bar (30m)",          57.6,  112),
    ("FVG (30m)",                 57.9,  122),
    ("Momentum (30m)",            56.1,  131),
    ("Donchian (30m)",            55.6,   69),
    ("Monthly Open (15m)",        55.1,   56),
]

for threshold in [55, 60, 65, 70, 75]:
    kept  = [(n, w, t) for n, w, t in FULL_ROSTER if w >= threshold]
    wins  = sum(round(t * w / 100) for _, w, t in kept)
    total = sum(t for _, _, t in kept)
    cwr   = round(wins / total * 100, 1) if total else 0
    print("  Keep WR >= {:2d}%:  {:2d} entries, {:,} trades  ->  {:.1f}% WR".format(
        threshold, len(kept), total, cwr))

# ── APPROACH 2: Test TGF on more TFs + best gap variants ──────────────────
print()
print("="*70)
print("  APPROACH 2: HIGH-WR CANDIDATES (TGF extra TFs + gap variants)")
print("="*70)
print("  {:<30} {:>4}  {:>7}  {:>6}  {:>7}  GR".format("Strategy","TF","WR","PF","Trades"))
print("-"*70)

CANDIDATES = [
    ("trend_gap_fill",  "TGF",        "5m",  58),
    ("trend_gap_fill",  "TGF",        "2h",  700),
    ("gap_fill",        "OGF",        "30m",  59),
    ("monday_gap_fill", "Monday GF",  "4h",  700),
    ("silver_bullet_strict","ICT SB", "15m",  58),
    ("order_block",     "Order Block","15m",  58),
    ("order_block",     "Order Block","30m",  59),
    ("bb_squeeze",      "BB Squeeze", "15m",  58),
    ("gap_fill",        "OGF",        "4h",  700),
]

highs = []
for sid, label, tf, days in CANDIDATES:
    wr, pf, trades = test(sid, tf, days)
    if wr:
        g = grade(wr, pf)
        flag = " ***" if wr >= 70 and pf >= 1.0 and trades >= 20 else ""
        print("  {:<30} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}{}".format(
            label, tf, wr, pf, trades, g, flag))
        if wr >= 70 and pf >= 1.0 and trades >= 20:
            highs.append((label, sid, tf, wr, pf, trades))
    else:
        print("  {:<30} {:>4}  N/A".format(label, tf))

# ── APPROACH 3: Simulated 80% roster ──────────────────────────────────────
print()
print("="*70)
print("  APPROACH 3: PROJECTED WR IF WE REPLACE ALL <70% ENTRIES")
print("             with the new high-WR entries found above")
print("="*70)

# Start from S-class only (pruned at 70%)
base = [(n, w, t) for n, w, t in FULL_ROSTER if w >= 70.0]
base_wins  = sum(round(t * w / 100) for _, w, t in base)
base_total = sum(t for _, _, t in base)
base_wr    = round(base_wins / base_total * 100, 1)
print("  S-class baseline (WR >= 70%): {:,} trades -> {:.1f}% WR".format(base_total, base_wr))

# Add new high-WR entries
for label, sid, tf, wr, pf, trades in highs:
    new_wins  = round(trades * wr / 100)
    new_total = base_total + trades
    new_wr    = round((base_wins + new_wins) / new_total * 100, 1)
    print("  + {:} {:}: {:,} trades @ {:.1f}% -> portfolio {:.1f}%".format(
        label, tf, trades, wr, new_wr))

print()
print("  NOTE: To move from 70.8% -> 80% with current 10,486 trades,")
print("  you'd need ~9,600 new trades at 90%+ WR, OR keep only")
print("  high-WR entries and find strategies that hit 80%+ individually.")
print()
