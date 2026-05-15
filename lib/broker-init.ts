import { ConvexHttpClient } from "convex/browser";
import { api } from "@/convex/_generated/api";
import * as brokerRegistry from "./broker-registry";

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

let lastAttempt = 0;

export async function ensureBrokerReady(userId: string): Promise<void> {
  if (brokerRegistry.getActiveName() !== "paper") return; // already on a real broker
  if (process.env.PAPER_MODE === "true") return;

  // Throttle retries to once per 30 seconds
  const now = Date.now();
  if (now - lastAttempt < 30_000) return;
  lastAttempt = now;

  try {
    const settings = await convex.query(api.userSettings.get, { userId });
    console.log("[broker-init] settings from Convex:", JSON.stringify({
      tlConnected: settings?.tlConnected,
      tlEmail: settings?.tlEmail ? "***" : null,
      tlServer: settings?.tlServer,
    }));
    if (settings?.tlConnected && settings.tlEmail && settings.tlPassword && settings.tlServer) {
      const creds: Record<string, string> = {
        email: settings.tlEmail,
        password: settings.tlPassword,
        server: settings.tlServer,
      };
      if (settings.tlApiUrl) creds.apiUrl = settings.tlApiUrl;
      const result = await brokerRegistry.connect("tradelocker", creds);
      console.log("[broker-init] auto-connect result:", result);
    } else {
      console.log("[broker-init] no saved TradeLocker credentials found");
    }
  } catch (err) {
    console.error("[broker-init] auto-connect failed:", err);
  }
}
