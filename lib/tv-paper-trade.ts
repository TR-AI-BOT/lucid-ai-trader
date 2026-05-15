import type { OrderResult } from "./types";

const CDP_PORT = Number(process.env.TV_CDP_PORT ?? 9222);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _client: any = null;

async function getClient() {
  if (_client) {
    try {
      await _client.Runtime.evaluate({ expression: "1", returnByValue: true });
      return _client;
    } catch {
      _client = null;
    }
  }
  const listRes = await fetch(`http://localhost:${CDP_PORT}/json/list`).catch(() => null);
  if (!listRes?.ok) throw new Error(`TradingView Desktop not found on port ${CDP_PORT}`);
  const targets = (await listRes.json()) as Array<{ type: string; url: string; id: string }>;
  const target = targets.find(t => t.type === "page" && /tradingview/i.test(t.url));
  if (!target) throw new Error("No TradingView chart page found");
  const CDP = (await import("chrome-remote-interface")).default;
  _client = await CDP({ host: "localhost", port: CDP_PORT, target: target.id });
  await _client.Runtime.enable();
  return _client;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function evaluate(expression: string): Promise<any> {
  const c = await getClient();
  const result = await c.Runtime.evaluate({ expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text ?? "JS error");
  }
  return result.result?.value;
}

function sleep(ms: number) { return new Promise<void>(r => setTimeout(r, ms)); }

// Switch TradingView chart to the given symbol before trading
async function switchToSymbol(symbol: string): Promise<boolean> {
  // Map our symbols to TradingView search terms
  const TV_SYMBOL_MAP: Record<string, string> = {
    "MES1!":  "MES1!",
    "MNQ1!":  "MNQ1!",
    "ES1!":   "ES1!",
    "NQ1!":   "NQ1!",
    "MYM1!":  "MYM1!",
    "M2K1!":  "M2K1!",
    "NAS100": "OANDA:NAS100USD",
    "NAS100.R": "NAS100",
    "SPX500.R": "SPX500USD",
    "US30.R": "US30USD",
    "BTCUSD": "BTCUSD",
    "ETHUSD": "ETHUSD",
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "USDJPY": "USDJPY",
    "USDCHF": "USDCHF",
    "AUDUSD": "AUDUSD",
    "NZDUSD": "NZDUSD",
    "USDCAD": "USDCAD",
    "EURGBP": "EURGBP",
    "EURJPY": "EURJPY",
    "GBPJPY": "GBPJPY",
  };
  const searchTerm = TV_SYMBOL_MAP[symbol] ?? symbol;

  // Click the symbol button in the header to open search
  const clickResult = await evaluate(`
    (function() {
      // Find the symbol label button in the top bar (leftmost button, small y)
      const btns = Array.from(document.querySelectorAll('button')).filter(b => {
        const r = b.getBoundingClientRect();
        return r.x < 250 && r.y < 60 && r.width > 30;
      });
      if (!btns.length) return 'no-btn';
      btns[0].click();
      return 'clicked';
    })()
  `);

  if (clickResult !== "clicked") return false;
  await sleep(600);

  // Find the search input and set the symbol
  const typeResult = await evaluate(`
    (function(sym) {
      const input = document.querySelector('input[data-role="search"]')
        || document.querySelector('[class*="SearchInput"] input')
        || document.querySelector('[class*="search-input"] input')
        || Array.from(document.querySelectorAll('input')).find(i => {
          const r = i.getBoundingClientRect();
          return r.y < 200 && r.width > 100 && document.activeElement === i;
        })
        || Array.from(document.querySelectorAll('input')).find(i => {
          const r = i.getBoundingClientRect();
          return r.y < 200 && r.width > 100;
        });
      if (!input) return 'no-input';
      // Use React's native setter to trigger change events
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
      if (setter) setter.call(input, sym);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      return 'typed:' + sym;
    })('${searchTerm}')
  `);

  if (!typeResult?.startsWith("typed")) return false;
  await sleep(1200); // wait for search results

  // Press Enter to select the first result
  await evaluate(`
    (function() {
      const input = document.querySelector('input[data-role="search"]')
        || Array.from(document.querySelectorAll('input')).find(i => {
          const r = i.getBoundingClientRect();
          return r.y < 200 && r.width > 100;
        });
      if (input) {
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
        return 'enter';
      }
      // Click first search result
      const row = document.querySelector('[class*="listItem"], [class*="result-row"], [class*="search-result"]');
      if (row) { row.click(); return 'clicked-result'; }
      return 'no-target';
    })()
  `);

  await sleep(1500); // wait for chart + order panel to update to new symbol
  return true;
}

// Enable a TP or SL checkbox if not already checked
async function enableCheckbox(index: number): Promise<void> {
  await evaluate(`
    (function(idx) {
      const panel = document.querySelector('[data-name="order-panel"]');
      if (!panel) return;
      const checkboxes = Array.from(panel.querySelectorAll('input[type="checkbox"]'));
      const cb = checkboxes[idx];
      if (cb && !cb.checked) {
        cb.click();
      }
    })(${index})
  `);
  await sleep(200);
}

// Set a numeric input in the order panel by index (0=qty, 1=TP price, 2=SL price)
async function setOrderPanelValue(inputIndex: number, value: number): Promise<void> {
  await evaluate(`
    (function(idx, val) {
      const panel = document.querySelector('[data-name="order-panel"]');
      if (!panel) return;
      const inputs = Array.from(panel.querySelectorAll('input:not([type="checkbox"])'));
      const input = inputs[idx];
      if (!input) return;
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
      if (setter) setter.call(input, String(val));
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true }));
    })(${inputIndex}, ${value})
  `);
  await sleep(150);
}

export interface TVOrderOptions {
  stopLoss?: number;
  takeProfit?: number;
}

export async function placeTVPaperOrder(
  symbol: string,
  side: "Buy" | "Sell",
  options: TVOrderOptions = {}
): Promise<OrderResult> {
  try {
    // Step 1: Switch chart to the correct symbol
    const switched = await switchToSymbol(symbol);
    if (!switched) {
      return { ok: false, message: `Could not switch TradingView chart to ${symbol}` };
    }

    // Step 2: Select Buy or Sell side
    const sideAttr = side === "Buy" ? "buy" : "sell";
    const sideResult = await evaluate(`
      (function() {
        const el = document.querySelector('[data-name="side-control-${sideAttr}"]');
        if (!el) return 'not-found';
        el.click();
        return 'ok';
      })()
    `);
    if (sideResult !== "ok") {
      return { ok: false, message: "Order panel not visible — open Trade → Paper Trading in TradingView" };
    }
    await sleep(250);

    // Step 3: Set Take Profit if provided
    if (options.takeProfit && options.takeProfit > 0) {
      await enableCheckbox(0); // TP checkbox is index 0
      await sleep(300);
      await setOrderPanelValue(1, Math.round(options.takeProfit * 100) / 100); // TP price is input index 1
    }

    // Step 4: Set Stop Loss if provided
    if (options.stopLoss && options.stopLoss > 0) {
      await enableCheckbox(1); // SL checkbox is index 1
      await sleep(300);
      await setOrderPanelValue(2, Math.round(options.stopLoss * 100) / 100); // SL price is input index 2
    }

    await sleep(200);

    // Step 5: Click place order
    const orderResult = await evaluate(`
      (function() {
        const btn = document.querySelector('[data-name="place-and-modify-button"]');
        if (!btn) return 'not-found';
        const label = btn.textContent?.trim().slice(0, 60) ?? '';
        btn.click();
        return label || 'placed';
      })()
    `);

    if (orderResult === "not-found") {
      return { ok: false, message: "Place order button not found" };
    }

    const tpStr = options.takeProfit ? ` | TP: ${options.takeProfit.toFixed(2)}` : "";
    const slStr = options.stopLoss ? ` | SL: ${options.stopLoss.toFixed(2)}` : "";
    return { ok: true, message: `[TV Paper] ${side} ${symbol}${tpStr}${slStr}` };

  } catch (err) {
    return { ok: false, message: `TV Paper Trading error: ${String(err)}` };
  }
}

export async function isAvailable(): Promise<boolean> {
  if (process.env.TV_PAPER_ENABLED !== "true") return false;
  try { await getClient(); return true; } catch { return false; }
}

export function disconnect(): void {
  if (_client) {
    try { _client.close(); } catch {}
    _client = null;
  }
}
