import { NextResponse } from "next/server";

const CDP_PORT = Number(process.env.TV_CDP_PORT ?? 9222);

export async function GET() {
  try {
    const listRes = await fetch(`http://localhost:${CDP_PORT}/json/list`, {
      next: { revalidate: 0 },
    });
    if (!listRes.ok) throw new Error("CDP not reachable");

    const targets: { type: string; url: string; webSocketDebuggerUrl?: string }[] =
      await listRes.json();

    const target = targets.find(t => t.type === "page" && t.url.includes("tradingview"));
    if (!target?.webSocketDebuggerUrl) throw new Error("TradingView page not found");

    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const CDP = require("chrome-remote-interface");
    const client = await CDP({ port: CDP_PORT, target: target.webSocketDebuggerUrl });

    const { result } = await client.Runtime.evaluate({
      expression: `(function() {
        const labels = ['Account balance', 'Equity', 'Realized PnL', 'Unrealized PnL', 'Available funds'];
        const data = {};
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) {
          const t = node.textContent?.trim();
          if (!labels.includes(t)) continue;
          let el = node.parentElement;
          for (let i = 0; i < 6; i++) {
            if (!el) break;
            const parent = el.parentElement;
            if (parent) {
              const kids = Array.from(parent.children);
              const idx = kids.indexOf(el);
              for (let j = idx + 1; j < Math.min(idx + 3, kids.length); j++) {
                const raw = kids[j]?.textContent?.trim() ?? '';
                // Handle unicode minus (U+2212) and comma thousands separator
                const cleaned = raw.replace(/\\u2212|\\u2013/g, '-').replace(/,/g, '').replace('USD','').trim();
                if (cleaned !== '' && !isNaN(Number(cleaned))) {
                  data[t] = Number(cleaned);
                  break;
                }
              }
            }
            if (data[t] !== undefined) break;
            el = el.parentElement;
          }
        }
        return data;
      })()`,
      returnByValue: true,
    });

    await client.close();

    const raw = result.value ?? {};
    const balance: number = raw["Account balance"] ?? 0;
    const equity: number = raw["Equity"] ?? balance;
    const realizedPnl: number = raw["Realized PnL"] ?? 0;
    const unrealizedPnl: number = raw["Unrealized PnL"] ?? 0;
    const availableFunds: number = raw["Available funds"] ?? balance;

    if (!balance && balance !== 0) throw new Error("No account data found");

    return NextResponse.json(
      { balance, equity, realizedPnl, unrealizedPnl, availableFunds },
      { headers: { "Cache-Control": "no-store" } }
    );
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 503 });
  }
}
