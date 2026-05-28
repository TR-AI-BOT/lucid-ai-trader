import type { OrderResult, Position } from "./types";

interface TLToken {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

interface TLAccount {
  id: number;
  accNum: string;
  name: string;
  currency: string;
  balance: number;
}

let _token: TLToken | null = null;
let _account: TLAccount | null = null;

function baseUrl() {
  return process.env.TRADELOCKER_API_URL ?? "https://demo.tradelocker.com/backend-api";
}

async function request<T>(
  path: string,
  method: "GET" | "POST" | "DELETE" = "GET",
  body?: unknown,
  extraHeaders?: Record<string, string>
): Promise<T> {
  const token = await getAccessToken();
  const account = await getAccount();
  const res = await fetch(`${baseUrl()}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "accNum": account.accNum,
      ...extraHeaders,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`TradeLocker ${method} ${path} → ${res.status}: ${await res.text()}`);
  const json = await res.json() as { s?: string; d?: T } & T;
  // Handle both { s, d } and direct response formats
  return (json.s === "ok" ? json.d : json) as T;
}

export async function getAccessToken(): Promise<string> {
  if (_token && Date.now() < _token.expiresAt - 60_000) return _token.accessToken;

  const res = await fetch(`${baseUrl()}/auth/jwt/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: process.env.TRADELOCKER_EMAIL,
      password: process.env.TRADELOCKER_PASSWORD,
      server: process.env.TRADELOCKER_SERVER ?? "OSP-DEMO",
    }),
  });

  if (!res.ok) throw new Error(`TradeLocker auth failed: ${res.status} ${await res.text()}`);
  const json = await res.json() as Record<string, unknown>;

  // Handle both response formats: direct tokens (GatesFX) or wrapped { s, d } (standard)
  const data = (json.s === "ok" ? json.d : json) as Record<string, unknown>;
  const accessToken = data.accessToken as string;
  const refreshToken = data.refreshToken as string;
  if (!accessToken) throw new Error(`TradeLocker auth error: ${JSON.stringify(json)}`);

  const expiresAt = data.expireDate
    ? new Date(data.expireDate as string).getTime()
    : Date.now() + ((data.expiration as number) ?? 900) * 1000;

  _token = { accessToken, refreshToken, expiresAt };
  _account = null; // reset account on new token
  return _token.accessToken;
}

export async function getAccount(): Promise<TLAccount> {
  if (_account) return _account;
  if (!_token) await getAccessToken(); // auto-auth on first call
  const token = _token?.accessToken;
  if (!token) throw new Error("Not authenticated");

  const res = await fetch(`${baseUrl()}/auth/jwt/all-accounts`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`TradeLocker accounts failed: ${res.status}`);
  const json = await res.json() as Record<string, unknown>;
  // Handle both { s, d: { accounts } } and direct { accounts } formats
  const payload = (json.s === "ok" ? json.d : json) as Record<string, unknown>;
  const accounts: TLAccount[] = (payload?.accounts ?? json?.accounts ?? []) as TLAccount[];
  if (!accounts.length) throw new Error("No TradeLocker accounts found");
  _account = accounts[0];
  return _account;
}

const SYMBOL_MAP: Record<string, string> = {
  "MNQ1!": "NAS100.R", "NQ1!": "NAS100.R",
  "MES1!": "SPX500.R", "ES1!": "SPX500.R",
  "MYM1!": "US30.R",   "YM1!": "US30.R",
  "RTY1!": "US2000",   "M2K1!": "US2000",
  "GC1!":  "XAUUSD",   "MGC1!": "XAUUSD",
  "CL1!":  "USOIL",    "MCL1!": "USOIL",
  "BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD",
  "EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "USDJPY": "USDJPY",
  // GatesFX uses exact .R suffix — pass through directly
  "NAS100.R": "NAS100.R", "SPX500.R": "SPX500.R", "US30.R": "US30.R",
};

interface TLInstrument {
  tradableInstrumentId: number;
  id: number;
  name: string;
  routes?: Array<{ id: number; type: string }>;
}

