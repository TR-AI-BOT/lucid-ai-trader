import type { Candle, SignalResult } from "../types";
import { atr, pivotHigh, pivotLow, rsi, clamp } from "./utils";

// ── Fibonacci ratio constants ────────────────────────────────────────────────
const FIB = {
  R382: 0.382, R500: 0.500, R618: 0.618, R705: 0.705,
  R786: 0.786, R886: 0.886, R100: 1.000, R127: 1.272, R161: 1.618,
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function ratio(a: number, b: number): number {
  return b === 0 ? 0 : Math.abs(a / b);
}

function near(val: number, target: number, tol = 0.05): boolean {
  return Math.abs(val - target) <= tol;
}

// Find the last N swing highs/lows for XABCD detection
function swings(candles: Candle[], lookback = 5): { highs: number[]; lows: number[] } {
  const highs: number[] = [];
  const lows:  number[] = [];
  for (let i = lookback; i < candles.length - lookback; i++) {
    const slice = candles.slice(i - lookback, i + lookback + 1);
    const midH = candles[i].high;
    const midL = candles[i].low;
    if (slice.every(c => c.high <= midH)) highs.push(midH);
    if (slice.every(c => c.low  >= midL)) lows.push(midL);
  }
  return { highs: highs.slice(-4), lows: lows.slice(-4) };
}

// Build XABCD points from alternating swing highs/lows.
// For a bullish pattern: X=low, A=high, B=low, C=high, D=low (entry)
// For a bearish pattern: X=high, A=low, B=high, C=low, D=high (entry)
function buildXABCD(
  candles: Candle[],
  bullish: boolean
): { X: number; A: number; B: number; C: number; D: number } | null {
  const sw = swings(candles);
  if (sw.highs.length < 2 || sw.lows.length < 2) return null;
  if (bullish) {
    // X low → A high → B low → C high → D low (current close as proxy for D)
    const X = sw.lows[sw.lows.length - 2];
    const A = sw.highs[sw.highs.length - 2];
    const B = sw.lows[sw.lows.length - 1];
    const C = sw.highs[sw.highs.length - 1];
    const D = candles[candles.length - 1].close;
    if (X >= A || B >= A || C <= B) return null;
    return { X, A, B, C, D };
  } else {
    const X = sw.highs[sw.highs.length - 2];
    const A = sw.lows[sw.lows.length - 2];
    const B = sw.highs[sw.highs.length - 1];
    const C = sw.lows[sw.lows.length - 1];
    const D = candles[candles.length - 1].close;
    if (X <= A || B <= A || C >= B) return null;
    return { X, A, B, C, D };
  }
}

// ── ABCD Pattern (simplest — 4 point, AB≈CD) ────────────────────────────────
export function analyzeAbcd(candles: Candle[]): SignalResult | null {
  if (candles.length < 20) return null;
  const atrVal = atr(candles);
  const sw = swings(candles, 4);
  if (sw.highs.length < 2 || sw.lows.length < 2) return null;

  const rsiVal = rsi(candles);

  // Bullish ABCD: A=high, B=low, C=high, D=low (retest of AB leg)
  const A = sw.highs[sw.highs.length - 2];
  const B = sw.lows[sw.lows.length - 2];
  const C = sw.highs[sw.highs.length - 1];
  const D = candles[candles.length - 1].close;
  const AB = A - B;
  const CD = C - D;
  const ABratio = ratio(CD, AB);

  if (B < A && C > B && D < C && near(ABratio, 1.0, 0.12) && rsiVal < 45) {
    return {
      setupType:  "ABCD_BULLISH",
      direction:  "BULLISH",
      confidence: clamp(0.65 + (1 - Math.abs(ABratio - 1)) * 0.1, 0.65, 0.78),
      reason:     `ABCD bullish: AB=${AB.toFixed(2)} ≈ CD=${CD.toFixed(2)} (ratio ${ABratio.toFixed(2)}) at D=${D.toFixed(2)}`,
      entryPrice: D,
      stopPrice:  D - 1.5 * atrVal,
      target1:    B,
      target2:    A,
    };
  }

  // Bearish ABCD
  const Ah = sw.lows[sw.lows.length - 2];
  const Bh = sw.highs[sw.highs.length - 2];
  const Ch = sw.lows[sw.lows.length - 1];
  const Dh = candles[candles.length - 1].close;
  const ABh = Bh - Ah;
  const CDh = Dh - Ch;
  const ABrh = ratio(CDh, ABh);

  if (Bh > Ah && Ch < Bh && Dh > Ch && near(ABrh, 1.0, 0.12) && rsiVal > 55) {
    return {
      setupType:  "ABCD_BEARISH",
      direction:  "BEARISH",
      confidence: clamp(0.65 + (1 - Math.abs(ABrh - 1)) * 0.1, 0.65, 0.78),
      reason:     `ABCD bearish: AB=${ABh.toFixed(2)} ≈ CD=${CDh.toFixed(2)} (ratio ${ABrh.toFixed(2)}) at D=${Dh.toFixed(2)}`,
      entryPrice: Dh,
      stopPrice:  Dh + 1.5 * atrVal,
      target1:    Bh,
      target2:    Ah,
    };
  }

  return null;
}

// ── Gartley (bullish/bearish) ────────────────────────────────────────────────
// AB = 61.8% of XA  |  BC = 38.2–88.6% of AB  |  CD = 78.6% of XA (D point)
export function analyzeGartley(candles: Candle[]): SignalResult | null {
  if (candles.length < 30) return null;
  const atrVal = atr(candles);
  const rsiVal = rsi(candles);

  for (const bullish of [true, false]) {
    const pts = buildXABCD(candles, bullish);
    if (!pts) continue;
    const { X, A, B, C, D } = pts;

    const XA = Math.abs(A - X);
    const AB = Math.abs(B - A);
    const BC = Math.abs(C - B);
    const CD = Math.abs(D - C);
    if (XA === 0 || AB === 0) continue;

    const AB_XA = ratio(AB, XA);
    const BC_AB = ratio(BC, AB);
    const D_XA  = ratio(Math.abs(D - X), XA);   // D should be 78.6% retrace of XA from X

    if (
      near(AB_XA, FIB.R618, 0.07) &&
      BC_AB >= FIB.R382 - 0.05 && BC_AB <= FIB.R886 + 0.05 &&
      near(D_XA, FIB.R786, 0.07) &&
      (bullish ? rsiVal < 50 : rsiVal > 50)
    ) {
      const score = 1 - (Math.abs(AB_XA - FIB.R618) + Math.abs(D_XA - FIB.R786)) / 2;
      return {
        setupType:  bullish ? "GARTLEY_BULLISH" : "GARTLEY_BEARISH",
        direction:  bullish ? "BULLISH" : "BEARISH",
        confidence: clamp(0.68 + score * 0.10, 0.68, 0.82),
        reason:     `Gartley ${bullish ? "bullish" : "bearish"}: AB/XA=${AB_XA.toFixed(3)} D/XA=${D_XA.toFixed(3)} at D=${D.toFixed(2)}`,
        entryPrice: D,
        stopPrice:  bullish ? X - atrVal * 0.5 : X + atrVal * 0.5,
        target1:    bullish ? C : C,   // 38.2% of AD leg
        target2:    bullish ? A : A,   // 61.8% of AD leg
      };
    }
  }
  return null;
}

// ── Bat Pattern ──────────────────────────────────────────────────────────────
// AB = 38.2–50% of XA  |  BC = 38.2–88.6% of AB  |  D = 88.6% of XA
export function analyzeBat(candles: Candle[]): SignalResult | null {
  if (candles.length < 30) return null;
  const atrVal = atr(candles);
  const rsiVal = rsi(candles);

  for (const bullish of [true, false]) {
    const pts = buildXABCD(candles, bullish);
    if (!pts) continue;
    const { X, A, B, C, D } = pts;

    const XA   = Math.abs(A - X);
    const AB   = Math.abs(B - A);
    const BC   = Math.abs(C - B);
    if (XA === 0 || AB === 0) continue;

    const AB_XA = ratio(AB, XA);
    const BC_AB = ratio(BC, AB);
    const D_XA  = ratio(Math.abs(D - X), XA);

    if (
      AB_XA >= FIB.R382 - 0.04 && AB_XA <= FIB.R500 + 0.04 &&
      BC_AB >= FIB.R382 - 0.05 && BC_AB <= FIB.R886 + 0.05 &&
      near(D_XA, FIB.R886, 0.06) &&
      (bullish ? rsiVal < 50 : rsiVal > 50)
    ) {
      const score = 1 - Math.abs(D_XA - FIB.R886) * 5;
      return {
        setupType:  bullish ? "BAT_BULLISH" : "BAT_BEARISH",
        direction:  bullish ? "BULLISH" : "BEARISH",
        confidence: clamp(0.68 + score * 0.10, 0.68, 0.82),
        reason:     `Bat ${bullish ? "bullish" : "bearish"}: AB/XA=${AB_XA.toFixed(3)} D/XA=${D_XA.toFixed(3)} at D=${D.toFixed(2)}`,
        entryPrice: D,
        stopPrice:  bullish ? X - atrVal * 0.3 : X + atrVal * 0.3,
        target1:    bullish ? C : C,
        target2:    bullish ? A : A,
      };
    }
  }
  return null;
}

// ── Butterfly Pattern ────────────────────────────────────────────────────────
// AB = 78.6% of XA  |  BC = 38.2–88.6% of AB  |  D = 127–161.8% extension of XA
export function analyzeButterfly(candles: Candle[]): SignalResult | null {
  if (candles.length < 30) return null;
  const atrVal = atr(candles);
  const rsiVal = rsi(candles);

  for (const bullish of [true, false]) {
    const pts = buildXABCD(candles, bullish);
    if (!pts) continue;
    const { X, A, B, C, D } = pts;

    const XA    = Math.abs(A - X);
    const AB    = Math.abs(B - A);
    const BC    = Math.abs(C - B);
    if (XA === 0 || AB === 0) continue;

    const AB_XA = ratio(AB, XA);
    const BC_AB = ratio(BC, AB);
    // For butterfly, D extends BEYOND X (D_XA > 1.0)
    const D_XA  = ratio(Math.abs(D - X), XA);

    if (
      near(AB_XA, FIB.R786, 0.07) &&
      BC_AB >= FIB.R382 - 0.05 && BC_AB <= FIB.R886 + 0.05 &&
      D_XA >= FIB.R127 - 0.06 && D_XA <= FIB.R161 + 0.10 &&
      (bullish ? rsiVal < 45 : rsiVal > 55)
    ) {
      const score = 1 - (Math.abs(AB_XA - FIB.R786) + Math.abs(D_XA - FIB.R127)) / 2;
      return {
        setupType:  bullish ? "BUTTERFLY_BULLISH" : "BUTTERFLY_BEARISH",
        direction:  bullish ? "BULLISH" : "BEARISH",
        confidence: clamp(0.70 + score * 0.10, 0.70, 0.84),
        reason:     `Butterfly ${bullish ? "bullish" : "bearish"}: AB/XA=${AB_XA.toFixed(3)} D/XA=${D_XA.toFixed(3)} (extension) at D=${D.toFixed(2)}`,
        entryPrice: D,
        stopPrice:  bullish ? D - 1.2 * atrVal : D + 1.2 * atrVal,
        target1:    bullish ? C : C,
        target2:    bullish ? A : A,
      };
    }
  }
  return null;
}

// ── Crab Pattern ─────────────────────────────────────────────────────────────
// AB = 38.2–61.8% of XA  |  BC = 38.2–88.6% of AB  |  D = 161.8% of XA
export function analyzeCrab(candles: Candle[]): SignalResult | null {
  if (candles.length < 30) return null;
  const atrVal = atr(candles);
  const rsiVal = rsi(candles);

  for (const bullish of [true, false]) {
    const pts = buildXABCD(candles, bullish);
    if (!pts) continue;
    const { X, A, B, C, D } = pts;

    const XA    = Math.abs(A - X);
    const AB    = Math.abs(B - A);
    const BC    = Math.abs(C - B);
    if (XA === 0 || AB === 0) continue;

    const AB_XA = ratio(AB, XA);
    const BC_AB = ratio(BC, AB);
    const D_XA  = ratio(Math.abs(D - X), XA);

    if (
      AB_XA >= FIB.R382 - 0.05 && AB_XA <= FIB.R618 + 0.05 &&
      BC_AB >= FIB.R382 - 0.05 && BC_AB <= FIB.R886 + 0.05 &&
      near(D_XA, FIB.R161, 0.08) &&
      (bullish ? rsiVal < 40 : rsiVal > 60)
    ) {
      const score = 1 - Math.abs(D_XA - FIB.R161) * 3;
      return {
        setupType:  bullish ? "CRAB_BULLISH" : "CRAB_BEARISH",
        direction:  bullish ? "BULLISH" : "BEARISH",
        confidence: clamp(0.70 + score * 0.12, 0.70, 0.85),
        reason:     `Crab ${bullish ? "bullish" : "bearish"}: AB/XA=${AB_XA.toFixed(3)} D/XA=${D_XA.toFixed(3)} (161.8% ext) at D=${D.toFixed(2)}`,
        entryPrice: D,
        stopPrice:  bullish ? D - atrVal : D + atrVal,
        target1:    bullish ? C : C,
        target2:    bullish ? A : A,
      };
    }
  }
  return null;
}

// ── Combined harmonic scanner ─────────────────────────────────────────────────
export function analyzeHarmonic(candles: Candle[]): SignalResult | null {
  // Run all patterns in order of typical accuracy; return the first match
  return (
    analyzeCrab(candles) ??
    analyzeBat(candles) ??
    analyzeGartley(candles) ??
    analyzeButterfly(candles) ??
    analyzeAbcd(candles)
  );
}
