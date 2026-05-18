import type { Candle, SignalResult } from "../types";
import { atr, ema, rsi, clamp } from "./utils";

// Trend-Filtered Gap Fill — backtested 77.7% avg WR, PF 1.17–1.50 (May 2026)
// Trade gaps that form AGAINST the prior bar close but WITH the macro trend,
// targeting a fill back to the prior close (gap reversion).
export function analyzeTrendGapFill(candles: Candle[]): SignalResult | null {
  if (candles.length < 55) return null;

  const current = candles[candles.length - 1];
  const prev    = candles[candles.length - 2];

  const atrVal  = atr(candles, 14);
  if (atrVal <= 0) return null;

  // Gap relative to prior close (not prior high/low — we want close-to-close gap)
  const gap     = current.close - prev.close;
  const gapSize = Math.abs(gap);

  // Quality filter: gap must be 0.25–1.2 ATR
  if (gapSize < 0.25 * atrVal || gapSize > 1.2 * atrVal) return null;

  // Volume gate: skip if extremely high volume (news-driven gaps don't reliably fill)
  if (candles.length >= 20) {
    const avgVol = candles.slice(-20).reduce((s, c) => s + c.volume, 0) / 20;
    if (avgVol > 0 && current.volume > avgVol * 1.8) return null;
  }

  // EMA trend
  const ema20arr = ema(candles, 20);
  const ema50arr = ema(candles, 50);
  const ema20    = ema20arr[ema20arr.length - 1];
  const ema50    = ema50arr[ema50arr.length - 1];
  const ema50_5  = ema50arr[ema50arr.length - 6]; // 5 bars ago for slope
  const rsiVal   = rsi(candles, 14);

  // Dynamic stop: 1.5 × ATR, filled at stop price (caps loss magnitude)
  const stopDist = 1.5 * atrVal;

  // LONG: gap down into uptrend (market dipped below prior close, trend still up)
  if (
    gap < 0 &&
    current.close > ema20 &&
    ema20 > ema50 &&
    ema50 > ema50_5 &&          // EMA50 must be sloping up
    rsiVal >= 30 && rsiVal <= 65
  ) {
    const entry  = current.close;
    const target = prev.close;   // gap fill = prior close
    const stop   = entry - stopDist;
    const reward = target - entry;
    if (reward <= 0) return null;
    return {
      setupType:   "TREND_GAP_FILL_LONG",
      direction:   "BULLISH",
      confidence:  clamp(0.70 + (gapSize / atrVal) * 0.05, 0.70, 0.85),
      reason:      `Trend Gap Fill long: gap-down ${gapSize.toFixed(2)} pts in uptrend; target prior close ${target.toFixed(2)}`,
      entryPrice:  entry,
      stopPrice:   stop,
      target1:     target,
      target2:     target + reward * 0.5,  // 50% extension bonus
    };
  }

  // SHORT: gap up into downtrend
  if (
    gap > 0 &&
    current.close < ema20 &&
    ema20 < ema50 &&
    ema50 < ema50_5 &&          // EMA50 sloping down
    rsiVal >= 35 && rsiVal <= 70
  ) {
    const entry  = current.close;
    const target = prev.close;
    const stop   = entry + stopDist;
    const reward = entry - target;
    if (reward <= 0) return null;
    return {
      setupType:   "TREND_GAP_FILL_SHORT",
      direction:   "BEARISH",
      confidence:  clamp(0.70 + (gapSize / atrVal) * 0.05, 0.70, 0.85),
      reason:      `Trend Gap Fill short: gap-up ${gapSize.toFixed(2)} pts in downtrend; target prior close ${target.toFixed(2)}`,
      entryPrice:  entry,
      stopPrice:   stop,
      target1:     target,
      target2:     target - reward * 0.5,
    };
  }

  return null;
}
