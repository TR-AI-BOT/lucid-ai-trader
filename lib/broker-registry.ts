import type { OrderResult, Position, BrokerStatus } from "./types";
import * as tradovate from "./tradovate";
import * as tradelocker from "./tradelocker";
import * as tvPaper from "./tv-paper-trade";
import type { TVOrderOptions } from "./tv-paper-trade";

// ── Paper Broker (in-memory) ──────────────────────────────────────────────────
class PaperBroker {
  private startingBalance = 100_000;
  private balance = 100_000;
  private connected = true;
  private positions = new Map<string, { qty: number; side: "Long" | "Short"; entryPrice: number }>();

  connect() { this.connected = true; }
  disconnect() { this.connected = false; }
  isConnected() { return this.connected; }
  getStartingBalance() { return this.startingBalance; }

  setBalance(amount: number) {
    this.startingBalance = amount;
    this.balance = amount;
    this.positions.clear();
  }

  reset() {
    this.balance = this.startingBalance;
    this.positions.clear();
  }

  async placeOrder(symbol: string, qty: number, action: "Buy" | "Sell"): Promise<OrderResult> {
    this.positions.set(symbol, {
      qty,
      side: action === "Buy" ? "Long" : "Short",
      entryPrice: 0,
    });
    return { ok: true, message: `[PAPER] ${action} ${qty} ${symbol}` };
  }

  async closePosition(symbol: string): Promise<OrderResult> {
    this.positions.delete(symbol);
    return { ok: true, message: `[PAPER] Closed ${symbol}` };
  }

  async getBalance(): Promise<number> { return this.balance; }

  async getPositions(): Promise<Position[]> {
    return Array.from(this.positions.entries()).map(([symbol, p]) => ({
      symbol,
      qty: p.qty,
      side: p.side,
      entryPrice: p.entryPrice,
      currentPnl: 0,
    }));
  }
}

// ── Tradovate Broker ──────────────────────────────────────────────────────────
class TradovateBroker {
  private connected = false;

  async connect(creds: { username: string; password: string; clientId: string; clientSecret: string }): Promise<{ ok: boolean; message: string }> {
    try {
      await tradovate.getAccessToken();
      this.connected = true;
      return { ok: true, message: "Connected to Tradovate" };
    } catch (err) {
      return { ok: false, message: String(err) };
    }
  }

  isConnected(): boolean { return this.connected; }

  async placeOrder(symbol: string, qty: number, action: "Buy" | "Sell"): Promise<OrderResult> {
    return tradovate.placeOrder(symbol, qty, action);
  }

  async closePosition(symbol: string): Promise<OrderResult> {
    const positions = await tradovate.getPositions();
    const pos = positions.find((p) => p.symbol === symbol);
    if (!pos) return { ok: false, message: `No open position for ${symbol}` };
    return tradovate.liquidatePosition(0);
  }

  async getBalance(): Promise<number> { return tradovate.getAccountBalance(); }
  async getPositions(): Promise<Position[]> { return tradovate.getPositions(); }

  disconnect(): void {
    this.connected = false;
    tradovate.clearToken();
  }
}

// ── TradeLocker Broker ────────────────────────────────────────────────────────
class TradeLockerBroker {
  private connected = false;

  async connect(creds: { email: string; password: string; server: string; apiUrl?: string }): Promise<{ ok: boolean; message: string }> {
    try {
      process.env.TRADELOCKER_EMAIL = creds.email;
      process.env.TRADELOCKER_PASSWORD = creds.password;
      process.env.TRADELOCKER_SERVER = creds.server;
      if (creds.apiUrl) process.env.TRADELOCKER_API_URL = creds.apiUrl;
      await tradelocker.getAccessToken();
      this.connected = true;
      return { ok: true, message: "Connected to TradeLocker" };
    } catch (err) {
      return { ok: false, message: String(err) };
    }
  }

  isConnected(): boolean { return this.connected; }
  async placeOrder(symbol: string, qty: number, action: "Buy" | "Sell"): Promise<OrderResult> { return tradelocker.placeOrder(symbol, qty, action); }
  async getBalance(): Promise<number> { return tradelocker.getAccountBalance(); }
  async getPositions(): Promise<Position[]> { return tradelocker.getPositions(); }
  disconnect(): void { this.connected = false; tradelocker.clearToken(); }
}

// ── Registry Singleton ─────────────────────────────────────────────────────────
type BrokerName = "paper" | "tradovate" | "tradelocker" | "tv-paper";

const paper = new PaperBroker();
const tradovateBroker = new TradovateBroker();
const tradelockerBroker = new TradeLockerBroker();

