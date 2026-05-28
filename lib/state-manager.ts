import type { TradingSignal, Account, TradingMode } from "./types";
import { checkTradeAllowed } from "./risk-manager";
import * as brokerRegistry from "./broker-registry";
import * as telegram from "./telegram";

export interface SignalRouteResult {
  action: "executed" | "pending_approval" | "signal_only" | "filtered";
  reason: string;
  orderId?: string;
}

export async function routeSignal(
  signal: TradingSignal,
  account: Account,
  mode: TradingMode,
  dailyTradeCount: number,
  signalId: string,
  positionSide?: "Long" | "Short"
): Promise<SignalRouteResult> {
  // CLOSE always bypasses risk/mode gates — never block a position close
  let qty = parseInt(process.env.ORDER_QTY ?? "1", 10);

  if (signal.action !== "CLOSE") {
    // Risk gate (only for entry signals)
    const risk = checkTradeAllowed(account, signal, dailyTradeCount, account.peakBalance ?? account.startingBalance);
    if (!risk.allowed) {
      if (risk.haltLevel >= 2) {
        await telegram.sendRiskAlert(risk.haltLevel, risk.reason);
      }
      return { action: "filtered", reason: risk.reason };
    }
    qty = Math.min(qty, risk.maxContracts);
  }

  if (mode === "SIGNALS_ONLY") {
    await telegram.sendMessage(
      `📡 <b>Signal (No Execution)</b>\n${signal.action} ${signal.symbol} @ ${signal.price}\n${signal.reason}`
    );
    return { action: "signal_only", reason: "SIGNALS_ONLY mode" };
  }

  if (mode === "SEMI_AUTO") {
    await telegram.sendMessage(`⏳ Awaiting approval for ${signal.action} ${signal.symbol}…`);
    const approved = await telegram.sendSignalApproval(signalId, signal);
    if (!approved) {
      return { action: "filtered", reason: "Rejected in SEMI_AUTO mode" };
    }
  }

  // Execute
  const brokerAction: "Buy" | "Sell" = signal.action === "BUY" ? "Buy" : "Sell";

  if (signal.action === "CLOSE") {
    const result = await brokerRegistry.closePosition(signal.symbol, positionSide);
    if (!result.ok) return { action: "filtered", reason: result.message };
    await telegram.sendTradeAlert("CLOSE", signal.symbol, qty, signal.price);
    return { action: "executed", reason: result.message, orderId: result.orderId };
  }

  const result = await brokerRegistry.placeOrder(signal.symbol, qty, brokerAction, {
    stopLoss: signal.stopLoss,
    takeProfit: signal.takeProfit,
  });
  if (!result.ok) {
    return { action: "filtered", reason: result.message };
  }
  await telegram.sendTradeAlert(signal.action, signal.symbol, qty, signal.price, signal.stopLoss, signal.takeProfit);
  return { action: "executed", reason: result.message, orderId: result.orderId };
}
