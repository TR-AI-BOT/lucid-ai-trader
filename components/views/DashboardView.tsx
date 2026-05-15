"use client";

import { useQuery, useMutation } from "convex/react";
import { useCurrentUserId } from "@/hooks/useCurrentUserId";
import { usePortfolioPnl } from "@/hooks/usePortfolioPnl";
import { api } from "@/convex/_generated/api";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Activity, Send, CheckCircle2, XCircle, Clock, Bell, RotateCcw, Scan } from "lucide-react";

function PnlCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="glass rounded-2xl p-4 flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={cn("text-2xl font-bold tabular-nums", color)}>{value}</span>
    </div>
  );
}

function PendingApprovalBanner({
  userId,
}: {
  userId: string;
}) {
  const pendingSignal = useQuery(api.signals.getPending, userId ? { userId } : "skip");
  const updateStatus = useMutation(api.signals.updateStatus);
  const [countdown, setCountdown] = useState(90);

  useEffect(() => {
    if (!pendingSignal) return;
    setCountdown(90);
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          updateStatus({ signalId: pendingSignal._id, status: "rejected" });
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingSignal?._id]);

  if (!pendingSignal) return null;

  return (
    <div className="glass border border-accent/40 rounded-2xl p-4 flex items-center gap-4 animate-pulse-subtle">
      <div className="flex items-center gap-2 text-accent flex-none">
        <Clock className="w-5 h-5" />
        <span className="text-2xl font-bold tabular-nums w-8">{countdown}</span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold">Trade approval required</p>
        <p className="text-xs text-muted-foreground truncate">
          <span className={cn("font-medium", pendingSignal.action === "BUY" ? "text-buy" : "text-sell")}>
            {pendingSignal.action}
          </span>{" "}
          {pendingSignal.symbol} — {pendingSignal.reason}
        </p>
      </div>
      <div className="flex gap-2 flex-none">
        <Button
          size="sm"
          className="gap-1.5 bg-buy hover:bg-buy/90 text-white"
          onClick={() => updateStatus({ signalId: pendingSignal._id, status: "approved" })}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Approve
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5 border-sell/40 text-sell hover:bg-sell/10"
          onClick={() => updateStatus({ signalId: pendingSignal._id, status: "rejected" })}
        >
          <XCircle className="w-3.5 h-3.5" />
          Decline
        </Button>
      </div>
    </div>
  );
}

