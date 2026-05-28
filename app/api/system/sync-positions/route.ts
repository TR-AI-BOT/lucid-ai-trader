import { NextRequest, NextResponse } from "next/server";
import { ConvexHttpClient } from "convex/browser";
import { api } from "@/convex/_generated/api";
import * as tvPaper from "@/lib/tv-paper-trade";
import * as telegram from "@/lib/telegram";
import { YF_SYMBOL_MAP } from "@/lib/market-data";

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

// MES1! contract multiplier for P&L ($5 per point)
const CONTRACT_MULTIPLIERS: Record<string, number> = {
  "MES1!": 5,
  "ES1!": 50,
  "MNQ1!": 2,
  "NQ1!": 20,
  "MYM1!": 0.5,
  "YM1!": 5,
  "M2K1!": 10,
  "RTY1!": 50,
};

function calcPnl(side: "Long" | "Short", entry: number, exit: number, qty: number, symbol: string): number {
  const multiplier = CONTRACT_MULTIPLIERS[symbol] ?? 1;
  const direction = side === "Long" ? 1 : -1;
  return direction * (exit - entry) * qty * multiplier;
}

export async function POST(req: NextRequest) {
  const userId = req.nextUrl.searchParams.get("userId")
    ?? process.env.AUTONOMOUS_USER_ID
    ?? "system";

  // Only relevant when TV Paper is active
  if (process.env.TV_PAPER_ENABLED !== "true") {
    return NextResponse.json({ ok: true, synced: 0, message: "TV Paper not enabled" });
  }

  // Read TradingView's positions panel text
  const panelText = await tvPaper.getPositionsPanelText();
  if (panelText === null) {
    // CDP unavailable — TradingView not running or not accessible
    return NextResponse.json({ ok: true, synced: 0, message: "TradingView not reachable" });
  }

  // Get Convex open trades for this user
  const openTrades = await convex.query(api.trades.getOpen, { userId });
  if (openTrades.length === 0) {
    return NextResponse.json({ ok: true, synced: 0, message: "No open trades" });
  }

  // Get account for balance/day P&L
  const account = await convex.query(api.accounts.getActive, { userId });

  let synced = 0;
  const closed: string[] = [];

  for (const trade of openTrades) {
    // A trade that was opened less than 10 seconds ago may not appear yet — skip
    const ageMs = Date.now() - trade.executedAt;
    if (ageMs < 10_000) continue;

    // If the symbol is NOT found in the TradingView positions panel text, it was manually closed
    const symbolInPanel = panelText.toLowerCase().includes(trade.symbol.toLowerCase());
    if (symbolInPanel) continue;

    // Manually closed — fetch current market price as exit approximation
    let exitPrice = trade.entryPrice;
    try {
      const yfSym = YF_SYMBOL_MAP[trade.symbol] ?? trade.symbol;
      const now = Math.floor(Date.now() / 1000);
      const yf = await fetch(
        `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(yfSym)}?period1=${now - 300}&period2=${now}&interval=1m`,
        { headers: { "User-Agent": "Mozilla/5.0" } }
      ).catch(() => null);
      if (yf?.ok) {
        const data = await yf.json() as { chart?: { result?: Array<{ indicators?: { quote?: Array<{ close?: number[] }> } }> } };
        const closes = data.chart?.result?.[0]?.indicators?.quote?.[0]?.close ?? [];
        const last = closes.filter(Boolean).at(-1);
        if (last) exitPrice = last;
      }
    } catch { /* use entry as fallback */ }

    const pnl = calcPnl(trade.side, trade.entryPrice, exitPrice, trade.qty, trade.symbol);

    // Close in Convex
    await convex.mutation(api.trades.close, {
      tradeId: trade._id,
      exitPrice,
      pnl,
    });

    // Day P&L and balance from account
    const dayPnl = (account?.dailyPnl ?? 0) + pnl;
    const balance = (account?.currentBalance ?? 0) + pnl;

    // Send Telegram manual exit notification
    await telegram.sendManualExitAlert({
      side: trade.side,
      symbol: trade.symbol,
      strategy: trade.strategy,
      entryPrice: trade.entryPrice,
      exitPrice,
      pnl,
      dayPnl,
      balance,
    });

    closed.push(trade.symbol);
    synced++;
  }

  return NextResponse.json({ ok: true, synced, closed });
}
