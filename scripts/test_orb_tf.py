"""Quick test of ORB Breakout on 15m and 5m."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta

END      = datetime.today().strftime("%Y-%m-%d")
START_58 = (datetime.today() - timedelta(days=58)).strftime("%Y-%m-%d")

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

print("\nORB Breakout — 15m and 5m test\n" + "="*70)
for tf in ["15m", "5m"]:
    wrs, pfs = [], []
    print(f"\n  [{tf}]")
    for sym, lbl in FUTURES + INDICES:
        try:
            r = run_backtest("orb", sym, START_58, END, tf, starting_balance=100_000, qty=1)
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
        print(f"\n  AVG: WR={avg_wr}%  PF={avg_pf}  Grade={grade(avg_wr, avg_pf)}")
print()
