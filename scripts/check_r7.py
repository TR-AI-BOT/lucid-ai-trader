from backtesting.engine import run_backtest
from datetime import datetime, timedelta
import sys
sys.path.insert(0, ".")

END      = datetime.today().strftime("%Y-%m-%d")
START_1D = "2019-01-01"
START_1H = (datetime.today() - timedelta(days=700)).strftime("%Y-%m-%d")

pairs_1d = [("MNQ=F","MNQ"), ("MES=F","MES"), ("MYM=F","MYM"),
            ("^GSPC","SPX"), ("^NDX","NAS"), ("^DJI","US30")]

pairs_1h = [("MNQ=F","MNQ"), ("MES=F","MES"), ("MYM=F","MYM")]

def run(name, sym, start, end, tf):
    try:
        r = run_backtest(name, sym, start, end, tf, starting_balance=100_000, qty=1)
        m = r["metrics"]
        t = m["total_trades"]
        return t, round(m["win_rate"],1), round(m["profit_factor"],2)
    except Exception as e:
        return 0, None, None

print("=== monday_gap_fill on 1D ===")
wrs = []
for sym, lbl in pairs_1d:
    t, wr, pf = run("monday_gap_fill", sym, START_1D, END, "1d")
    print(f"  {lbl}: trades={t}  WR={wr}%  PF={pf}")
    if wr: wrs.append(wr)
if wrs:
    print(f"  AVG WR: {sum(wrs)/len(wrs):.1f}%")

print()
print("=== trend_gap_fill on 1D ===")
wrs = []
for sym, lbl in pairs_1d:
    t, wr, pf = run("trend_gap_fill", sym, START_1D, END, "1d")
    print(f"  {lbl}: trades={t}  WR={wr}%  PF={pf}")
    if wr: wrs.append(wr)
if wrs:
    print(f"  AVG WR: {sum(wrs)/len(wrs):.1f}%")

print()
print("=== quarterly_open on 1H (futures) ===")
wrs = []
for sym, lbl in pairs_1h:
    t, wr, pf = run("quarterly_open", sym, START_1H, END, "1h")
    print(f"  {lbl}: trades={t}  WR={wr}%  PF={pf}")
    if wr: wrs.append(wr)
if wrs:
    print(f"  AVG WR: {sum(wrs)/len(wrs):.1f}%")
