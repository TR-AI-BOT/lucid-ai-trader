import { NextResponse } from "next/server";
import { ensureBrokerReady } from "@/lib/broker-init";
import { getAccessToken, getAccount } from "@/lib/tradelocker";

const BASE = process.env.TRADELOCKER_API_URL ?? "https://demo.tradelocker.com/backend-api";
const USER_ID = process.env.AUTONOMOUS_USER_ID ?? "m17ap1ehn4419nyj1e6w93a08986m0pc";

export async function GET() {
  try {
    await ensureBrokerReady(USER_ID);
    const token = await getAccessToken();
    const account = await getAccount();

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "accNum": account.accNum,
    };

    const tradableInstrumentId = 13645;
    const tradeRouteId = 1482858;

    const combos = [
      { type: "market", validity: "FOK" },
      { type: "market", validity: "GTC" },
      { type: "market", validity: "DAY" },
      { type: "market", validity: "IOC" },
      { type: "market", noValidity: true },
      { type: "MARKET", validity: "FOK" },
      { type: "MARKET", validity: "IOC" },
      { type: "market", validity: "FOK", qty: 0.1 },
      { type: "market", validity: "IOC", qty: 0.1 },
    ];

    const results = [];

    for (const combo of combos) {
      const body: Record<string, unknown> = {
        tradableInstrumentId,
        routeId: tradeRouteId,
        side: "buy",
        qty: combo.qty ?? 1,
        type: combo.type,
      };
      if (!combo.noValidity && combo.validity) body.validity = combo.validity;

      const res = await fetch(`${BASE}/trade/accounts/${account.id}/orders`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
      const text = await res.text();
      const label = `type=${combo.type} validity=${combo.validity ?? "none"} qty=${combo.qty ?? 1}`;
      results.push({ label, status: res.status, body: text.slice(0, 150) });

      try {
        const json = JSON.parse(text);
        if (json.s === "ok") return NextResponse.json({ winner: label, results });
      } catch {}
    }

    return NextResponse.json({ winner: null, results });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
