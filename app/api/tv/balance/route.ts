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
        // Walk all text nodes to find "Account balance" label
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) {
          if (node.textContent && node.textContent.trim() === 'Account balance') {
            // Walk up to find a container, then look for the sibling value element
            let el = node.parentElement;
            for (let i = 0; i < 4; i++) {
              if (!el) break;
              const next = el.nextElementSibling;
              if (next) {
                const text = next.textContent?.trim() ?? '';
                const num = parseFloat(text.replace(/,/g, '').replace('USD', ''));
                if (!isNaN(num) && num >= 0) return num;
              }
              // Also try children of parent
              const parent = el.parentElement;
              if (parent) {
                const children = Array.from(parent.children);
                const idx = children.indexOf(el);
                if (idx !== -1 && children[idx + 1]) {
                  const text = children[idx + 1].textContent?.trim() ?? '';
                  const num = parseFloat(text.replace(/,/g, '').replace('USD', ''));
                  if (!isNaN(num) && num >= 0) return num;
                }
              }
              el = el.parentElement;
            }
          }
        }
        // Fallback: find all numeric USD-like values and return the first positive one
        const spans = Array.from(document.querySelectorAll('span, div'));
        for (const el of spans) {
          if (el.children.length > 0) continue;
          const text = el.textContent?.trim() ?? '';
          if (/^\\d[\\d,]*\\.\\d{2}(USD)?$/.test(text)) {
            const num = parseFloat(text.replace(/,/g, '').replace('USD', ''));
            if (num > 0) return num;
          }
        }
        return null;
      })()`,
      returnByValue: true,
    });

    await client.close();

    const balance: number | null = result.value;
    if (balance === null || balance === undefined) throw new Error("Balance not found in DOM");

    return NextResponse.json({ balance }, { headers: { "Cache-Control": "no-store" } });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 503 });
  }
}
