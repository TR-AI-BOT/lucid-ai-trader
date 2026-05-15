import { NextResponse } from "next/server";
import { ConvexHttpClient } from "convex/browser";
import { api } from "@/convex/_generated/api";
import * as brokerRegistry from "@/lib/broker-registry";
import { ensureBrokerReady } from "@/lib/broker-init";
import { getAccessToken, getAccount } from "@/lib/tradelocker";

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);
const BASE = process.env.TRADELOCKER_API_URL ?? "https://demo.tradelocker.com/backend-api";

export async function GET() {
  const userId = process.env.AUTONOMOUS_USER_ID ?? "";
  const beforeBroker = brokerRegistry.getActiveName();

  await ensureBrokerReady(userId);

  const afterBroker = brokerRegistry.getActiveName();
  const settings = await convex.query(api.userSettings.get, { userId }).catch(() => null);

  // Try to list instruments to see how GatesFX names them
  let instruments: string[] = [];
  let instrumentError = null;
  let rawInstrumentSample: unknown = null;
  let accountInfo: unknown = null;
  try {
    const token = await getAccessToken();
    const account = await getAccount();
    accountInfo = { id: account.id, accNum: account.accNum, name: account.name };

    const headers2 = { Authorization: `Bearer ${token}`, "accNum": account.accNum };

    // Full NAS100.R instrument object — show every field
    const iRes = await fetch(`${BASE}/trade/accounts/${account.id}/instruments?locale=en`, { headers: headers2 });
    const iJson = await iRes.json() as { d: { instruments: Array<Record<string, unknown>> } };
    const insts = iJson.d?.instruments ?? [];
    const nas = insts.find(i => String(i.name).includes("NAS100"));
    instruments = [
      `NAS100.R full object: ${JSON.stringify(nas)}`,
    ];

    // Try orders history to find a routeId that was used before
    const oRes = await fetch(`${BASE}/trade/accounts/${account.id}/ordersHistory?limit=5`, { headers: headers2 });
    const oText = await oRes.text();
    rawInstrumentSample = `ordersHistory ${oRes.status}: ${oText.slice(0, 600)}`;
  } catch (err) {
    instrumentError = String(err);
  }

  return NextResponse.json({
    PAPER_MODE: process.env.PAPER_MODE,
    activeBroker_before: beforeBroker,
    activeBroker_after: afterBroker,
    convex_tlConnected: settings?.tlConnected ?? null,
    convex_tlEmail: settings?.tlEmail ? "***saved***" : "not saved",
    convex_tlServer: settings?.tlServer ?? null,
    instruments,
    instrumentError,
    rawInstrumentSample,
    accountInfo,
  });
}
