"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { useCurrentUserId } from "@/hooks/useCurrentUserId";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

const INTERVALS: { label: string; value: string }[] = [
  { label: "5m",  value: "5m"  },
  { label: "15m", value: "15m" },
  { label: "1h",  value: "1h"  },
  { label: "4h",  value: "4h"  },
  { label: "1D",  value: "1d"  },
];

const SYMBOLS = ["MNQ1!", "MES1!", "MYM1!", "ES1!", "NQ1!", "RTY1!", "YM1!", "SPY", "QQQ"];

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface OpenTrade {
  _id: string;
  symbol: string;
  side: "Long" | "Short";
  entryPrice: number;
  stopLoss?: number;
  takeProfit?: number;
  qty: number;
}

function formatPrice(p: number) {
  return p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function TradingViewPanel() {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const seriesRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const priceLineRefs = useRef<any[]>([]);

  const [symbol, setSymbol] = useState("MNQ1!");
  const [interval, setInterval] = useState("15m");
  const [loading, setLoading] = useState(false);
  const [lastPrice, setLastPrice] = useState<number | null>(null);

  const userId = useCurrentUserId();
  const openTrades = useQuery(api.trades.getOpen, userId ? { userId } : "skip") as OpenTrade[] | undefined;

  // Find the open trade for the currently-selected symbol
  const activeTrade = openTrades?.find((t) => t.symbol === symbol) ?? null;

  const loadCandles = useCallback(async () => {
    if (!seriesRef.current) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/market/ohlcv?symbol=${symbol}&interval=${interval}`);
      const data = await res.json();
      const candles: Candle[] = (data.candles ?? []).map((c: Candle) => ({
        time: c.time as number,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));
      if (candles.length > 0) {
        seriesRef.current.setData(candles);
        setLastPrice(candles[candles.length - 1].close);
        chartRef.current?.timeScale().fitContent();
      }
    } finally {
      setLoading(false);
    }
  }, [symbol, interval]);

  // Draw / update TP-SL-Entry price lines whenever activeTrade changes
  const drawTradeLines = useCallback(() => {
    if (!seriesRef.current) return;

    // Remove old lines
    for (const pl of priceLineRefs.current) {
      try { seriesRef.current.removePriceLine(pl); } catch { /* already removed */ }
    }
    priceLineRefs.current = [];

    if (!activeTrade) return;

    // Lazy-import LineStyle to avoid SSR issues
    import("lightweight-charts").then(({ LineStyle }) => {
      const addLine = (price: number, color: string, title: string, style: number) => {
        const pl = seriesRef.current.createPriceLine({
          price,
          color,
          lineWidth: 1,
          lineStyle: style,
          axisLabelVisible: true,
          title,
        });
        priceLineRefs.current.push(pl);
      };

      addLine(activeTrade.entryPrice, "#f59e0b", "Entry", LineStyle.Solid);
      if (activeTrade.takeProfit) addLine(activeTrade.takeProfit, "#22c55e", "TP", LineStyle.Dashed);
      if (activeTrade.stopLoss)   addLine(activeTrade.stopLoss,   "#ef4444", "SL", LineStyle.Dashed);
    });
  }, [activeTrade]);

  // Init chart once on mount
  useEffect(() => {
    if (!containerRef.current) return;
    let chart: unknown;

    import("lightweight-charts").then(({ createChart, CrosshairMode }) => {
      if (!containerRef.current) return;

      chart = createChart(containerRef.current, {
        layout: {
          background: { color: "transparent" },
          textColor: "#94a3b8",
        },
        grid: {
          vertLines: { color: "rgba(148,163,184,0.08)" },
          horzLines: { color: "rgba(148,163,184,0.08)" },
        },
        crosshair: { mode: CrosshairMode.Normal },
        rightPriceScale: { borderColor: "rgba(148,163,184,0.15)" },
        timeScale: {
          borderColor: "rgba(148,163,184,0.15)",
          timeVisible: true,
          secondsVisible: false,
        },
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
      });

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const candleSeries = (chart as any).addCandlestickSeries({
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderUpColor: "#22c55e",
        borderDownColor: "#ef4444",
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444",
      });

      chartRef.current = chart;
      seriesRef.current = candleSeries;
    });

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (chartRef.current as any).applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (chart) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (chart as any).remove();
        chartRef.current = null;
        seriesRef.current = null;
        priceLineRefs.current = [];
      }
    };
  }, []);

  // Load candles when symbol/interval changes or chart initialises
  useEffect(() => {
    // Wait a tick for the chart to be ready
    const t = setTimeout(() => loadCandles(), 50);
    return () => clearTimeout(t);
  }, [loadCandles]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const id = window.setInterval(() => { void loadCandles(); }, 30_000);
    return () => window.clearInterval(id);
  }, [loadCandles]);

  // Redraw trade lines whenever active trade changes
  useEffect(() => {
    drawTradeLines();
  }, [drawTradeLines]);

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Toolbar */}
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          className="bg-input border border-border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {SYMBOLS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <div className="flex gap-1">
          {INTERVALS.map((i) => (
            <button
              key={i.value}
              onClick={() => setInterval(i.value)}
              className={cn(
                "px-2.5 py-1 rounded-lg text-xs font-medium transition-colors",
                interval === i.value
                  ? "bg-primary text-white"
                  : "bg-white/5 text-muted-foreground hover:text-foreground"
              )}
            >
              {i.label}
            </button>
          ))}
        </div>

        {lastPrice && (
          <span className="text-sm font-semibold tabular-nums ml-1">
            ${formatPrice(lastPrice)}
          </span>
        )}

        <Button
          variant="outline"
          size="sm"
          className="ml-auto text-xs gap-1.5"
          onClick={loadCandles}
          disabled={loading}
        >
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Active trade badge */}
      {activeTrade && (
        <div className="flex flex-wrap gap-3 px-3 py-2 rounded-xl bg-white/5 border border-border text-xs">
          <span className={cn("font-semibold", activeTrade.side === "Long" ? "text-emerald-400" : "text-red-400")}>
            {activeTrade.side} {activeTrade.qty}x {activeTrade.symbol}
          </span>
          <span className="text-muted-foreground">Entry <span className="text-amber-400 font-mono">{formatPrice(activeTrade.entryPrice)}</span></span>
          {activeTrade.takeProfit && (
            <span className="text-muted-foreground">TP <span className="text-emerald-400 font-mono">{formatPrice(activeTrade.takeProfit)}</span></span>
          )}
          {activeTrade.stopLoss && (
            <span className="text-muted-foreground">SL <span className="text-red-400 font-mono">{formatPrice(activeTrade.stopLoss)}</span></span>
          )}
        </div>
      )}

      {/* Chart */}
      <div className="flex-1 glass rounded-2xl overflow-hidden min-h-0 relative">
        <div ref={containerRef} className="absolute inset-0" />
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <span className="text-xs text-muted-foreground">Loading…</span>
          </div>
        )}
      </div>
    </div>
  );
}