async function findInstrument(symbol: string): Promise<{ tradableInstrumentId: number; routeId: number }> {
  const tlSymbol = SYMBOL_MAP[symbol] ?? symbol;
  const account = await getAccount();
  const token = _token!.accessToken;
  const headers = { Authorization: `Bearer ${token}`, "accNum": account.accNum };

  const iRes = await fetch(`${baseUrl()}/trade/accounts/${account.id}/instruments?locale=en`, { headers });
  if (!iRes.ok) throw new Error(`TL instruments failed: ${iRes.status}`);
  const iJson = await iRes.json() as { d: { instruments: TLInstrument[] } };
  const instruments = iJson.d?.instruments ?? [];

  // Exact match first, then partial
  const inst =
    instruments.find(i => i.name.toUpperCase() === tlSymbol.toUpperCase()) ??
    instruments.find(i => i.name.toUpperCase().includes(tlSymbol.toUpperCase()));
  if (!inst) throw new Error(`TL: instrument not found for ${symbol} (tried "${tlSymbol}")`);

  // Routes are embedded in the instrument — pick the TRADE route
  const tradeRoute = inst.routes?.find(r => r.type === "TRADE") ?? inst.routes?.[0];
  if (!tradeRoute) throw new Error(`TL: no TRADE route found for ${symbol}`);

  return { tradableInstrumentId: inst.tradableInstrumentId, routeId: tradeRoute.id };
}

export async function placeOrder(symbol: string, qty: number, action: "Buy" | "Sell"): Promise<OrderResult> {
  try {
    const account = await getAccount();
    const { tradableInstrumentId, routeId } = await findInstrument(symbol);
    console.log(`[TL] placing order: instrumentId=${tradableInstrumentId} routeId=${routeId} side=${action.toLowerCase()} qty=${qty}`);
    const token = await getAccessToken();
    const res = await fetch(`${baseUrl()}/trade/accounts/${account.id}/orders`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "accNum": account.accNum,
      },
      body: JSON.stringify({
        tradableInstrumentId,
        routeId,
        type: "market",
        side: action.toLowerCase(),
        qty,
        validity: "IOC", // GatesFX only accepts IOC for market orders
      }),
    });
    const rawText = await res.text();
    console.log(`[TL] order response ${res.status}:`, rawText);
    if (!res.ok) return { ok: false, message: `TradeLocker ${res.status}: ${rawText}` };
    const json = JSON.parse(rawText) as { s?: string; d?: unknown; message?: string };
    if (json.s !== "ok") {
      return { ok: false, message: `TL raw: ${rawText}` };
    }
    return { ok: true, message: `[TradeLocker] ${action} ${qty} ${symbol} (instrument ${tradableInstrumentId})` };
  } catch (err) {
    return { ok: false, message: String(err) };
  }
}

export async function getPositions(): Promise<Position[]> {
  try {
    const account = await getAccount();
    const data = await request<{ positions: Array<{ id: number; tradableInstrumentId: number; side: string; qty: number; avgPrice: number; pnl: number; name?: string }> }>(
      `/trade/accounts/${account.id}/positions`
    );
    return (data.positions ?? []).map((p) => ({
      symbol: p.name ?? String(p.tradableInstrumentId),
      qty: p.qty,
      side: p.side === "buy" ? ("Long" as const) : ("Short" as const),
      entryPrice: p.avgPrice,
      currentPnl: p.pnl ?? 0,
    }));
  } catch {
    return [];
  }
}

export async function closePositionBySymbol(symbol: string): Promise<OrderResult> {
  try {
    const account = await getAccount();
    const tlSymbol = SYMBOL_MAP[symbol] ?? symbol;
    const data = await request<{ positions: Array<{ id: number; name?: string; tradableInstrumentId: number }> }>(
      `/trade/accounts/${account.id}/positions`
    );
    const pos = (data.positions ?? []).find(
      (p) => (p.name ?? "").toUpperCase() === tlSymbol.toUpperCase()
    );
    if (!pos) return { ok: false, message: `No open position for ${symbol}` };
    return closePosition(pos.id);
  } catch (err) {
    return { ok: false, message: String(err) };
  }
}

export async function getAccountBalance(): Promise<number> {
  try {
    const account = await getAccount();
    return account.balance;
  } catch {
    return 0;
  }
}

export async function closePosition(positionId: number): Promise<OrderResult> {
  try {
    const account = await getAccount();
    await request(`/trade/accounts/${account.id}/positions/${positionId}`, "DELETE");
    return { ok: true, message: "Position closed" };
  } catch (err) {
    return { ok: false, message: String(err) };
  }
}

export function clearToken(): void {
  _token = null;
  _account = null;
}
