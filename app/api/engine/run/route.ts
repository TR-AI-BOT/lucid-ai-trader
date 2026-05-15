import { NextRequest, NextResponse } from "next/server";
import { runAutonomousEngine } from "@/lib/autonomous-engine";
import { ensureBrokerReady } from "@/lib/broker-init";

// Vercel Cron calls this every 5 minutes via GET
// Can also be triggered manually: GET /api/engine/run?userId=<clerk_user_id>
export async function GET(req: NextRequest) {
  // Auth: only allow Vercel cron or requests with the engine secret
  const authHeader = req.headers.get("authorization");
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId =
    req.nextUrl.searchParams.get("userId") ??
    process.env.AUTONOMOUS_USER_ID ??
    "";

  if (!userId) {
    return NextResponse.json(
      { error: "No userId. Set AUTONOMOUS_USER_ID in .env or pass ?userId= in URL." },
      { status: 400 }
    );
  }

  const force = req.nextUrl.searchParams.get("force") === "true";

  try {
    await ensureBrokerReady(userId);
    const result = await runAutonomousEngine(userId, force);
    return NextResponse.json({ ok: true, userId, ...result });
  } catch (err) {
    console.error("[Autonomous Engine]", err);
    return NextResponse.json({ ok: false, error: String(err) }, { status: 500 });
  }
}
