"""
adaptive_risk.py
================
Live-market adaptive risk manager.

Implements three mechanisms:
  1. Rolling WR (last 15 trades) → scales down risk when market turns hostile
  2. Per-strategy cooldown       → skips a strategy after 3 consecutive losses today
  3. Intraday profit lock        → protects a big day by reducing risk once up 5× base

Usage:
    from core.adaptive_risk import AdaptiveRiskManager

    rm = AdaptiveRiskManager(base_risk=200.0)
    rm.new_day()                          # call at the start of each trading day

    if not rm.should_take_trade("order_block"):
        continue                          # strategy on cooldown

    risk = rm.get_trade_risk()            # returns adapted $ risk for this trade
    # ... execute trade ...
    rm.record_outcome("order_block", pnl) # pnl > 0 = win, < 0 = loss
"""

from collections import deque
from datetime import date


class AdaptiveRiskManager:
    # ── WR thresholds ─────────────────────────────────────────────────────────
    WR_TIERS = [
        (0.60, 1.00, "NORMAL"),
        (0.45, 0.85, "CAUTIOUS"),
        (0.30, 0.70, "DEFENSIVE"),
        (0.00, 0.60, "SURVIVAL"),
    ]
    ROLLING_WINDOW   = 15    # trades in rolling WR window
    MIN_TRADES_FOR_ADAPT = 5 # need at least this many before adapting
    STRAT_COOLDOWN   = 3     # consecutive losses before strategy is skipped today
    LOCK_MULTIPLIER  = 5     # once day_pnl >= base_risk × this, activate profit lock
    LOCK_RISK_RATIO  = 0.60  # risk multiplier once profit lock is active

    def __init__(self, base_risk: float):
        self.base_risk = base_risk

        # Rolling WR state (persists across days)
        self._outcomes: deque = deque(maxlen=self.ROLLING_WINDOW)

        # Daily state (reset each day)
        self._day_pnl:       float = 0.0
        self._strat_streaks: dict  = {}
        self._profit_locked: bool  = False
        self._current_date:  date  = None

    # ── Day boundary ──────────────────────────────────────────────────────────

    def new_day(self, today: date = None) -> None:
        """Call at the start of each trading day to reset daily state."""
        self._day_pnl       = 0.0
        self._strat_streaks = {}
        self._profit_locked = False
        self._current_date  = today or date.today()

    # ── Pre-trade checks ──────────────────────────────────────────────────────

    def should_take_trade(self, strategy_id: str) -> bool:
        """
        Returns False if this strategy has hit its daily cooldown limit.
        Call this before sizing a trade.
        """
        return self._strat_streaks.get(strategy_id, 0) < self.STRAT_COOLDOWN

    def get_trade_risk(self) -> float:
        """
        Returns the $ risk to use for the next trade, accounting for:
          - Rolling WR multiplier
          - Intraday profit lock
        Always returns a value >= 30.0.
        """
        mult = self._wr_multiplier()

        # Base adaptive risk
        adapted = self.base_risk * mult

        # Profit lock: if already up 5× base_risk today, drop to 60% of adapted
        if self._profit_locked or self._day_pnl >= self.base_risk * self.LOCK_MULTIPLIER:
            self._profit_locked = True
            adapted = adapted * self.LOCK_RISK_RATIO

        return max(30.0, round(adapted / 5) * 5)

    def get_mode(self) -> str:
        """Returns current adaptive mode label: NORMAL / CAUTIOUS / DEFENSIVE / SURVIVAL."""
        mult, label = self._wr_mult_and_label()
        prefix = label
        if self._profit_locked or self._day_pnl >= self.base_risk * self.LOCK_MULTIPLIER:
            prefix += "+LOCK" if prefix else "LOCK"
        return prefix or "NORMAL"

    # ── Post-trade update ─────────────────────────────────────────────────────

    def record_outcome(self, strategy_id: str, pnl: float) -> None:
        """
        Call after every completed trade with its P&L.
        Updates rolling WR, per-strategy streak, and daily P&L.
        """
        win = pnl > 0
        self._outcomes.append(win)
        self._day_pnl += pnl

        if win:
            self._strat_streaks[strategy_id] = 0
        else:
            self._strat_streaks[strategy_id] = self._strat_streaks.get(strategy_id, 0) + 1

    # ── Inspection ────────────────────────────────────────────────────────────

    def rolling_wr(self) -> float:
        """Current rolling win rate (0.0–1.0). Returns 1.0 if not enough trades yet."""
        if len(self._outcomes) < self.MIN_TRADES_FOR_ADAPT:
            return 1.0
        return sum(self._outcomes) / len(self._outcomes)

    def day_pnl(self) -> float:
        return self._day_pnl

    def is_profit_locked(self) -> bool:
        return self._profit_locked or self._day_pnl >= self.base_risk * self.LOCK_MULTIPLIER

    def strategy_streak(self, strategy_id: str) -> int:
        return self._strat_streaks.get(strategy_id, 0)

    def status_line(self) -> str:
        """One-line summary for logging/display."""
        wr  = self.rolling_wr()
        n   = len(self._outcomes)
        mode = self.get_mode()
        risk = self.get_trade_risk()
        return (f"AdaptiveRisk | mode={mode} | WR={wr:.0%} ({n} trades) "
                f"| day_pnl=${self._day_pnl:+,.2f} | next_risk=${risk:.0f}")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _wr_multiplier(self) -> float:
        return self._wr_mult_and_label()[0]

    def _wr_mult_and_label(self):
        if len(self._outcomes) < self.MIN_TRADES_FOR_ADAPT:
            return 1.0, ""
        wr = sum(self._outcomes) / len(self._outcomes)
        for threshold, mult, label in self.WR_TIERS:
            if wr >= threshold:
                return mult, ("" if label == "NORMAL" else label)
        return 0.60, "SURVIVAL"
