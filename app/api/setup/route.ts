import { NextRequest, NextResponse } from "next/server";
import { ConvexHttpClient } from "convex/browser";
import { api } from "@/convex/_generated/api";

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

// GET — ensure account exists (initial setup)
export async function GET(req: NextRequest) {
  const userId = req.nextUrl.searchParams.get("userId") ?? process.env.AUTONOMOUS_USER_ID ?? "";
  if (!userId) return NextResponse.json({ error: "No userId" }, { status: 400 });

  const existing = await convex.query(api.accounts.getActive, { userId });
  if (existing) return NextResponse.json({ ok: true, message: "Account already exists", account: existing });

  const accountId = await convex.mutation(api.accounts.create, {
    userId,
    name: "Paper Account (Souley100x)",
    accountType: "DEMO",
    riskMode: "BALANCED",
    tradingMode: "FULL_AUTO",
    broker: "paper",
    startingBalance: 10000,
    dailyLossLimit: 500,
    maxDrawdownPct: 10,
    maxContracts: 5,
  });

  return NextResponse.json({ ok: true, message: "Account created", accountId });
}

// POST — reset all data and set fresh $10k starting balance
export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const userId = body.userId ?? process.env.AUTONOMOUS_USER_ID ?? "";
  const balance: number = body.balance ?? 10000;

  if (!userId) return NextResponse.json({ error: "No userId" }, { status: 400 });

  const [deletedTrades, deletedSignals] = await Promise.all([
    convex.mutation(api.trades.deleteAll, { userId }),
    convex.mutation(api.signals.deleteAll, { userId }),
  ]);

  const existing = await convex.query(api.accounts.getActive, { userId });
  let accountId: string;
  if (existing) {
    await convex.mutation(api.accounts.resetBalance, { userId, balance });
    accountId = existing._id;
  } else {
    accountId = await convex.mutation(api.accounts.create, {
      userId,
      name: "Paper Account (Souley100x)",
      accountType: "DEMO",
      riskMode: "BALANCED",
      tradingMode: "FULL_AUTO",
      broker: "paper",
      startingBalance: balance,
      dailyLossLimit: 500,
      maxDrawdownPct: 10,
      maxContracts: 5,
    });
  }

  return NextResponse.json({
    ok: true,
    message: `Reset complete — $${balance.toLocaleString()} starting balance`,
    deletedTrades,
    deletedSignals,
    accountId,
  });
}
