"use client";

import { useQuery } from "convex/react";
import { useCurrentUserId } from "@/hooks/useCurrentUserId";
import { usePortfolioPnl } from "@/hooks/usePortfolioPnl";
import { api } from "@/convex/_generated/api";
import { STRATEGY_REGISTRY } from "@/convex/strategies";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Trophy, Activity } from "lucide-react";

type DateRange = "today" | "week" | "month" | "all";

const DATE_RANGES: { label: string; value: DateRange }[] = [
  { label: "Today", value: "today" },
  { label: "Week", value: "week" },
  { label: "Month", value: "month" },
  { label: "All Time", value: "all" },
];

const STRATEGY_NAMES = Object.fromEntries(STRATEGY_REGISTRY.map(s => [s.id, s.name]));

function fmt(n: number) {
  return `${n >= 0 ? "+" : ""}$${Math.abs(n).toFixed(2)}`;
}

export function PerformanceView() {
  const userId = useCurrentUserId();
  const [dateRange, setDateRange] = useState<DateRange>("week");

  const { pnlStats: pnl, openTrades, tvBalance, tvRealizedPnl, tvUnrealizedPnl, totalPnl } = usePortfolioPnl(dateRange);

  const strategies = useQuery(api.trades.getAllStrategyStats, userId ? { userId, dateRange } : "skip");
  const curve      = useQuery(api.trades.getCumulativePnl,   userId ? { userId, dateRange } : "skip");
  const trades     = useQuery(api.trades.list,               userId ? { userId, limit: 30 } : "skip");

  const best = strategies?.[0];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Performance</h2>
        <div className="flex gap-1">
          {DATE_RANGES.map(({ label, value }) => (
            <button
              key={value}
              onClick={() => setDateRange(value)}
              className={cn("px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                dateRange === value ? "bg-primary text-white" : "bg-white/5 text-muted-foreground hover:text-foreground"
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* TradingView Account — live banner */}
      <div className="glass rounded-xl px-4 py-3 border border-border/50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Balance</p>
            <p className="text-base font-bold tabular-nums text-foreground">
              {tvBalance !== null ? `$${tvBalance.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Realized P&L</p>
            <p className={cn("text-base font-bold tabular-nums", (tvRealizedPnl ?? 0) >= 0 ? "text-buy" : "text-sell")}>
              {tvRealizedPnl !== null ? `${tvRealizedPnl >= 0 ? "+" : ""}$${tvRealizedPnl.toFixed(2)}` : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Unrealized P&L</p>
            <p className={cn("text-base font-bold tabular-nums", (tvUnrealizedPnl ?? 0) >= 0 ? "text-buy" : "text-sell")}>
              {tvUnrealizedPnl !== null ? `${tvUnrealizedPnl >= 0 ? "+" : ""}$${tvUnrealizedPnl.toFixed(2)}` : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total P&L</p>
            <p className={cn("text-base font-bold tabular-nums", totalPnl >= 0 ? "text-buy" : "text-sell")}>
              {tvRealizedPnl !== null ? `${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}` : "—"}
            </p>
          </div>
        </div>
      </div>

      {/* Open positions indicator */}
      {openTrades.length > 0 && (
        <div className="glass rounded-xl px-4 py-2.5 flex items-center gap-3 border border-primary/10">
          <Activity className="w-3.5 h-3.5 text-primary flex-none" />
          <span className="text-xs text-muted-foreground">
            <span className="text-foreground font-medium">{openTrades.length}</span> open position{openTrades.length !== 1 ? "s" : ""} — unrealized P&L updates every 20s from TradingView
          </span>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Win Rate",      value: pnl?.closedTrades ? `${((pnl.winRate) * 100).toFixed(1)}%` : "—", color: (pnl?.winRate ?? 0) >= 0.5 ? "text-buy" : "text-sell" },
          { label: "Profit Factor", value: pnl?.closedTrades ? (pnl.profitFactor >= 999 ? "∞" : pnl.profitFactor.toFixed(2)) : "—", color: (pnl?.profitFactor ?? 0) >= 1.5 ? "text-buy" : "text-sell" },
          { label: "Total Trades",  value: String(pnl?.totalTrades ?? 0), color: "text-foreground" },
          { label: "Open Trades",   value: String(openTrades.length), color: openTrades.length > 0 ? "text-primary" : "text-foreground" },
          { label: "Avg Win",       value: pnl?.avgWin ? `+$${pnl.avgWin.toFixed(2)}` : "—",  color: "text-buy" },
          { label: "Avg Loss",      value: pnl?.avgLoss ? `-$${pnl.avgLoss.toFixed(2)}` : "—", color: "text-sell" },
          { label: "Gross Profit",  value: `+$${(pnl?.grossProfit ?? 0).toFixed(2)}`,           color: "text-buy" },
          { label: "Gross Loss",    value: `-$${(pnl?.grossLoss ?? 0).toFixed(2)}`,             color: "text-sell" },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass rounded-2xl p-4">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className={cn("text-lg font-bold tabular-nums mt-1", color)}>{value}</p>
          </div>
        ))}
      </div>

      {/* Best Strategy Banner */}
      {best && best.totalTrades > 0 && (
        <div className="glass rounded-2xl p-4 flex items-center gap-3 border border-primary/20">
          <Trophy className="w-5 h-5 text-yellow-400 flex-none" />
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground">Top Performing Strategy</p>
            <p className="text-sm font-semibold">{STRATEGY_NAMES[best.strategy] ?? best.strategy}</p>
          </div>
          <div className="text-right flex-none">
            <p className={cn("text-lg font-bold tabular-nums", best.netPnl >= 0 ? "text-buy" : "text-sell")}>{fmt(best.netPnl)}</p>
            <p className="text-xs text-muted-foreground">{(best.winRate * 100).toFixed(0)}% win rate · {best.totalTrades} trades</p>
          </div>
        </div>
      )}

      {/* Cumulative P&L Chart */}
      <div className="glass rounded-2xl p-4">
        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary" />
          Cumulative P&L
        </h3>
        {(() => {
          const base = curve ?? [];
          const lastPnl = base.at(-1)?.pnl ?? 0;
          const unrealized = tvUnrealizedPnl ?? 0;
          const chartData = unrealized !== 0
            ? [...base, { time: Date.now(), pnl: Math.round((lastPnl + unrealized) * 100) / 100, open: true }]
            : base;
          const finalPnl = chartData.at(-1)?.pnl ?? 0;
          if (chartData.length === 0) return (
            <p className="text-xs text-muted-foreground text-center py-8">No trades yet — place a trade to start tracking</p>
          );
          return (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData}>
                <XAxis dataKey="time" hide />
                <YAxis hide domain={["auto", "auto"]} />
                <Tooltip
                  contentStyle={{ background: "#0f0f0f", border: "1px solid #222", borderRadius: 8 }}
                  formatter={(v: number, _: string, props: { payload?: { open?: boolean } }) => [
                    `$${v.toFixed(2)}${props.payload?.open ? " (open)" : ""}`, "P&L"
                  ]}
                  labelFormatter={() => ""}
                />
                <ReferenceLine y={0} stroke="#444" strokeDasharray="3 3" />
                <Line type="monotone" dataKey="pnl" stroke={finalPnl >= 0 ? "#22c55e" : "#ef4444"} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          );
        })()}
      </div>

      {/* Strategy Breakdown */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold">Strategy Breakdown</h3>
        </div>
        {(strategies ?? []).length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-8">No strategy data yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 text-xs text-muted-foreground font-medium">Strategy</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">Trades</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">Win %</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">Avg Win</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">Avg Loss</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">P. Factor</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">Net P&L</th>
                </tr>
              </thead>
              <tbody>
                {(strategies ?? []).map((s) => (
                  <tr key={s.strategy} className="border-b border-border/50 hover:bg-white/3 transition-colors">
                    <td className="px-4 py-2.5 font-medium">{STRATEGY_NAMES[s.strategy] ?? s.strategy}</td>
                    <td className="px-4 py-2.5 text-right text-muted-foreground">
                      <span className="text-buy">{s.wins}W</span>
                      <span className="text-muted-foreground mx-1">/</span>
                      <span className="text-sell">{s.losses}L</span>
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <span className={cn("font-medium", s.winRate >= 0.5 ? "text-buy" : "text-sell")}>
                        {(s.winRate * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right text-buy tabular-nums">+${s.avgWin.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-right text-sell tabular-nums">-${s.avgLoss.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      <span className={cn(s.profitFactor >= 1.5 ? "text-buy" : s.profitFactor >= 1 ? "text-foreground" : "text-sell")}>
                        {s.profitFactor >= 999 ? "∞" : s.profitFactor.toFixed(2)}
                      </span>
                    </td>
                    <td className={cn("px-4 py-2.5 text-right font-semibold tabular-nums", s.netPnl >= 0 ? "text-buy" : "text-sell")}>
                      {fmt(s.netPnl)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Trades */}

      <div className="glass rounded-2xl overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center gap-2">
          <h3 className="text-sm font-semibold flex-1">Recent Trades</h3>
          <span className="text-xs text-muted-foreground">Last 30</span>
        </div>
        {(trades ?? []).length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-8">No trades yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 text-xs text-muted-foreground font-medium">Symbol</th>
                  <th className="text-left px-4 py-3 text-xs text-muted-foreground font-medium">Side</th>
                  <th className="text-left px-4 py-3 text-xs text-muted-foreground font-medium">Strategy</th>
                  <th className="text-left px-4 py-3 text-xs text-muted-foreground font-medium">Time (ET)</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">Entry</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">Exit</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">P&L</th>
                  <th className="text-right px-4 py-3 text-xs text-muted-foreground font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {(trades ?? []).map((t) => {
                  const displayPnl = t.pnl != null ? t.pnl : null;
                  return (
                  <tr key={t._id} className="border-b border-border/50 hover:bg-white/3 transition-colors">
                    <td className="px-4 py-2.5 font-medium">{t.symbol}</td>
                    <td className="px-4 py-2.5">
                      <span className={cn("text-xs font-semibold", t.side === "Long" ? "text-buy" : "text-sell")}>
                        {t.side === "Long" ? "▲ Long" : "▼ Short"}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-xs text-muted-foreground">
                      {STRATEGY_NAMES[t.strategy ?? ""] ?? t.strategy ?? "Manual"}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-muted-foreground tabular-nums">
                      {new Date(t.executedAt).toLocaleString("en-US", { timeZone: "America/New_York", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: true })}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums">{t.entryPrice > 0 ? t.entryPrice.toFixed(2) : "—"}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">
                      {t.exitPrice ? t.exitPrice.toFixed(2) : "—"}
                    </td>
                    <td className={cn("px-4 py-2.5 text-right font-semibold tabular-nums",
                      displayPnl == null ? "text-muted-foreground" : displayPnl >= 0 ? "text-buy" : "text-sell"
                    )}>
                      {displayPnl != null
                        ? <>{fmt(displayPnl)}{t.status === "open" && <span className="text-[10px] text-muted-foreground ml-1">unr.</span>}</>
                        : "—"}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium",
                        t.status === "open" ? "bg-primary/10 text-primary" : "bg-white/5 text-muted-foreground"
                      )}>
                        {t.status}
                      </span>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Debug: userId check */}
      <p className="text-[10px] text-muted-foreground/40 text-center select-all">
        uid: {userId || "loading…"}
      </p>
    </div>
  );
}
