"""Test ORB Breakout & Retest on 1h, 15m, and 5m."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")

START = {
    "1h":  (TODAY - timedelta(days=700)).strftime("%Y-%m-%d"),
    "15m": (TODAY - timedelta(days=58)).strftime("%Y-%m-%d"),
    "5m":  (TODAY - timedelta(days=58)).strftime("%Y-%m-%d"),
}

FUTURES = [("MNQ=F","MNQ"),("MES=F","MES"),("MYM=F","MYM")]
INDICES = [("^GSPC","SPX"),("^NDX","NAS"),("^DJI","US30")]

def grade(wr, pf):
    if wr is None: return "-"
    if wr >= 70 and pf >= 1.2: return "S"
    if wr >= 62 and pf >= 1.3: return "A"
    if wr >= 55 and pf >= 1.1: return "B"
    if wr >= 48 and pf >= 1.0: return "C"
    if pf >= 1.0:              return "D"
    return "F"

print("\nORB Breakout & Retest — 1h / 15m / 5m\n" + "="*70)
for tf in ["1h", "15m", "5m"]:
    wrs, pfs = [], []
    print(f"\n  [{tf}]")
    pairs = FUTURES + INDICES
    for sym, lbl in pairs:
        try:
            r = run_backtest("orb_retest", sym, START[tf], END, tf, starting_balance=100_000, qty=1)
            m = r["metrics"]
            if m["total_trades"] >= 5:
                wr = round(m["win_rate"], 1)
                pf = round(m["profit_factor"], 2)
                wrs.append(wr); pfs.append(pf)
                print(f"    {lbl}: WR={wr}%  PF={pf}  trades={m['total_trades']}")
            else:
                print(f"    {lbl}: N/A (only {m['total_trades']} trades)")
        except Exception as e:
            print(f"    {lbl}: error — {e}")
    if wrs:
        avg_wr = round(sum(wrs)/len(wrs), 1)
        avg_pf = round(sum(pfs)/len(pfs), 2)
        g = grade(avg_wr, avg_pf)
        print(f"\n  AVG: WR={avg_wr}%  PF={avg_pf}  Grade={g}")
    else:
        print("  AVG: no qualifying results")
print()
