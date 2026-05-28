import { NextRequest, NextResponse } from "next/server";
import { fetchLiveCandles } from "@/lib/market-data";

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") ?? "MNQ1!";
  const interval = req.nextUrl.searchParams.get("interval") ?? "15m";

  try {
    const candles = await fetchLiveCandles(symbol, interval);
    return NextResponse.json({ candles });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ candles: [], error: message });
  }
}
