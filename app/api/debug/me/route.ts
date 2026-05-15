import { NextResponse } from "next/server";
import { ConvexHttpClient } from "convex/browser";
import { api } from "@/convex/_generated/api";

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

export async function GET() {
  const autonomousUserId = process.env.AUTONOMOUS_USER_ID ?? "(not set)";

  let tradeCount = 0;
  try {
    const trades = await convex.query(api.trades.list, { userId: autonomousUserId });
    tradeCount = trades.length;
  } catch {}

  return NextResponse.json({
    autonomousUserId,
    tradeCountForAutonomousUser: tradeCount,
    note: "Compare autonomousUserId with your browser userId. Open /api/debug/me while logged in and check browser console for userId via useCurrentUserId hook.",
  });
}
