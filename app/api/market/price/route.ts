import { NextRequest, NextResponse } from "next/server";
import { YF_SYMBOL_MAP } from "@/lib/market-data";

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol");
  if (!symbol) return NextResponse.json({ error: "symbol required" }, { status: 400 });

  const yfSymbol = YF_SYMBOL_MAP[symbol] ?? symbol;
  const now = Math.floor(Date.now() / 1000);
  const period1 = now - 3600; // last 1 hour

  try {
    const res = await fetch(
      `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(yfSymbol)}?period1=${period1}&period2=${now}&interval=1m&events=history`,
      {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
          "Accept": "application/json",
        },
        next: { revalidate: 0 },
      }
    );
    const json = await res.json();
    const result = json?.chart?.result?.[0];
    const closes: number[] = result?.indicators?.quote?.[0]?.close ?? [];
    const price = closes.filter(Boolean).at(-1) ?? 0;
    return NextResponse.json({ symbol, price });
  } catch {
    return NextResponse.json({ symbol, price: 0 });
  }
}
