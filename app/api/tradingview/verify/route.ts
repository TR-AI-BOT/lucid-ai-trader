import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { email, password } = await req.json();
  if (!email || !password) return NextResponse.json({ ok: false, error: "Missing credentials" }, { status: 400 });

  try {
    const res = await fetch("https://www.tradingview.com/accounts/signin/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.tradingview.com/",
        "Origin": "https://www.tradingview.com",
      },
      body: new URLSearchParams({ username: email, password, remember_me: "on" }).toString(),
    });

    const data = await res.json().catch(() => null);

    // TradingView returns { user: {...} } on success, or { error: "..." } on failure
    if (data?.user?.id || data?.sessionid) {
      const username = data?.user?.username ?? null;
      return NextResponse.json({ ok: true, username });
    }

    const errorMsg: string = data?.error ?? data?.message ?? "Invalid email or password";

    // Google-linked accounts — TradingView sometimes includes username in error response
    if (errorMsg.toLowerCase().includes("google") || errorMsg.toLowerCase().includes("social")) {
      const username = data?.username ?? data?.user?.username ?? null;
      return NextResponse.json({ ok: true, googleAccount: true, username });
    }

    return NextResponse.json({ ok: false, error: errorMsg });
  } catch {
    return NextResponse.json({ ok: false, error: "Could not reach TradingView" }, { status: 502 });
  }
}
