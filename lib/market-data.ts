import type { Candle } from "./types";

export const YF_SYMBOL_MAP: Record<string, string> = {
  "MES1!": "ES=F",
  "MNQ1!": "NQ=F",
  "M2K1!": "RTY=F",
  "MYM1!": "YM=F",
  "MGC1!": "GC=F",
  "MCL1!": "CL=F",
  "MBT1!": "BTC=F",
  "ES1!":  "ES=F",
  "NQ1!":  "NQ=F",
  "RTY1!": "RTY=F",
  "YM1!":  "YM=F",
  "GC1!":  "GC=F",
  "SI1!":  "SI=F",
  "CL1!":  "CL=F",
  "NG1!":  "NG=F",
  "HG1!":  "HG=F",
  "ZB1!":  "ZB=F",
  "ZN1!":  "ZN=F",
  "EURUSD": "EURUSD=X",
  "GBPUSD": "GBPUSD=X",
  "USDJPY": "JPY=X",
  "USDCHF": "CHF=X",
  "AUDUSD": "AUDUSD=X",
  "NZDUSD": "NZDUSD=X",
  "USDCAD": "CAD=X",
  "EURGBP": "EURGBP=X",
  "EURJPY": "EURJPY=X",
  "GBPJPY": "GBPJPY=X",
  "BTCUSD": "BTC-USD",
  "ETHUSD": "ETH-USD",
  // TradeLocker direct symbols
  "NAS100.R": "NQ=F",
  "SPX500.R": "ES=F",
  "US30.R":   "YM=F",
};

export const YF_INTERVAL_MAP: Record<string, string> = {
  "5m":  "5m",
  "15m": "15m",
  "1h":  "60m",
  "1d":  "1d",
};

// How many bars to request per timeframe
const BARS_NEEDED: Record<string, number> = {
  "5m":  80,
  "15m": 100,
  "1h":  100,
  "1d":  100,
};

// Seconds of lookback per timeframe (with 1.5x buffer for weekends/holidays)
const LOOKBACK_SECONDS: Record<string, number> = {
  "5m":  80  * 5  * 60 * 2,
  "15m": 100 * 15 * 60 * 2,
  "1h":  100 * 60 * 60 * 2,
  "1d":  100 * 24 * 60 * 60 * 1.5,
};

// Get current time in New York / Eastern Time (handles EST and EDT automatically)
export function getNYTime(): { day: number; hours: number; minutes: number; dateStr: string } {
  const now = new Date();
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);

  const get = (type: string) => parts.find(p => p.type === type)?.value ?? "0";
  const dayMap: Record<string, number> = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };

  let hours = parseInt(get("hour"));
  if (hours === 24) hours = 0; // Intl sometimes returns 24 for midnight

  return {
    day: dayMap[get("weekday")] ?? 1,
    hours,
    minutes: parseInt(get("minute")),
    dateStr: `${get("year")}-${get("month")}-${get("day")}`,
  };
}

// Returns the Unix timestamp for today's NY session open (9:30 AM ET)
function todaySessionStart(): number {
  const { dateStr } = getNYTime();
  // Parse the NY date and build 9:30 AM ET as a UTC timestamp
  const [year, month, day] = dateStr.split("-").map(Number);
  // Create a date string at 09:30 ET — let the browser/Node resolve the offset
  const d = new Date(`${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}T09:30:00`);
  // Adjust: subtract the NY offset from UTC so we get the correct UTC epoch for 9:30 AM ET
  const nyOffset = new Date(d.toLocaleString("en-US", { timeZone: "America/New_York" })).getTime() - d.getTime();
  return Math.floor((d.getTime() - nyOffset) / 1000);
}

export async function fetchLiveCandles(symbol: string, timeframe: string): Promise<Candle[]> {
  const yfSymbol = YF_SYMBOL_MAP[symbol] ?? symbol;
  const interval = YF_INTERVAL_MAP[timeframe] ?? "60m";
  const now = Math.floor(Date.now() / 1000);

  let period1: number;
  if (timeframe === "5m") {
    // ORB: fetch from today's market open so the first bars are the opening range
    period1 = todaySessionStart();
  } else {
    period1 = now - (LOOKBACK_SECONDS[timeframe] ?? 7 * 24 * 3600);
  }

  const url =
    `https://query1.finance.yahoo.com/v8/finance/chart/` +
    `${encodeURIComponent(yfSymbol)}` +
    `?period1=${period1}&period2=${now}&interval=${interval}&events=history`;

  const res = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
      "Accept": "application/json",
    },
    next: { revalidate: 0 },
  });

  if (!res.ok) throw new Error(`Yahoo Finance ${res.status} for ${yfSymbol}`);

  const json = await res.json();
  const result = json?.chart?.result?.[0];
  if (!result) return [];

  const timestamps: number[] = result.timestamp ?? [];
  const q = result.indicators?.quote?.[0] ?? {};

  return timestamps
    .map((t, i) => ({
      time: t,
      open:   (q.open?.[i]   ?? 0) as number,
      high:   (q.high?.[i]   ?? 0) as number,
      low:    (q.low?.[i]    ?? 0) as number,
      close:  (q.close?.[i]  ?? 0) as number,
      volume: (q.volume?.[i] ?? 0) as number,
    }))
    .filter(c => c.close > 0);
}

// Regular session: 9:30 AM – 4:00 PM New York time, Mon–Fri
export function isMarketHours(): boolean {
  const { day, hours, minutes } = getNYTime();
  if (day === 0 || day === 6) return false; // weekend
  const mins = hours * 60 + minutes;
  return mins >= 9 * 60 + 30 && mins < 16 * 60; // 9:30 AM – 4:00 PM ET
}

// All strategies run every 5 minutes during market hours.
// Only daily strategies are gated to the market-open window.
export function isTimeframeDue(timeframe: string): boolean {
  if (timeframe === "1d") {
    const { hours, minutes } = getNYTime();
    const mins = hours * 60 + minutes;
    return mins >= 9 * 60 + 30 && mins < 9 * 60 + 35; // 9:30–9:35 AM ET only
  }
  return true; // 5m, 15m, 1h — always scan during market hours
}

// Human-readable New York time string (for logs)
export function nyTimeString(): string {
  return new Date().toLocaleString("en-US", {
    timeZone: "America/New_York",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  }) + " ET";
}
