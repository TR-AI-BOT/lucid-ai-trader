"""Summary of the 6 active strategies in the Claude Trading Bot."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from backtesting.engine import run_backtest
from datetime import datetime, timedelta

TODAY = datetime.today()
END   = TODAY.strftime("%Y-%m-%d")

ACTIVE = [
    ("trend_gap_fill", "Trend Gap Fill",  "1h",  (TODAY - timedelta(days=700)).strftime("%Y-%m-%d")),
    ("ict_smc",        "ICT/SMC",         "30m", (TODAY - timedelta(days=59)).strftime("%Y-%m-%d")),
    ("orb",            "ORB Breakout",    "1h",  (TODAY - timedelta(days=700)).strftime("%Y-%m-%d")),
    ("mean_reversion", "Mean Reversion",  "1h",  (TODAY - timedelta(days=700)).strftime("%Y-%m-%d")),
    ("momentum",       "Momentum",        "30m", (TODAY - timedelta(days=59)).strftime("%Y-%m-%d")),
    ("trend_following","Trend Following", "30m", (TODAY - timedelta(days=59)).strftime("%Y-%m-%d")),
]

PAIRS = [("MNQ=F","MNQ"),("MES=F","MES"),("MYM=F","MYM"),("^GSPC","SPX"),("^NDX","NAS"),("^DJI","US30")]

def grade(wr, pf):
    if wr is None: return "-"
    if wr >= 70 and pf >= 1.2: return "S"
    if wr >= 62 and pf >= 1.3: return "A"
    if wr >= 55 and pf >= 1.1: return "B"
    if wr >= 50 and pf >= 1.0: return "C"
    if pf >= 1.0:              return "D"
    return "F"

print()
print("="*72)
print("  ACTIVE STRATEGIES - Claude Trading Bot (6 strategies)")
print("  Grade: S>=70%+1.2PF  A>=62%+1.3PF  B>=55%+1.1PF  C>=50%+1.0PF  D=profitable  F=losing")
print("="*72)
print("  {:<22} {:>4}  {:>7}  {:>6}  {:>7}  GR".format("Strategy","TF","WR","PF","Trades"))
print("-"*72)

all_wrs, all_pfs, all_trades = [], [], []

for strat_id, label, tf, start in ACTIVE:
    wrs, pfs, total = [], [], 0
    for sym, _ in PAIRS:
        try:
            r = run_backtest(strat_id, sym, start, END, tf, starting_balance=100_000, qty=1)
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
        print("  {:<22} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}".format(label, tf, wr, pf, total, g))
        all_wrs.append(wr); all_pfs.append(pf); all_trades.append(total)
    else:
        print("  {:<22} {:>4}  N/A".format(label, tf))

print("="*72)
if all_wrs:
    weighted_wr = round(sum(w*t for w,t in zip(all_wrs, all_trades)) / sum(all_trades), 1)
    simple_wr   = round(sum(all_wrs)/len(all_wrs), 1)
    avg_pf      = round(sum(all_pfs)/len(all_pfs), 2)
    total_t     = sum(all_trades)
    print("  {:<22} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}   {}".format(
        "COMBINED (weighted)", "", weighted_wr, avg_pf, total_t, grade(weighted_wr, avg_pf)))
    print("  {:<22} {:>4}  {:>6.1f}%".format("COMBINED (simple avg)", "", simple_wr))
print()