export function DashboardView() {
  const userId = useCurrentUserId();
  const signals = useQuery(api.signals.list, userId ? { userId, limit: 20 } : "skip");
  const state = useQuery(api.tradingState.get, userId ? { userId } : "skip");
  const { pnlStats: pnl, totalPnl, openCount, tvBalance, tvRealizedPnl, tvUnrealizedPnl } = usePortfolioPnl("today");
  const [symbol, setSymbol] = useState("MES1!");
  const [action, setAction] = useState<"BUY" | "SELL" | "CLOSE">("BUY");
  const [manualReason, setManualReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [tradeMsg, setTradeMsg] = useState("");
  const [resetting, setResetting] = useState(false);
  const [resetMsg, setResetMsg] = useState("");
  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState("");

  // Auto-scan every 5 minutes while the page is open (backup for server-side instrumentation)
  useEffect(() => {
    if (!userId) return;
    const run = () => fetch(`/api/engine/run?userId=${userId}`).catch(() => {});
    // Delay first auto-run by 30s so it doesn't overlap with server-side startup scan
    const initial = setTimeout(run, 30_000);
    const interval = setInterval(run, 5 * 60 * 1000);
    return () => { clearTimeout(initial); clearInterval(interval); };
  }, [userId]);

  async function forceScan() {
    setScanning(true);
    setScanMsg("");
    try {
      const res = await fetch(`/api/engine/run?userId=${userId}&force=true`);
      const data = await res.json();
      if (data.ok) {
        setScanMsg(
          data.signalsFound > 0
            ? `✓ ${data.signalsFound} signal${data.signalsFound !== 1 ? "s" : ""} found, ${data.signalsRouted} executed`
            : "✓ Scan complete — no setups found right now"
        );
      } else {
        setScanMsg("✗ " + (data.error ?? data.skipped ?? "Unknown error"));
      }
    } catch (e) {
      setScanMsg("✗ " + String(e));
    } finally {
      setScanning(false);
    }
  }

  async function resetAccount() {
    if (!confirm("Reset all trades, signals, and set balance to $10,000? This cannot be undone.")) return;
    setResetting(true);
    setResetMsg("");
    try {
      const res = await fetch("/api/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, balance: 10000 }),
      });
      const data = await res.json();
      setResetMsg(data.ok ? "✓ " + data.message : "✗ " + data.message);
    } catch (e) {
      setResetMsg("✗ " + String(e));
    } finally {
      setResetting(false);
    }
  }

  async function submitManual() {
    setSubmitting(true);
    setTradeMsg("");
    try {
      const res = await fetch("/api/trade/manual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, symbol, action, reason: manualReason }),
      });
      const data = await res.json();
      setTradeMsg(data.ok ? "✓ " + data.message : "✗ " + data.message);
      if (data.ok) setManualReason("");
    } catch (e) {
      setTradeMsg("✗ " + String(e));
    } finally {
      setSubmitting(false);
    }
  }

  const modeLabel = {
    FULL_AUTO: "Auto Trading",
    SEMI_AUTO: "Pre-Approval",
    SIGNALS_ONLY: "Manual",
  }[state?.mode ?? "FULL_AUTO"];

  const modeDescription = {
    FULL_AUTO: "Bot enters trades automatically",
    SEMI_AUTO: "Bot asks you 90s before each trade",
    SIGNALS_ONLY: "Signals shown — you enter trades yourself",
  }[state?.mode ?? "FULL_AUTO"];

  return (
    <div className="space-y-4">
      {/* Pre-approval banner */}
      {state?.mode === "SEMI_AUTO" && <PendingApprovalBanner userId={userId} />}

      {/* Manual mode: latest signal alert */}
      {state?.mode === "SIGNALS_ONLY" && signals && signals.length > 0 && (() => {
        const latest = signals[0];
        const age = Date.now() - latest.receivedAt;
        if (age > 60_000) return null;
        return (
          <div className="glass border border-primary/30 rounded-2xl p-4 flex items-center gap-3">
            <Bell className="w-4 h-4 text-primary flex-none" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold">New signal — enter manually if you agree</p>
              <p className="text-xs text-muted-foreground truncate">
                <span className={cn("font-medium", latest.action === "BUY" ? "text-buy" : "text-sell")}>
                  {latest.action}
                </span>{" "}
                {latest.symbol} — {latest.reason}
              </p>
            </div>
            <span className="text-xs text-muted-foreground flex-none">
              {Math.round(age / 1000)}s ago
            </span>
          </div>
        );
      })()}

      {/* P&L Row — all live from TradingView */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <PnlCard
          label="Realized P&L"
          value={tvRealizedPnl !== null ? `${tvRealizedPnl >= 0 ? "+" : ""}$${tvRealizedPnl.toFixed(2)}` : "—"}
          color={tvRealizedPnl !== null ? (tvRealizedPnl >= 0 ? "text-buy" : "text-sell") : "text-foreground"}
        />
        <PnlCard
          label="Unrealized P&L"
          value={tvUnrealizedPnl !== null ? `${tvUnrealizedPnl >= 0 ? "+" : ""}$${tvUnrealizedPnl.toFixed(2)}` : "—"}
          color={tvUnrealizedPnl !== null ? (tvUnrealizedPnl >= 0 ? "text-buy" : "text-sell") : "text-foreground"}
        />
        <PnlCard
          label="Total P&L"
          value={tvRealizedPnl !== null ? `${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}` : "—"}
          color={totalPnl >= 0 ? "text-buy" : "text-sell"}
        />
        <PnlCard
          label="TV Balance"
          value={tvBalance !== null ? `$${tvBalance.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—"}
          color="text-foreground"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Signals Feed */}
        <div className="lg:col-span-2 glass rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-accent" />
            <h3 className="text-sm font-semibold flex-1">Recent Signals</h3>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5 text-xs h-7 px-2"
              onClick={forceScan}
              disabled={scanning}
            >
              <Scan className={cn("w-3 h-3", scanning && "animate-spin")} />
              {scanning ? "Scanning…" : "Force Scan"}
            </Button>
          </div>
          {scanMsg && (
            <p className={cn("text-xs mb-2 px-1", scanMsg.startsWith("✓") ? "text-buy" : "text-sell")}>
              {scanMsg}
            </p>
          )}
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {(signals ?? []).length === 0 && (
              <div className="text-center py-8">
                <p className="text-xs text-muted-foreground">No signals yet</p>
                <p className="text-xs text-muted-foreground/60 mt-1">Bot scans every 5 min during market hours · 9:30 AM–4:00 PM ET</p>
              </div>
            )}
            {(signals ?? []).map((s) => (
              <div key={s._id} className="flex items-center gap-3 p-2.5 rounded-xl bg-white/3 hover:bg-white/5 transition-colors">
                <Badge
                  variant="outline"
                  className={cn("text-xs border",
                    s.action === "BUY" ? "text-buy border-buy/30 bg-buy/10" :
                    s.action === "SELL" ? "text-sell border-sell/30 bg-sell/10" :
                    "text-close border-close/30 bg-close/10"
                  )}
                >
                  {s.action}
                </Badge>
                <span className="text-sm font-medium">{s.symbol}</span>
                <span className="text-xs text-muted-foreground flex-1 truncate">{s.reason}</span>
                <span className="text-xs text-muted-foreground flex-none">
                  {new Date(s.receivedAt).toLocaleTimeString("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: true })} ET
                </span>
                <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full",
                  s.status === "executed" ? "bg-buy/10 text-buy" :
                  s.status === "pending" ? "bg-accent/10 text-accent" :
                  s.status === "rejected" ? "bg-sell/10 text-sell" :
                  "bg-muted text-muted-foreground"
                )}>
                  {s.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Manual Trade + Mode */}
        <div className="space-y-3">
          <div className="glass rounded-2xl p-4">
            <h3 className="text-sm font-semibold mb-3">Manual Trade</h3>
            <div className="space-y-2">
              <input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="Symbol (MES1!)"
                className="w-full bg-input border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              />
              <div className="grid grid-cols-3 gap-1">
                {(["BUY", "SELL", "CLOSE"] as const).map((a) => (
                  <button
                    key={a}
                    onClick={() => setAction(a)}
                    className={cn("py-1.5 rounded-lg text-xs font-semibold transition-colors",
                      action === a ? (a === "BUY" ? "bg-buy text-white" : a === "SELL" ? "bg-sell text-white" : "bg-close text-white") :
                      "bg-white/5 text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {a}
                  </button>
                ))}
              </div>
              <input
                value={manualReason}
                onChange={(e) => setManualReason(e.target.value)}
                placeholder="Reason (optional)"
                className="w-full bg-input border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              />
              <Button className="w-full gap-2" onClick={submitManual} disabled={submitting}>
                <Send className="w-3.5 h-3.5" />
                {submitting ? "Submitting…" : "Submit"}
              </Button>
              {tradeMsg && (
                <p className={cn("text-xs mt-1 break-all", tradeMsg.startsWith("✓") ? "text-buy" : "text-sell")}>
                  {tradeMsg}
                </p>
              )}
            </div>
          </div>

          <div className="glass rounded-2xl p-4">
            <h3 className="text-sm font-semibold mb-2">Trading Mode</h3>
            <p className="text-sm font-medium text-primary">{modeLabel}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{modeDescription}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {state?.isPaused ? "⏸ Trading paused" : "▶ Trading active"}
            </p>
            <div className="mt-3 pt-3 border-t border-border/50">
              <Button
                size="sm"
                variant="outline"
                className="w-full gap-2 border-sell/30 text-sell hover:bg-sell/10 text-xs"
                onClick={resetAccount}
                disabled={resetting}
              >
                <RotateCcw className="w-3 h-3" />
                {resetting ? "Resetting…" : "Reset Account ($10k)"}
              </Button>
              {resetMsg && (
                <p className={cn("text-xs mt-1.5 break-all", resetMsg.startsWith("✓") ? "text-buy" : "text-sell")}>
                  {resetMsg}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
