export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;

  const userId = process.env.AUTONOMOUS_USER_ID;
  if (!userId) {
    console.warn("[Engine] AUTONOMOUS_USER_ID not set — auto-scan disabled");
    return;
  }

  // Lazy import so Next.js doesn't pull this into edge bundles
  const { runAutonomousEngine } = await import("@/lib/autonomous-engine");
  const { nyTimeString, isMarketHours } = await import("@/lib/market-data");

  const runEngine = async () => {
    try {
      const result = await runAutonomousEngine(userId, false);
      if (result.skipped === "Market closed (NY time)") {
        // Quiet log so you know it's alive and waiting
        console.log(`[Engine] ${nyTimeString()} — market closed, waiting for 9:30 AM ET`);
        return;
      }
      if (result.skipped) {
        console.log(`[Engine] ${nyTimeString()} — skipped: ${result.skipped}`);
        return;
      }
      console.log(
        `[Engine] ${nyTimeString()} — MARKET OPEN | ` +
        `scanned ${result.signalsFound} signal${result.signalsFound !== 1 ? "s" : ""} across all strategies | ` +
        `executed: ${result.signalsRouted}`
      );
    } catch (err) {
      console.error("[Engine] run error:", err);
    }
  };

  // Wait 8s for Next.js server + Convex client to be ready, then start loop
  setTimeout(() => {
    console.log(`[Engine] Auto-scan started for user ${userId}`);
    runEngine(); // immediate first run
    setInterval(runEngine, 5 * 60 * 1000); // every 5 minutes
  }, 8000);
}
