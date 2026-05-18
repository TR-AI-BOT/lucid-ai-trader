"""
Round 2: Test all remaining untested strategies + retry near-misses on alt TFs.
Goal: find enough S/A/B class to fill Claude bot to 20.
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from backtesting.strategies import BACKTEST_STRATEGIES
from datetime import datetime, timedelta

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")

def start(days): return (TODAY - timedelta(days=days)).strftime("%Y-%m-%d")

# Known active in Claude bot (skip)
ALREADY_ACTIVE = {"trend_gap_fill", "ict_smc", "orb", "mean_reversion", "momentum", "trend_following"}
# Already confirmed S/A/B in round 1
ALREADY_FOUND  = {"gap_fill", "monday_gap_fill", "order_block", "smc"}

# All remaining — test each on 2 TFs, keep best
REMAINING = [sid for sid in BACKTEST_STRATEGIES if sid not in ALREADY_ACTIVE and sid not in ALREADY_FOUND]

TF_WINDOWS = {
    "1d":  700, "4h": 700, "1h": 700,
    "30m":  59, "15m": 58, "5m": 58, "1m": 7,
}
TEST_TFS = ["1h", "30m", "15m", "5m"]  # skip 1d/4h/1m for speed

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

def test_strat(sid, tf):
    wrs, pfs, total = [], [], 0
    days = TF_WINDOWS.get(tf, 59)
    for sym, _ in ALL:
        try:
            r = run_backtest(sid, sym, start(days), END, tf, starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= 5:
                wrs.append(m["win_rate"])
                pfs.append(m["profit_factor"])
                total += m["total_trades"]
        except:
            pass
    if not wrs:
        return None, None, 0
    wr = round(sum(wrs)/len(wrs), 1)
    pf = round(min(sum(pfs)/len(pfs), 9.99), 2)
    return wr, pf, total

best_results = {}
print()
print("="*80)
print("  ROUND 2 — Sweeping all remaining strategies")
print("="*80)

for sid in sorted(REMAINING):
    label = BACKTEST_STRATEGIES[sid].get("label", sid)
    best_wr, best_row = -1, None
    for tf in TEST_TFS:
        wr, pf, trades = test_strat(sid, tf)
        if wr is not None and wr > best_wr:
            best_wr = wr
            best_row = (wr, pf, trades, tf)
    if best_row:
        wr, pf, trades, tf = best_row
        g = grade(wr, pf)
        best_results[sid] = (label, tf, wr, pf, trades, g)
        marker = " <--" if g in ("S","A","B") else ""
        print("  {:<35} {:>4}  {:>6.1f}%  {:>6.2f}  {:>6} trades  [{}]{}".format(
            label, tf, wr, pf, trades, g, marker))
    else:
        print("  {:<35}  N/A".format(label))

# Summary
good = [(sid, *v) for sid, v in best_results.items() if v[5] in ("S","A","B")]
good.sort(key=lambda x: x[3], reverse=True)  # sort by WR

print()
print("="*80)
print("  NEW S/A/B STRATEGIES FOUND THIS ROUND")
print("="*80)
for sid, label, tf, wr, pf, trades, g in good:
    print("  [{}] {:<35} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}".format(
        g, label, tf, wr, pf, trades))
print()
print("  Found {} new qualifying strategies".format(len(good)))
print()
