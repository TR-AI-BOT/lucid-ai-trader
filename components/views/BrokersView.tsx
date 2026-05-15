"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { FlaskConical, RefreshCw, Power, TvMinimal, Eye, EyeOff, CheckCircle, AlertCircle, Zap } from "lucide-react";
import { useCurrentUserId } from "@/hooks/useCurrentUserId";

interface PaperStatus {
  connected: boolean;
  balance: number;
  startingBalance: number;
  positions: { symbol: string; qty: number; side: string; entryPrice: number; currentPnl: number }[];
}

export function BrokersView() {
  const userId = useCurrentUserId();
  const [paper, setPaper] = useState<PaperStatus | null>(null);
  const [balanceInput, setBalanceInput] = useState("");
  const [loading, setLoading] = useState<string | null>(null);

  // TradingView
  const [tvEmail, setTvEmail] = useState("");
  const [tvPassword, setTvPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [tvLoading, setTvLoading] = useState(false);
  const [tvError, setTvError] = useState("");
  const [isGoogleAccount, setIsGoogleAccount] = useState(false);
  const [tvUsername, setTvUsername] = useState("");

  // TradeLocker
  const [tlEmail, setTlEmail] = useState("");
  const [tlPassword, setTlPassword] = useState("");
  const [tlServer, setTlServer] = useState("");
  const [tlConnected, setTlConnected] = useState(false);
  const [tlLoading, setTlLoading] = useState(false);
  const [tlError, setTlError] = useState("");

  const tvSettings = useQuery(api.userSettings.get, userId ? { userId } : "skip");
  const convexAccount = useQuery(api.accounts.getActive, userId ? { userId } : "skip");
  const setTradingView = useMutation(api.userSettings.setTradingView);
  const disconnectTradingView = useMutation(api.userSettings.disconnectTradingView);

  const tvConnected = tvSettings?.tvConnected ?? false;

  async function fetchPaper() {
    const data = await fetch("/api/brokers/paper").then((r) => r.json()).catch(() => null);
    if (data) {
      setPaper(data);
      setBalanceInput(String(data.startingBalance));
    }
  }

  useEffect(() => { fetchPaper(); }, []);

  async function paperAction(action: string, body?: Record<string, unknown>) {
    setLoading(action);
    if (action === "connect" && userId) {
      await fetch(`/api/setup?userId=${userId}`).catch(() => null);
    }
    await fetch(`/api/brokers/paper?action=${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    });
    await fetchPaper();
    setLoading(null);
  }

  async function connectTradingView() {
    if (!tvEmail || !userId) return;
    if (!isGoogleAccount && !tvPassword) return;
    setTvLoading(true);
    setTvError("");

    if (!isGoogleAccount) {
      const res = await fetch("/api/tradingview/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: tvEmail, password: tvPassword }),
      }).then((r) => r.json()).catch(() => ({ ok: false, error: "Network error" }));

      if (res.googleAccount) {
        // Connect immediately — use whatever username TV returned (may be null)
        await setTradingView({
          userId,
          tvEmail,
          tvPassword: "google-oauth",
          tvUsername: res.username ?? undefined,
        });
        setTvPassword("");
        setTvLoading(false);
        return;
      }

      if (!res.ok) {
        setTvError(res.error ?? "Invalid credentials");
        setTvLoading(false);
        return;
      }

      if (res.username) setTvUsername(res.username);
    }

    await setTradingView({
      userId,
      tvEmail,
      tvPassword,
      tvUsername: tvUsername || undefined,
    });
    setTvPassword("");
    setTvLoading(false);
  }

  async function connectTradeLocker() {
    if (!tlEmail || !tlPassword || !tlServer) return;
    setTlLoading(true);
    setTlError("");
    const res = await fetch("/api/brokers/tradelocker?action=connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: tlEmail, password: tlPassword, server: tlServer }),
    }).then((r) => r.json()).catch(() => ({ ok: false, message: "Network error" }));
    if (res.ok) {
      setTlConnected(true);
      setTlPassword("");
    } else {
      setTlError(res.message ?? "Connection failed");
    }
    setTlLoading(false);
  }

  function disconnectTradeLocker() {
    fetch("/api/brokers/tradelocker?action=disconnect", { method: "POST", body: JSON.stringify({}) });
    setTlConnected(false);
    setTlEmail("");
    setTlServer("");
  }

  async function disconnectTV() {
    if (!userId) return;
    setTvLoading(true);
    await disconnectTradingView({ userId });
    setTvLoading(false);
  }

  const pnl = paper ? paper.balance - paper.startingBalance : 0;

  return (
    <div className="space-y-4 max-w-2xl">
      <h2 className="text-lg font-semibold">Trading Accounts</h2>

      {/* TradingView Account */}
      <div className="glass rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <TvMinimal className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <p className="font-medium text-sm">TradingView</p>
              <p className="text-xs text-muted-foreground">Connect your account for market data & signals</p>
            </div>
          </div>
          <Badge variant="outline" className={cn("text-xs", tvConnected
            ? "text-buy border-buy/30 bg-buy/10"
            : "text-muted-foreground border-border")}>
            {tvConnected ? "Connected" : "Not Connected"}
          </Badge>
        </div>

        {tvConnected ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 bg-buy/10 border border-buy/20 rounded-xl px-4 py-3">
              <CheckCircle className="w-4 h-4 text-buy shrink-0" />
              <div>
                <p className="text-sm font-medium text-buy">Account Connected</p>
                {tvSettings?.tvUsername && (
                  <p className="text-xs font-semibold text-foreground">@{tvSettings.tvUsername}</p>
                )}
                <p className="text-xs text-muted-foreground">{tvSettings?.tvEmail}</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="w-full border-sell/30 text-sell hover:bg-sell/10"
              onClick={disconnectTV}
              disabled={tvLoading}
            >
              {tvLoading ? "Disconnecting…" : "Disconnect TradingView"}
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">TradingView Email</label>
              <input
                type="email"
                value={tvEmail}
                onChange={(e) => { setTvEmail(e.target.value); setTvError(""); }}
                placeholder="you@email.com"
                className="w-full bg-input border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            {!isGoogleAccount && (
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">TradingView Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={tvPassword}
                    onChange={(e) => { setTvPassword(e.target.value); setTvError(""); }}
                    placeholder="••••••••"
                    className={cn(
                      "w-full bg-input border rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-1 focus:ring-ring",
                      tvError ? "border-sell" : "border-border"
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            )}

            {isGoogleAccount && (
              <div className="flex items-center gap-2 text-blue-400 text-xs bg-blue-500/10 border border-blue-500/20 rounded-lg px-3 py-2">
                <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                Google account detected — click Connect to link your account.
              </div>
            )}

            {tvError && (
              <div className="flex items-center gap-2 text-sell text-xs bg-sell/10 border border-sell/20 rounded-lg px-3 py-2">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                {tvError}
              </div>
            )}

            <Button
              className="w-full"
              onClick={connectTradingView}
              disabled={tvLoading || !tvEmail || (!isGoogleAccount && !tvPassword)}
            >
              {tvLoading ? "Verifying…" : "Connect TradingView Account"}
            </Button>
            <p className="text-xs text-muted-foreground text-center">
              Credentials are verified with TradingView and stored securely for market data access.
            </p>
          </div>
        )}
      </div>

      {/* TradeLocker */}
      <div className="glass rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <Zap className="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <p className="font-medium text-sm">TradeLocker</p>
              <p className="text-xs text-muted-foreground">Connect your TradeLocker account for live trading</p>
            </div>
          </div>
          <Badge variant="outline" className={cn("text-xs", tlConnected
            ? "text-buy border-buy/30 bg-buy/10"
            : "text-muted-foreground border-border")}>
            {tlConnected ? "Connected" : "Not Connected"}
          </Badge>
        </div>

        {tlConnected ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 bg-buy/10 border border-buy/20 rounded-xl px-4 py-3">
              <CheckCircle className="w-4 h-4 text-buy shrink-0" />
              <div>
                <p className="text-sm font-medium text-buy">TradeLocker Connected</p>
                <p className="text-xs text-muted-foreground">{tlEmail} — {tlServer}</p>
              </div>
            </div>
            <Button variant="outline" size="sm" className="w-full border-sell/30 text-sell hover:bg-sell/10"
              onClick={disconnectTradeLocker}>
              Disconnect TradeLocker
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Email</label>
              <input type="email" value={tlEmail} onChange={(e) => { setTlEmail(e.target.value); setTlError(""); }}
                placeholder="your@email.com"
                className="w-full bg-input border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring" />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Password</label>
              <input type="password" value={tlPassword} onChange={(e) => { setTlPassword(e.target.value); setTlError(""); }}
                placeholder="••••••••"
                className="w-full bg-input border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring" />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Server</label>
              <input type="text" value={tlServer} onChange={(e) => { setTlServer(e.target.value); setTlError(""); }}
                placeholder="e.g. OSP-DEMO or OSP-LIVE"
                className="w-full bg-input border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring" />
              <p className="text-xs text-muted-foreground">Find your server name in TradeLocker → Settings</p>
            </div>
            {tlError && (
              <div className="flex items-center gap-2 text-sell text-xs bg-sell/10 border border-sell/20 rounded-lg px-3 py-2">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                {tlError}
              </div>
            )}
            <Button className="w-full" onClick={connectTradeLocker}
              disabled={tlLoading || !tlEmail || !tlPassword || !tlServer}>
              {tlLoading ? "Connecting…" : "Connect TradeLocker"}
            </Button>
          </div>
        )}
      </div>

      {/* Paper Trading */}
      <div className="glass rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center">
              <FlaskConical className="w-4 h-4 text-orange-400" />
            </div>
            <div>
              <p className="font-medium text-sm">Paper Trading</p>
              <p className="text-xs text-muted-foreground">Simulated account — no real money</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline"
              className={cn("text-xs", paper?.connected
                ? "text-buy border-buy/30 bg-buy/10"
                : "text-muted-foreground border-border")}>
              {paper?.connected ? "Active" : "Inactive"}
            </Badge>
            <Button
              size="sm"
              variant={paper?.connected ? "secondary" : "default"}
              className="gap-1.5 h-7 px-2.5 text-xs"
              onClick={() => paperAction(paper?.connected ? "disconnect" : "connect")}
              disabled={loading !== null}
            >
              <Power className="w-3 h-3" />
              {paper?.connected ? "Disconnect" : "Connect"}
            </Button>
          </div>
        </div>

        {/* Account Details from Convex */}
        {convexAccount && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              ["Type", convexAccount.accountType],
              ["Broker", convexAccount.broker],
              ["Risk Mode", convexAccount.riskMode],
              ["Trading Mode", convexAccount.tradingMode],
              ["Daily Loss Limit", `$${convexAccount.dailyLossLimit.toLocaleString()}`],
              ["Max Drawdown", `${convexAccount.maxDrawdownPct}%`],
              ["Max Contracts", convexAccount.maxContracts],
            ].map(([label, value]) => (
              <div key={String(label)} className="bg-white/3 rounded-lg px-3 py-2">
                <p className="text-muted-foreground">{label}</p>
                <p className="font-medium mt-0.5">{value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Balance Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white/3 rounded-xl p-3">
            <p className="text-xs text-muted-foreground">Balance</p>
            <p className="text-base font-bold tabular-nums">${(paper?.balance ?? convexAccount?.currentBalance ?? 50000).toLocaleString()}</p>
          </div>
          <div className="bg-white/3 rounded-xl p-3">
            <p className="text-xs text-muted-foreground">Starting</p>
            <p className="text-base font-bold tabular-nums">${(paper?.startingBalance ?? convexAccount?.startingBalance ?? 50000).toLocaleString()}</p>
          </div>
          <div className="bg-white/3 rounded-xl p-3">
            <p className="text-xs text-muted-foreground">P&L</p>
            <p className={cn("text-base font-bold tabular-nums", pnl >= 0 ? "text-buy" : "text-sell")}>
              {pnl >= 0 ? "+" : ""}${pnl.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Set Balance */}
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">Set account balance</label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">$</span>
              <input
                type="number"
                value={balanceInput}
                onChange={(e) => setBalanceInput(e.target.value)}
                className="w-full bg-input border border-border rounded-lg pl-7 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                placeholder="50000"
                min={1000}
              />
            </div>
            <Button
              size="sm"
              onClick={() => paperAction("set-balance", { balance: Number(balanceInput) })}
              disabled={loading !== null || !balanceInput || Number(balanceInput) <= 0}
            >
              Set Balance
            </Button>
          </div>
        </div>

        {/* Open Positions */}
        {(paper?.positions ?? []).length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs text-muted-foreground">Open Positions</p>
            <div className="space-y-1">
              {paper!.positions.map((p) => (
                <div key={p.symbol} className="flex items-center justify-between bg-white/3 rounded-lg px-3 py-2 text-xs">
                  <span className="font-medium">{p.symbol}</span>
                  <span className={cn("font-medium", p.side === "Long" ? "text-buy" : "text-sell")}>{p.side}</span>
                  <span className="text-muted-foreground">Qty {p.qty}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reset */}
        <Button
          variant="outline"
          size="sm"
          className="w-full gap-2 border-sell/30 text-sell hover:bg-sell/10"
          onClick={() => paperAction("reset")}
          disabled={loading !== null}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {loading === "reset" ? "Resetting…" : "Reset Account"}
        </Button>
      </div>
    </div>
  );
}
