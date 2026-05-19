"""
FINAL DEEP SEARCH — all untested Lucid strategies.
Target: individual WR >= 72.1% to not drag combined below 72.1%.
BASE: 13,919 trades, 72.1% WR (10,034 wins).
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
            if m["total_trades"] >= 3:
                wrs.append(m["win_rate"]); pfs.append(m["profit_factor"])
                total += m["total_trades"]
        except: pass
    if not wrs: return None, None, 0
    return round(sum(wrs)/len(wrs),1), round(min(sum(pfs)/len(pfs),9.99),2), total

BASE_TRADES = 13919
BASE_WINS   = round(BASE_TRADES * 0.721)

# ALL untested strategies from Lucid's registry
CANDIDATES = [
    # ICT precision concepts — highest WR potential
    ("ote_entry",       "ICT OTE Entry (5m)",       "5m",   58),
    ("ote_entry",       "ICT OTE Entry (15m)",       "15m",  58),
    ("ote_entry",       "ICT OTE Entry (30m)",       "30m",  59),
    ("ote_entry",       "ICT OTE Entry (1h)",        "1h",  700),
    ("fvg_strict",      "FVG Strict (5m)",           "5m",   58),
    ("fvg_strict",      "FVG Strict (15m)",          "15m",  58),
    ("fvg_strict",      "FVG Strict (30m)",          "30m",  59),
    ("ifvg",            "Inverse FVG (5m)",          "5m",   58),
    ("ifvg",            "Inverse FVG (15m)",         "15m",  58),
    ("ifvg",            "Inverse FVG (30m)",         "30m",  59),
    ("ifvg",            "Inverse FVG (1h)",          "1h",  700),
    # VWAP strategies
    ("vwap",            "VWAP Bounce (5m)",          "5m",   58),
    ("vwap",            "VWAP Bounce (15m)",         "15m",  58),
    ("vwap_bands",      "VWAP Bands (5m)",           "5m",   58),
    ("vwap_bands",      "VWAP Bands (15m)",          "15m",  58),
    ("vwap_2sd",        "VWAP 2SD Reversion (15m)",  "15m",  58),
    ("vwap_2sd",        "VWAP 2SD Reversion (5m)",   "5m",   58),
    # Key level strategies
    ("quarterly_open",  "Quarterly Open (15m)",      "15m",  700),
    ("quarterly_open",  "Quarterly Open (1h)",       "1h",  700),
    ("quarterly_open",  "Quarterly Open (4h)",       "4h",  700),
    ("supply_demand",   "Supply & Demand (15m)",     "15m",  58),
    ("supply_demand",   "Supply & Demand (30m)",     "30m",  59),
    ("supply_demand",   "Supply & Demand (1h)",      "1h",  700),
    # Pullback / trend strategies
    ("ema200_pullback", "EMA200 Pullback (5m)",      "5m",   58),
    ("ema200_pullback", "EMA200 Pullback (15m)",     "15m",  58),
    ("ema200_pullback", "EMA200 Pullback (30m)",     "30m",  59),
    ("ema200_pullback", "EMA200 Pullback (1h)",      "1h",  700),
    ("ema_pullback",    "EMA Trend Pullback (5m)",   "5m",   58),
    ("ema_pullback",    "EMA Trend Pullback (15m)",  "15m",  58),
    ("ema_pullback",    "EMA Trend Pullback (30m)",  "30m",  59),
    ("ema_pullback",    "EMA Trend Pullback (1h)",   "1h",  700),
    # Session / open strategies
    ("opening_drive",   "Opening Drive (5m)",        "5m",   58),
    ("opening_drive",   "Opening Drive (15m)",       "15m",  58),
    ("opening_drive",   "Opening Drive (30m)",       "30m",  59),
    ("asia_range",      "Asia Range (15m)",          "15m",  58),
    ("asia_range",      "Asia Range (30m)",          "30m",  59),
    ("asia_range",      "Asia Range (1h)",           "1h",  700),
    ("gap_go",          "Gap & Go (5m)",             "5m",   58),
    ("gap_go",          "Gap & Go (15m)",            "15m",  58),
    # Sweep / structure
    ("sweep_reversal",  "Sweep Reversal (5m)",       "5m",   58),
    ("sweep_reversal",  "Sweep Reversal (15m)",      "15m",  58),
    ("sweep_reversal",  "Sweep Reversal (30m)",      "30m",  59),
    ("two_leg_pullback","Two-Leg Pullback (5m)",     "5m",   58),
    ("two_leg_pullback","Two-Leg Pullback (15m)",    "15m",  58),
    ("two_leg_pullback","Two-Leg Pullback (30m)",    "30m",  59),
    ("failed_breakout", "Failed Breakout (15m)",     "15m",  58),
    ("failed_breakout", "Failed Breakout (30m)",     "30m",  59),
    ("failed_breakout", "Failed Breakout (1h)",      "1h",  700),
    # ORB variants
    ("orb_retest",      "ORB Retest (5m)",           "5m",   58),
    ("orb_retest",      "ORB Retest (15m)",          "15m",  58),
    # Fibonacci
    ("fibonacci",       "Fibonacci Retrace (15m)",   "15m",  58),
    ("fibonacci",       "Fibonacci Retrace (1h)",    "1h",  700),
    # Triangle / patterns
    ("triangle",        "Triangle Break (30m)",      "30m",  59),
    ("triangle",        "Triangle Break (1h)",       "1h",  700),
    # Silver Bullet original (non-strict)
    ("silver_bullet",   "ICT SB Original (5m)",     "5m",   58),
    ("silver_bullet",   "ICT SB Original (15m)",    "15m",  58),
    # AMD / Power of 3
    ("amd",             "AMD (15m)",                 "15m",  58),
    ("amd",             "AMD (30m)",                 "30m",  59),
    # Breakout / reversal
    ("breakout",        "Breakout (15m)",            "15m",  58),
    ("breakout",        "Breakout (30m)",            "30m",  59),
    ("reversal",        "Reversal (15m)",            "15m",  58),
    ("reversal",        "Reversal (30m)",            "30m",  59),
    # News / continuation
    ("news_continuation","News Continuation (5m)",  "5m",   58),
    # Fade / mean revert
    ("fade",            "Fade / Counter (30m)",      "30m",  59),
    ("fade",            "Fade / Counter (1h)",       "1h",  700),
    ("mean_reversion",  "Mean Reversion (1h)",       "1h",  700),
    ("mean_reversion",  "Mean Reversion (30m)",      "30m",  59),
    # Range
    ("range_bound",     "Range Bound (15m)",         "15m",  58),
    ("range_bound",     "Range Bound (30m)",         "30m",  59),
]

print()
print("="*82)
print("  DEEP SEARCH — All untested Lucid strategies — target WR >= 72.1%")
print("  Any individual strategy with WR >= 72.1% keeps combined >= 72.1%")
print("="*82)
print("  {:<36} {:>4}  {:>7}  {:>6}  {:>7}  {:>8}  GR".format(
      "Strategy","TF","WR","PF","Trades","PortWR"))
print("-"*82)

qualifies = []
above_70  = []
all_results = []

for sid, label, tf, days in CANDIDATES:
    wr, pf, trades = test(sid, tf, days)
    if wr is not None:
        g = grade(wr, pf)
        new_wins = round(trades * wr / 100)
        port_wr  = round((BASE_WINS + new_wins) / (BASE_TRADES + trades) * 100, 1)
        ok = wr >= 72.1 and pf >= 1.0 and trades >= 10
        near = wr >= 68 and pf >= 1.0 and trades >= 10
        flag = " *** QUALIFIES" if ok else (" (near miss)" if near else "")
        print("  {:<36} {:>4}  {:>6.1f}%  {:>6.2f}  {:>7}  {:>7.1f}%   {}{}".format(
              label, tf, wr, pf, trades, port_wr, g, flag))
        all_results.append((label, sid, tf, wr, pf, trades, g, port_wr))
        if ok:
            qualifies.append((label, sid, tf, wr, pf, trades, g, port_wr))
        elif near:
            above_70.append((label, sid, tf, wr, pf, trades, g, port_wr))
    else:
        print("  {:<36} {:>4}  N/A".format(label, tf))

qualifies.sort(key=lambda x: x[3], reverse=True)
above_70.sort(key=lambda x: x[3], reverse=True)

print()
print("="*82)
print("  QUALIFIERS (WR >= 72.1%, PF >= 1.0, trades >= 10):")
for label, sid, tf, wr, pf, trades, g, port_wr in qualifies:
    print("  [{}] {:<36} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}  PortWR={:.1f}%".format(
          g, label, tf, wr, pf, trades, port_wr))
if not qualifies:
    print("  None hit 72.1% WR individually.")

print()
print("  NEAR MISSES (WR 68-72%, PF >= 1.0):")
for label, sid, tf, wr, pf, trades, g, port_wr in above_70:
    print("  [{}] {:<36} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}  PortWR={:.1f}%".format(
          g, label, tf, wr, pf, trades, port_wr))
if not above_70:
    print("  None in 68-72% range either.")

# Best profitable ones regardless of WR cutoff
print()
print("  TOP 10 by WR (profitable, >= 10 trades):")
top = sorted([r for r in all_results if r[4] >= 1.0 and r[5] >= 10], key=lambda x: x[3], reverse=True)[:10]
for label, sid, tf, wr, pf, trades, g, port_wr in top:
    print("  [{}] {:<36} {:>4}  WR={:.1f}%  PF={:.2f}  trades={}  PortWR={:.1f}%".format(
          g, label, tf, wr, pf, trades, port_wr))
print()
