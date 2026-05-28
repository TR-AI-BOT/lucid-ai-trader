import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const list = query({
  args: { userId: v.string(), limit: v.optional(v.number()) },
  handler: async (ctx, { userId, limit }) => {
    const q = ctx.db
      .query("signals")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .order("desc");
    return limit ? await q.take(limit) : await q.collect();
  },
});

export const add = mutation({
  args: {
    userId: v.string(),
    symbol: v.string(),
    action: v.union(v.literal("BUY"), v.literal("SELL"), v.literal("CLOSE")),
    price: v.number(),
    timeframe: v.string(),
    reason: v.string(),
    strategy: v.optional(v.string()),
    confidence: v.optional(v.number()),
    stopLoss: v.optional(v.number()),
    takeProfit: v.optional(v.number()),
    status: v.union(
      v.literal("pending"),
      v.literal("approved"),
      v.literal("rejected"),
      v.literal("executed"),
      v.literal("filtered")
    ),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("signals", { ...args, receivedAt: Date.now() });
  },
});

export const getPending = query({
  args: { userId: v.string() },
  handler: async (ctx, { userId }) => {
    return await ctx.db
      .query("signals")
      .withIndex("by_user_status", (q) =>
        q.eq("userId", userId).eq("status", "pending")
      )
      .order("desc")
      .first();
  },
});

export const updateStatus = mutation({
  args: {
    signalId: v.id("signals"),
    status: v.union(
      v.literal("approved"),
      v.literal("rejected"),
      v.literal("executed"),
      v.literal("filtered")
    ),
  },
  handler: async (ctx, { signalId, status }) => {
    await ctx.db.patch(signalId, { status });
  },
});

export const deleteAll = mutation({
  args: { userId: v.string() },
  handler: async (ctx, { userId }) => {
    const signals = await ctx.db
      .query("signals")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const signal of signals) await ctx.db.delete(signal._id);
    return signals.length;
  },
});

export const getPerformance = query({
  args: { userId: v.string() },
  handler: async (ctx, { userId }) => {
    // Today's midnight in New York time — handles EST (-5) and EDT (-4) automatically
    const nowUtc = Date.now();
    const nyDateStr = new Date(nowUtc).toLocaleDateString("en-US", {
      timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit",
    }); // "MM/DD/YYYY"
    const [m, d, y] = nyDateStr.split("/");
    const localMidnight = new Date(`${y}-${m}-${d}T00:00:00`);
    const nyOffset = new Date(localMidnight.toLocaleString("en-US", { timeZone: "America/New_York" })).getTime() - localMidnight.getTime();
    const nyMidnightUtc = localMidnight.getTime() - nyOffset;
    const signals = await ctx.db
      .query("signals")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .filter((q) => q.gte(q.field("receivedAt"), nyMidnightUtc))
      .collect();
    const executed = signals.filter((s) => s.status === "executed").length;
    return {
      buy: signals.filter((s) => s.action === "BUY").length,
      sell: signals.filter((s) => s.action === "SELL").length,
      close: signals.filter((s) => s.action === "CLOSE").length,
      filtered: signals.filter((s) => s.status === "filtered").length,
      executed,
      total: signals.length,
    };
  },
});
