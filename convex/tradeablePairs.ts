import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const getEnabled = query({
  args: { userId: v.string() },
  handler: async (ctx, { userId }) => {
    const pairs = await ctx.db
      .query("tradeablePairs")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    return pairs.filter((p) => p.enabled).map((p) => p.symbol);
  },
});

export const getAll = query({
  args: { userId: v.string() },
  handler: async (ctx, { userId }) => {
    const pairs = await ctx.db
      .query("tradeablePairs")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    return pairs;
  },
});

export const setEnabled = mutation({
  args: { userId: v.string(), symbol: v.string(), enabled: v.boolean() },
  handler: async (ctx, { userId, symbol, enabled }) => {
    const existing = await ctx.db
      .query("tradeablePairs")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .filter((q) => q.eq(q.field("symbol"), symbol))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, { enabled });
    } else {
      await ctx.db.insert("tradeablePairs", { userId, symbol, enabled });
    }
  },
});

export const setMany = mutation({
  args: { userId: v.string(), symbols: v.array(v.string()), enabled: v.boolean() },
  handler: async (ctx, { userId, symbols, enabled }) => {
    for (const symbol of symbols) {
      const existing = await ctx.db
        .query("tradeablePairs")
        .withIndex("by_user", (q) => q.eq("userId", userId))
        .filter((q) => q.eq(q.field("symbol"), symbol))
        .first();
      if (existing) {
        await ctx.db.patch(existing._id, { enabled });
      } else {
        await ctx.db.insert("tradeablePairs", { userId, symbol, enabled });
      }
    }
  },
});