// Auto-detect from env so the correct broker is active after every server restart
let activeBroker: BrokerName = (() => {
  if (process.env.TV_PAPER_ENABLED === "true") return "tv-paper";
  if (process.env.TRADELOCKER_EMAIL) return "tradelocker";
  if (process.env.TRADOVATE_USERNAME) return "tradovate";
  return "paper";
})();

export async function listAll(): Promise<BrokerStatus[]> {
  return [
    {
      name: "paper",
      connected: paper.isConnected(),
      balance: await paper.getBalance(),
      positions: await paper.getPositions(),
      connectionFields: [],
    },
    {
      name: "tradovate",
      connected: tradovateBroker.isConnected(),
      connectionFields: [
        { key: "username", label: "Username", type: "text", required: true },
        { key: "password", label: "Password", type: "password", required: true },
        { key: "clientId", label: "Client ID", type: "text", required: true },
        { key: "clientSecret", label: "Client Secret", type: "password", required: true },
      ],
    },
    {
      name: "tradelocker",
      connected: tradelockerBroker.isConnected(),
      connectionFields: [
        { key: "email", label: "Email", type: "text", required: true },
        { key: "password", label: "Password", type: "password", required: true },
        { key: "server", label: "Server", type: "text", required: true, placeholder: "e.g. OSP-DEMO or OSP-LIVE" },
        { key: "apiUrl", label: "API URL (optional)", type: "text", required: false, placeholder: "https://demo.tradelocker.com/backend-service" },
      ],
    },
  ];
}

export function getActiveName(): BrokerName { return activeBroker; }

export function connectPaper() { paper.connect(); activeBroker = "paper"; }
export function disconnectPaper() { paper.disconnect(); if (activeBroker === "paper") activeBroker = "paper"; }
export function setPaperBalance(amount: number) { paper.setBalance(amount); }
export function resetPaper() { paper.reset(); }
export async function getPaperStatus() {
  return {
    connected: paper.isConnected(),
    balance: await paper.getBalance(),
    startingBalance: paper.getStartingBalance(),
    positions: await paper.getPositions(),
  };
}

export async function connect(
  name: BrokerName,
  creds: Record<string, string>
): Promise<{ ok: boolean; message: string }> {
  if (name === "tradovate") {
    const result = await tradovateBroker.connect(creds as Parameters<typeof tradovateBroker.connect>[0]);
    if (result.ok) activeBroker = "tradovate";
    return result;
  }
  if (name === "tradelocker") {
    const result = await tradelockerBroker.connect(creds as Parameters<typeof tradelockerBroker.connect>[0]);
    if (result.ok) activeBroker = "tradelocker";
    return result;
  }
  return { ok: false, message: `Unknown broker: ${name}` };
}

export function switchTo(name: BrokerName): void {
  activeBroker = name;
}

export function disconnect(name: BrokerName): void {
  if (name === "tradovate") tradovateBroker.disconnect();
  if (name === "tradelocker") tradelockerBroker.disconnect();
  if (activeBroker === name) activeBroker = "paper";
}

export async function placeOrder(
  symbol: string,
  qty: number,
  action: "Buy" | "Sell",
  options: TVOrderOptions = {}
): Promise<OrderResult> {
  if (activeBroker === "tv-paper") return tvPaper.placeTVPaperOrder(symbol, action, options);
  if (process.env.PAPER_MODE === "true") return paper.placeOrder(symbol, qty, action);
  if (activeBroker === "tradovate") return tradovateBroker.placeOrder(symbol, qty, action);
  if (activeBroker === "tradelocker") return tradelockerBroker.placeOrder(symbol, qty, action);
  return paper.placeOrder(symbol, qty, action);
}

export async function closePosition(symbol: string): Promise<OrderResult> {
  if (activeBroker === "tv-paper") return tvPaper.placeTVPaperOrder(symbol, "Sell");
  if (process.env.PAPER_MODE === "true") return paper.closePosition(symbol);
  if (activeBroker === "tradovate") return tradovateBroker.closePosition(symbol);
  if (activeBroker === "tradelocker") return tradelockerBroker.placeOrder(symbol, 0, "Sell");
  return paper.closePosition(symbol);
}

export async function getActiveStatus(): Promise<{ name: string; balance: number; positions: Position[] }> {
  if (activeBroker === "tv-paper") {
    return { name: "tv-paper", balance: 0, positions: [] };
  }
  const broker =
    activeBroker === "tradovate" ? tradovateBroker :
    activeBroker === "tradelocker" ? tradelockerBroker :
    paper;
  return {
    name: activeBroker,
    balance: await broker.getBalance(),
    positions: await broker.getPositions(),
  };
}
