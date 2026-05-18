"""Debug harmonic signal generation."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

from backtesting.data_fetcher import fetch_ohlcv
from backtesting.strategies import BACKTEST_STRATEGIES
from datetime import datetime, timedelta

start = (datetime.today() - timedelta(days=700)).strftime("%Y-%m-%d")
end   = datetime.today().strftime("%Y-%m-%d")

for tf in ["1h", "1d"]:
    df = fetch_ohlcv("MNQ=F", start, end, tf)
    print(f"\nTimeframe: {tf}  Bars: {len(df)}")
    for name in ["abcd", "gartley", "bat", "butterfly", "crab"]:
        entry = BACKTEST_STRATEGIES[name]
        fn = entry["fn"] if isinstance(entry, dict) else entry
        sigs = fn(df)
        buys  = [s for s in sigs if s.get("action") in ("BUY","SELL","ENTRY","LONG","SHORT")]
        print(f"  {name:<12}: {len(sigs)} signals total  |  first 3: {sigs[:3]}")
