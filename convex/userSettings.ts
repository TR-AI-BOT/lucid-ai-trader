import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const get = query({
  args: { userId: v.string() },
  handler: async (ctx, { userId }) => {
    return await ctx.db
      .query("userSettings")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .first();
  },
});

export const setTradingView = mutation({
  args: {
    userId: v.string(),
    tvEmail: v.string(),
    tvPassword: v.string(),
    tvUsername: v.optional(v.string()),
  },
  handler: async (ctx, { userId, tvEmail, tvPassword, tvUsername }) => {
    const existing = await ctx.db
      .query("userSettings")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, { tvEmail, tvPassword, tvUsername, tvConnected: true });
    } else {
      await ctx.db.insert("userSettings", { userId, tvEmail, tvPassword, tvUsername, tvConnected: true });
    }
  },
});

export const setTradeLockerCreds = mutation({
  args: {
    userId: v.string(),
    tlEmail: v.string(),
    tlPassword: v.string(),
    tlServer: v.string(),
    tlApiUrl: v.optional(v.string()),
  },
  handler: async (ctx, { userId, tlEmail, tlPassword, tlServer, tlApiUrl }) => {
    const existing = await ctx.db
      .query("userSettings")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, { tlEmail, tlPassword, tlServer, tlApiUrl, tlConnected: true });
    } else {
      await ctx.db.insert("userSettings", { userId, tlEmail, tlPassword, tlServer, tlApiUrl, tlConnected: true });
    }
  },
});

export const disconnectTradingView = mutation({
  args: { userId: v.string() },
  handler: async (ctx, { userId }) => {
    const existing = await ctx.db
      .query("userSettings")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, { tvEmail: undefined, tvPassword: undefined, tvConnected: false });
    }
  },
});
