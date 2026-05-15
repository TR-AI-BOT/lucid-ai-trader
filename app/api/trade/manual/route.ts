import { NextRequest, NextResponse } from "next/server";
import { ConvexHttpClient } from "convex/browser";
import { api } from "@/convex/_generated/api";
import type { Id } from "@/convex/_generated/dataModel";
import * as brokerRegistry from "@/lib/broker-registry";
import { ensureBrokerReady } from "@/lib/broker-init";
import { YF_SYMBOL_MAP, isWeekend } from "@/lib/market-data";

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

async function fetchCurrentPrice(symbol: string): Promise<number> {
  try {
    const yfSymbol = YF_SYMBOL_MAP[symbol] ?? symbol;
    const now = Math.floor(Date.now() / 1000);
    const res = await fetch(
      `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(yfSymbol)}?period1=${now - 3600}&period2=${now}&interval=1m`,
      { headers: { "User-Agent": "Mozilla/5.0", "Accept": "application/json" }, next: { revalidate: 0 } }
    );
    const json = await res.json();
    const closes: number[] = json?.chart?.result?.[0]?.indicators?.quote?.[0]?.close ?? [];
    return closes.filter(Boolean).at(-1) ?? 0;
  } catch {
    return 0;
  }
}

export async function POST(req: NextRequest) {
  const body = await req.json() as {
    userId: string;
    symbol: string;
    action: "BUY" | "SELL" | "CLOSE";
    price?: number;
    reason?: string;
  };

  const { userId, symbol, action, reason } = body;
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  if (isWeekend()) {
    return NextResponse.json({ ok: false, message: "Markets are closed for the weekend. Trading resumes Monday 9:30 AM ET." }, { status: 400 });
  }

  await ensureBrokerReady(userId);

  const livePrice = body.price && body.price > 0 ? body.price : await fetchCurrentPrice(symbol);

  const signalId = await convex.mutation(api.signals.add, {
    userId,
    symbol,
    action,
    price: livePrice,
    timeframe: "manual",
    reason: reason ?? "Manual trade",
    status: "approved",
  });

  const qty = parseInt(process.env.ORDER_QTY ?? "1", 10);

  let result;
  if (action === "CLOSE") {
    result = await brokerRegistry.closePosition(symbol);
  } else {
    result = await brokerRegistry.placeOrder(symbol, qty, action === "BUY" ? "Buy" : "Sell");
  }

  await convex.mutation(api.signals.updateStatus, {
    signalId,
    status: result.ok ? "executed" : "filtered",
  });

  if (result.ok) {
    const account = await convex.query(api.accounts.getActive, { userId });

    if (action === "CLOSE") {
      const openTrades = await convex.query(api.trades.list, { userId, status: "open" });
      const openTrade = openTrades.find((t) => t.symbol === symbol);
      if (openTrade) {
        const exitPrice = livePrice || openTrade.entryPrice;
        const pnl = Math.round(
          (openTrade.side === "Long"
            ? (exitPrice - openTrade.entryPrice) * openTrade.qty
            : (openTrade.entryPrice - exitPrice) * openTrade.qty) * 100
        ) / 100;

        await convex.mutation(api.trades.close, {
          tradeId: openTrade._id as Id<"trades">,
          exitPrice,
          pnl,
        });

        // Update account balance with realized P&L
        if (account) {
          await convex.mutation(api.accounts.updateBalance, {
            accountId: account._id as Id<"accounts">,
            newBalance: Math.round((account.currentBalance + pnl) * 100) / 100,
            dailyPnl: Math.round((account.dailyPnl + pnl) * 100) / 100,
            totalPnl: Math.round((account.totalPnl + pnl) * 100) / 100,
          });
        }
      }
    } else {
      await convex.mutation(api.trades.add, {
        userId,
        accountId: account?._id ?? "manual",
        symbol,
        side: action === "BUY" ? "Long" : "Short",
        qty,
        entryPrice: livePrice,
        strategy: "manual",
      });
    }
  }

  return NextResponse.json({ ok: result.ok, message: result.message, entryPrice: livePrice });
}
