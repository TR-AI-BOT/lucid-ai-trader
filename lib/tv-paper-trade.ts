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

  // Click the symbol button in the top toolbar (it has the symbol text like "MNQ1!" and sits at y<20)
  const clickResult = await evaluate(`
    (function() {
      const btn = Array.from(document.querySelectorAll('button')).find(b => {
        const r = b.getBoundingClientRect();
        const text = b.textContent?.trim() ?? '';
        return r.y > 0 && r.y < 20 && r.x > 0 && r.x < 200 && text.length > 1 && /[A-Z!]/.test(text);
      });
      if (!btn) return 'no-btn';
      btn.click();
      return 'clicked';
    })()
  `);

  if (clickResult !== "clicked") return false;
  await sleep(800);

  // Find the symbol search input (placeholder: "Symbol, ISIN, or CUSIP")
  const typeResult = await evaluate(`
    (function(sym) {
      const input = Array.from(document.querySelectorAll('input')).find(i =>
        (i.placeholder || '').includes('Symbol') || document.activeElement === i
      ) || Array.from(document.querySelectorAll('input')).find(i => {
        const r = i.getBoundingClientRect();
        return r.y > 50 && r.y < 300 && r.width > 100;
      });
      if (!input) return 'no-input';
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
      const input = Array.from(document.querySelectorAll('input')).find(i =>
        (i.placeholder || '').includes('Symbol') || document.activeElement === i
      );
      if (input) {
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
        return 'enter';
      }
      const row = document.querySelector('[class*="listItem"], [class*="result-row"], [class*="search-result"]');
      if (row) { row.click(); return 'clicked-result'; }
      return 'no-target';
    })()
  `);

  await sleep(1500); // wait for chart + order panel to update to new symbol
  return true;
}

function getOrderPanel(): string {
  return `(document.querySelector('[data-name="order-panel"]') || document.querySelector('[class*="order-panel"]') || document.querySelector('[class*="orderPanel"]'))`;
}

// Enable the TP or SL toggle in the order panel (tries label-based lookup then falls back to index)
async function enableTpSlToggle(type: "tp" | "sl"): Promise<void> {
  const labelText = type === "tp" ? "take profit" : "stop loss";
  const fallbackIdx = type === "tp" ? 0 : 1;
  await evaluate(`
    (function(labelText, fallbackIdx) {
      const panel = ${getOrderPanel()};
      if (!panel) return;
      // Label-based: find the toggle that's near the TP/SL label
      const allEls = Array.from(panel.querySelectorAll('*'));
      const labelEl = allEls.find(el =>
        el.childElementCount <= 2 &&
        (el.textContent || '').toLowerCase().includes(labelText)
      );
      const container = labelEl
        ? (labelEl.closest('[class*="exit"]') || labelEl.closest('[class*="tp"]') || labelEl.closest('[class*="sl"]') || labelEl.parentElement?.parentElement || labelEl.parentElement)
        : null;
      const toggle = container
        ? (container.querySelector('input[type="checkbox"]') || container.querySelector('[role="switch"]') || container.querySelector('[role="checkbox"]'))
        : null;
      if (toggle) {
        const on = toggle instanceof HTMLInputElement ? toggle.checked : toggle.getAttribute('aria-checked') === 'true';
        if (!on) toggle.click();
        return;
      }
      // Fallback: by index
      const cbs = Array.from(panel.querySelectorAll('input[type="checkbox"]'));
      const cb = cbs[fallbackIdx];
      if (cb && !cb.checked) cb.click();
    })('${labelText}', ${fallbackIdx})
  `);
  await sleep(200);
}

