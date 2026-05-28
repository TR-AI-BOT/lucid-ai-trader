import { NextRequest, NextResponse } from "next/server";
import { createHmac } from "crypto";
import { ConvexHttpClient } from "convex/browser";
import { api } from "@/convex/_generated/api";
import type { TradingSignal } from "@/lib/types";
import { routeSignal } from "@/lib/state-manager";

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

function validateSecret(body: string, secret: string): boolean {
  const expected = createHmac("sha256", process.env.TRADINGVIEW_WEBHOOK_SECRET ?? "")
    .update(body)
    .digest("hex");
  return secret === expected || secret === process.env.TRADINGVIEW_WEBHOOK_SECRET;
}

export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  // Validate webhook secret
  const secret = (payload.secret as string) ?? "";
  if (!validateSecret(rawBody, secret)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { symbol, action, price, timeframe, reason, strategy, confidence, stopLoss, takeProfit } = payload as Record<string, string | number>;

  if (!["BUY", "SELL", "CLOSE"].includes(String(action))) {
    return NextResponse.json({ error: "Invalid action" }, { status: 400 });
  }

  const signal: TradingSignal = {
    symbol: String(symbol ?? "MES1!"),
    action: action as "BUY" | "SELL" | "CLOSE",
    price: Number(price ?? 0),
    timeframe: String(timeframe ?? "15m"),
    reason: String(reason ?? ""),
    strategy: strategy ? String(strategy) : undefined,
    confidence: confidence ? Number(confidence) : undefined,
    stopLoss: stopLoss ? Number(stopLoss) : undefined,
    takeProfit: takeProfit ? Number(takeProfit) : undefined,
  };

  // We need userId from the account — use a hardcoded system user for webhook context
  // In production, tie to a specific user account via webhook URL param or header
  const userId = req.nextUrl.searchParams.get("userId")
    ?? process.env.AUTONOMOUS_USER_ID
    ?? "system";

  // Store signal as pending
  const signalId = await convex.mutation(api.signals.add, {
    userId,
    symbol: signal.symbol,
    action: signal.action,
    price: signal.price,
    timeframe: signal.timeframe,
    reason: signal.reason,
    strategy: signal.strategy,
    confidence: signal.confidence,
    stopLoss: signal.stopLoss,
    takeProfit: signal.takeProfit,
    status: "pending",
  });

  // Get account and trading state for routing
  const [account, tradingState] = await Promise.all([
    convex.query(api.accounts.getActive, { userId }),
    convex.query(api.tradingState.get, { userId }),
  ]);

  if (!account) {
    await convex.mutation(api.signals.updateStatus, { signalId, status: "filtered" });
    return NextResponse.json({ ok: false, reason: "No active account" });
  }

  // Respect pause state
  if (tradingState.isPaused) {
    await convex.mutation(api.signals.updateStatus, { signalId, status: "filtered" });
    return NextResponse.json({ ok: false, reason: "Trading is paused" });
  }

  // Get daily trade count + open position side (for CLOSE direction)
  const [performance, openTrades] = await Promise.all([
    convex.query(api.signals.getPerformance, { userId }),
    convex.query(api.trades.getOpen, { userId }),
  ]);
  const dailyCount = performance.executed;
  const openTrade = openTrades.find((t) => t.symbol === signal.symbol);

  const result = await routeSignal(
    signal,
    account as Parameters<typeof routeSignal>[1],
    tradingState.mode,
    dailyCount,
    signalId,
    openTrade?.side as "Long" | "Short" | undefined
  );

  const finalStatus = result.action === "executed" ? "executed" : result.action === "pending_approval" ? "approved" : "filtered";
  await convex.mutation(api.signals.updateStatus, { signalId, status: finalStatus });

  if (result.action === "executed") {
    const qty = parseInt(process.env.ORDER_QTY ?? "1", 10);

    if (signal.action === "CLOSE") {
      // Close the matching open trade in Convex
      const openTrades = await convex.query(api.trades.getOpen, { userId });
      const openTrade = openTrades.find((t) => t.symbol === signal.symbol);
      if (openTrade) {
        await convex.mutation(api.trades.close, {
          tradeId: openTrade._id,
          exitPrice: signal.price,
          pnl: 0,
        });
      }
    } else {
      // Record new open trade with TP/SL
      await convex.mutation(api.trades.add, {
        userId,
        accountId: String(account._id),
        symbol: signal.symbol,
        side: signal.action === "BUY" ? "Long" : "Short",
        qty,
        entryPrice: signal.price,
        strategy: signal.strategy,
        stopLoss: signal.stopLoss,
        takeProfit: signal.takeProfit,
      });
    }
  }

  return NextResponse.json({ ok: true, ...result });
}
