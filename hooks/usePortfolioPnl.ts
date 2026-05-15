"use client";

import { useState, useEffect } from "react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { useCurrentUserId } from "./useCurrentUserId";

const ACCOUNT_KEY = "lucid_tv_account_cache";
const ACCOUNT_TTL = 20_000; // 20s — refresh often so P&L stays live

type TVAccount = {
  balance: number;
  equity: number;
  realizedPnl: number;
  unrealizedPnl: number;
  availableFunds: number;
};

type AccountCache = TVAccount & { ts: number };

function readStorage(key: string, ttl: number): AccountCache | null {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AccountCache;
    if (Date.now() - parsed.ts > ttl) return null;
    return parsed;
  } catch { return null; }
}

function writeStorage(key: string, data: object) {
  try { sessionStorage.setItem(key, JSON.stringify({ ...data, ts: Date.now() })); } catch {}
}

let accountCache: AccountCache | null = readStorage(ACCOUNT_KEY, ACCOUNT_TTL);
let accountInflight: Promise<TVAccount | null> | null = null;

async function fetchTVAccount(): Promise<TVAccount | null> {
  if (accountCache && Date.now() - accountCache.ts < ACCOUNT_TTL) return accountCache;
  if (accountInflight) return accountInflight;
  accountInflight = fetch("/api/tv/account")
    .then(r => r.json())
    .then((data: TVAccount & { error?: string }) => {
      if (data.error || data.balance === undefined) return null;
      const result: TVAccount = {
        balance: data.balance,
        equity: data.equity,
        realizedPnl: data.realizedPnl,
        unrealizedPnl: data.unrealizedPnl,
        availableFunds: data.availableFunds,
      };
      accountCache = { ...result, ts: Date.now() };
      writeStorage(ACCOUNT_KEY, result);
      return result;
    })
    .catch(() => null)
    .finally(() => { accountInflight = null; });
  return accountInflight;
}

export function usePortfolioPnl(dateRange = "today") {
  const userId = useCurrentUserId();
  const pnlStats   = useQuery(api.trades.getPnlStats, userId ? { userId, dateRange } : "skip");
  const openTrades = useQuery(api.trades.list,        userId ? { userId, status: "open" } : "skip");

  const cached = readStorage(ACCOUNT_KEY, ACCOUNT_TTL);
  const [tvAccount, setTvAccount] = useState<TVAccount | null>(cached ?? accountCache ?? null);

  useEffect(() => {
    fetchTVAccount().then(a => { if (a) setTvAccount(a); });
    // Refresh every 20s so P&L stays current
    const interval = setInterval(() => {
      accountCache = null; // force re-fetch
      fetchTVAccount().then(a => { if (a) setTvAccount(a); });
    }, ACCOUNT_TTL);
    return () => clearInterval(interval);
  }, []);

  const totalPnl = (tvAccount?.realizedPnl ?? 0) + (tvAccount?.unrealizedPnl ?? 0);

  return {
    pnlStats,
    openTrades: openTrades ?? [],
    tvAccount,
    tvBalance: tvAccount?.balance ?? null,
    tvRealizedPnl: tvAccount?.realizedPnl ?? null,
    tvUnrealizedPnl: tvAccount?.unrealizedPnl ?? null,
    tvEquity: tvAccount?.equity ?? null,
    totalPnl,
    openCount: openTrades?.length ?? 0,
    // Keep these for backward compat with Convex-based stats
    unrealized: tvAccount?.unrealizedPnl ?? 0,
    prices: {} as Record<string, number>,
  };
}