// Set TP or SL price value in the order panel (tries label-based lookup then falls back to index)
async function setTpSlValue(type: "tp" | "sl", value: number): Promise<void> {
  const labelText = type === "tp" ? "take profit" : "stop loss";
  const fallbackIdx = type === "tp" ? 2 : 3;
  await evaluate(`
    (function(labelText, fallbackIdx, val) {
      const panel = ${getOrderPanel()};
      if (!panel) return;
      const allEls = Array.from(panel.querySelectorAll('*'));
      const labelEl = allEls.find(el =>
        el.childElementCount <= 2 &&
        (el.textContent || '').toLowerCase().includes(labelText)
      );
      const container = labelEl
        ? (labelEl.closest('[class*="exit"]') || labelEl.closest('[class*="tp"]') || labelEl.closest('[class*="sl"]') || labelEl.parentElement?.parentElement || labelEl.parentElement)
        : null;
      const inputs = container
        ? Array.from(container.querySelectorAll('input[type="number"], input:not([type="checkbox"]):not([type="button"])'))
        : [];
      const input = inputs.length > 0 ? inputs[inputs.length - 1] as HTMLInputElement
        : (Array.from(panel.querySelectorAll('input:not([type="checkbox"])')) as HTMLInputElement[])[fallbackIdx];
      if (!input) return;
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
      if (setter) setter.call(input, String(val));
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true }));
    })('${labelText}', ${fallbackIdx}, ${value})
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
      await enableTpSlToggle("tp");
      await sleep(300);
      await setTpSlValue("tp", Math.round(options.takeProfit * 100) / 100);
    }

    // Step 4: Set Stop Loss if provided
    if (options.stopLoss && options.stopLoss > 0) {
      await enableTpSlToggle("sl");
      await sleep(300);
      await setTpSlValue("sl", Math.round(options.stopLoss * 100) / 100);
    }

    await sleep(200);

    // Step 5: Click place order — try multiple known button selectors/text patterns
    const orderResult = await evaluate(`
      (function() {
        // TradingView has used different data-name/text for this button over time
        const candidates = [
          document.querySelector('[data-name="place-and-modify-button"]'),
          document.querySelector('[data-name="order-submit-button"]'),
          document.querySelector('[data-name="place-order-button"]'),
          // Fallback: find any visible button in the order panel whose text mentions Buy/Sell/Place/Confirm
          ...Array.from(document.querySelectorAll('[data-name="order-panel"] button, [class*="order-panel"] button, [class*="orderPanel"] button')).filter(b => {
            const t = (b.textContent || '').toLowerCase();
            return t.includes('buy') || t.includes('sell') || t.includes('place') || t.includes('confirm') || t.includes('order');
          }),
        ].filter(Boolean);
        if (!candidates.length) return 'not-found';
        const btn = candidates[0];
        const label = btn.textContent?.trim().slice(0, 60) ?? '';
        btn.click();
        return label || 'placed';
      })()
    `);

    if (orderResult === "not-found") {
      return { ok: false, message: "Place order button not found — open Trade → Paper Trading in TradingView and ensure the order panel is visible" };
    }

    const tpStr = options.takeProfit ? ` | TP: ${options.takeProfit.toFixed(2)}` : "";
    const slStr = options.stopLoss ? ` | SL: ${options.stopLoss.toFixed(2)}` : "";
    return { ok: true, message: `[TV Paper] ${side} ${symbol}${tpStr}${slStr}` };

  } catch (err) {
    return { ok: false, message: `TV Paper Trading error: ${String(err)}` };
  }
}

// Returns text content of TradingView's paper trading positions panel.
// Returns null if CDP is unavailable (caller should skip sync).
// Returns empty string if panel found but no positions visible.
export async function getPositionsPanelText(): Promise<string | null> {
  try {
    const result = await evaluate(`
      (function() {
        // Try to activate the Positions tab in the bottom panel
        const tabs = Array.from(document.querySelectorAll('[role="tab"], [class*="tab-"]'));
        const posTab = tabs.find(t => /position/i.test(t.textContent || ''));
        if (posTab) { posTab.click(); }

        // Collect text from the bottom panel (paper trading area)
        const selectors = [
          '[class*="bottom-widgetbar"]',
          '[class*="bottomWidgetbar"]',
          '[id="bottom-area"]',
          '[class*="layout__area--bottom"]',
          '[data-name="trading-panel"]',
          '[class*="trading-panel"]',
          '[class*="tradingPanel"]',
        ];
        for (const sel of selectors) {
          const el = document.querySelector(sel);
          if (el) return el.textContent?.trim() || '';
        }
        // Fallback: look for any visible panel that mentions "Position"
        const allDivs = Array.from(document.querySelectorAll('div'));
        const posDiv = allDivs.find(d =>
          d.children.length > 2 &&
          /position/i.test(d.textContent || '') &&
          d.getBoundingClientRect().height > 50
        );
        return posDiv?.textContent?.trim() || '';
      })()
    `);
    return typeof result === "string" ? result : null;
  } catch {
    return null;
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
