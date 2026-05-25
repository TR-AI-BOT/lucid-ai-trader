# v18 Walk-Forward Validated Roster — 28 strategies
# Combined: 41.7% WR | +$672,835 P&L | 228,204 trades | 5-year window | 3 symbols
# Timeframes per strategy listed in PRIORITY ORDER (best P&L first)
# Bot checks all approved_tfs and enters on the cleanest setup

STRATEGY_REGISTRY = {

    # ── 01 · P02_FVG · Fair Value Gap retest ─────────────────────────────────
    "FVG_LONG":         {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "15m", "30m"], "wr": 41.3, "total_pnl": 123450},
    "FVG_SHORT":        {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "15m", "30m"], "wr": 41.3, "total_pnl": 123450},

    # ── 02 · N12_MOM_BURST · Momentum Burst ──────────────────────────────────
    "MOM_BURST_LONG":   {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m", "5m", "1h"],  "wr": 42.8, "total_pnl": 73522},
    "MOM_BURST_SHORT":  {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m", "5m", "1h"],  "wr": 42.8, "total_pnl": 73522},

    # ── 03 · P07_IBB · Initial Balance Breakout ───────────────────────────────
    "IBB_LONG":         {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m", "5m", "1h"],  "wr": 47.6, "total_pnl": 62156},
    "IBB_SHORT":        {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m", "5m", "1h"],  "wr": 47.6, "total_pnl": 62156},

    # ── 04 · N01_ENGULF · Engulfing Candle ───────────────────────────────────
    "ENGULF_LONG":      {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m", "30m", "1h"], "wr": 39.8, "total_pnl": 47352},
    "ENGULF_SHORT":     {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m", "30m", "1h"], "wr": 39.8, "total_pnl": 47352},

    # ── 05 · P03_OB_RETEST · Order Block Retest ──────────────────────────────
    "OB_RETEST_LONG":   {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m", "30m", "4h"], "wr": 41.0, "total_pnl": 45089},
    "OB_RETEST_SHORT":  {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m", "30m", "4h"], "wr": 41.0, "total_pnl": 45089},

    # ── 06 · N11_TREND_EMA8 · Trend + EMA8 Pullback ──────────────────────────
    "TREND_EMA8_LONG":  {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m", "30m", "1h"], "wr": 43.7, "total_pnl": 37754},
    "TREND_EMA8_SHORT": {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m", "30m", "1h"], "wr": 43.7, "total_pnl": 37754},

    # ── 07 · P04_AMD_PO3 · AMD + Power of 3 ─────────────────────────────────
    "AMD_PO3_LONG":     {"active": True, "min_confidence": 0.65, "approved_tfs": ["30m", "15m", "5m"], "wr": 43.4, "total_pnl": 29081},
    "AMD_PO3_SHORT":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["30m", "15m", "5m"], "wr": 43.4, "total_pnl": 29081},

    # ── 08 · N02_PIN_EMA · Pin Bar + EMA ─────────────────────────────────────
    "PIN_EMA_LONG":     {"active": True, "min_confidence": 0.65, "approved_tfs": ["30m", "1h", "4h"],  "wr": 42.5, "total_pnl": 26605},
    "PIN_EMA_SHORT":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["30m", "1h", "4h"],  "wr": 42.5, "total_pnl": 26605},

    # ── 09 · N03_IB_BREAK · Initial Balance Breakout (Pattern) ───────────────
    "IB_BREAK_LONG":    {"active": True, "min_confidence": 0.68, "approved_tfs": ["30m", "15m", "4h"], "wr": 47.1, "total_pnl": 21323},
    "IB_BREAK_SHORT":   {"active": True, "min_confidence": 0.68, "approved_tfs": ["30m", "15m", "4h"], "wr": 47.1, "total_pnl": 21323},

    # ── 10 · P12_VWAP_RCL · VWAP Reclaim ────────────────────────────────────
    "VWAP_RCL_LONG":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["30m", "15m", "4h"], "wr": 39.6, "total_pnl": 20469},
    "VWAP_RCL_SHORT":   {"active": True, "min_confidence": 0.65, "approved_tfs": ["30m", "15m", "4h"], "wr": 39.6, "total_pnl": 20469},

    # ── 11 · S08_LON_4CONF · London 4-Confluence ─────────────────────────────
    "LON_4CONF_LONG":   {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m", "4h", "30m"], "wr": 47.3, "total_pnl": 19668},
    "LON_4CONF_SHORT":  {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m", "4h", "30m"], "wr": 47.3, "total_pnl": 19668},

    # ── 12 · N05_EMA200_B · EMA200 Bounce ────────────────────────────────────
    "EMA200_B_LONG":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m"],              "wr": 41.0, "total_pnl": 17886},
    "EMA200_B_SHORT":   {"active": True, "min_confidence": 0.65, "approved_tfs": ["15m"],              "wr": 41.0, "total_pnl": 17886},

    # ── 13 · P29_THU_IBB · Thursday IBB ─────────────────────────────────────
    "THU_IBB_LONG":     {"active": True, "min_confidence": 0.68, "approved_tfs": ["5m", "1h", "30m"],  "wr": 48.8, "total_pnl": 17674},
    "THU_IBB_SHORT":    {"active": True, "min_confidence": 0.68, "approved_tfs": ["5m", "1h", "30m"],  "wr": 48.8, "total_pnl": 17674},

    # ── 14 · S25_2PM_KILL · 2 PM Kill Zone ───────────────────────────────────
    "PM_KILL_LONG":     {"active": True, "min_confidence": 0.72, "approved_tfs": ["1h", "30m"],        "wr": 55.0, "total_pnl": 14727},
    "PM_KILL_SHORT":    {"active": True, "min_confidence": 0.72, "approved_tfs": ["1h", "30m"],        "wr": 55.0, "total_pnl": 14727},

    # ── 15 · S06_LON_3CONF · London 3-Confluence ─────────────────────────────
    "LON_3CONF_LONG":   {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m", "30m"],       "wr": 45.9, "total_pnl": 10961},
    "LON_3CONF_SHORT":  {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m", "30m"],       "wr": 45.9, "total_pnl": 10961},

    # ── 16 · S20_PO3 · Power of 3 ────────────────────────────────────────────
    "PO3_LONG":         {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "30m", "15m"], "wr": 42.3, "total_pnl": 10277},
    "PO3_SHORT":        {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "30m", "15m"], "wr": 42.3, "total_pnl": 10277},

    # ── 17 · P15_RSI2_MR · RSI-2 Mean Reversion ──────────────────────────────
    "RSI2_MR_LONG":     {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "30m", "15m"], "wr": 37.8, "total_pnl": 10206},
    "RSI2_MR_SHORT":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "30m", "15m"], "wr": 37.8, "total_pnl": 10206},

    # ── 18 · S03_LON_RSI · London + RSI ─────────────────────────────────────
    "LON_RSI_LONG":     {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m", "30m"],       "wr": 45.9, "total_pnl": 9715},
    "LON_RSI_SHORT":    {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m", "30m"],       "wr": 45.9, "total_pnl": 9715},

    # ── 19 · S05_LON_BODY · London Body-Size ─────────────────────────────────
    "LON_BODY_LONG":    {"active": True, "min_confidence": 0.68, "approved_tfs": ["1h"],               "wr": 46.6, "total_pnl": 9297},
    "LON_BODY_SHORT":   {"active": True, "min_confidence": 0.68, "approved_tfs": ["1h"],               "wr": 46.6, "total_pnl": 9297},

    # ── 20 · P17_BB_RANGE · Bollinger Band Range ─────────────────────────────
    "BB_RANGE_LONG":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "4h"],         "wr": 44.2, "total_pnl": 9075},
    "BB_RANGE_SHORT":   {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "4h"],         "wr": 44.2, "total_pnl": 9075},

    # ── 21 · C05_3PUSH · 3-Push Exhaustion ───────────────────────────────────
    "PUSH_3_LONG":      {"active": True, "min_confidence": 0.68, "approved_tfs": ["30m", "1h", "15m"], "wr": 47.8, "total_pnl": 8278},
    "PUSH_3_SHORT":     {"active": True, "min_confidence": 0.68, "approved_tfs": ["30m", "1h", "15m"], "wr": 47.8, "total_pnl": 8278},

    # ── 22 · S22_WEEK_OPEN · Weekly Open Fade ────────────────────────────────
    "WEEK_OPEN_LONG":   {"active": True, "min_confidence": 0.65, "approved_tfs": ["5m", "30m"],        "wr": 37.5, "total_pnl": 7997},
    "WEEK_OPEN_SHORT":  {"active": True, "min_confidence": 0.65, "approved_tfs": ["5m", "30m"],        "wr": 37.5, "total_pnl": 7997},

    # ── 23 · S07_LON_3CE · London 3-Conf + EMA ───────────────────────────────
    "LON_3CE_LONG":     {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m"],              "wr": 45.4, "total_pnl": 7961},
    "LON_3CE_SHORT":    {"active": True, "min_confidence": 0.68, "approved_tfs": ["15m"],              "wr": 45.4, "total_pnl": 7961},

    # ── 24 · S23_MID_OPEN · Midnight Open Level ───────────────────────────────
    "MID_OPEN_LONG":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "15m"],        "wr": 38.8, "total_pnl": 7464},
    "MID_OPEN_SHORT":   {"active": True, "min_confidence": 0.65, "approved_tfs": ["1h", "15m"],        "wr": 38.8, "total_pnl": 7464},

    # ── 25 · P18_VWAP_2SD · VWAP 2-Standard Deviation ───────────────────────
    "VWAP_2SD_LONG":    {"active": True, "min_confidence": 0.68, "approved_tfs": ["30m", "15m"],       "wr": 49.4, "total_pnl": 6838},
    "VWAP_2SD_SHORT":   {"active": True, "min_confidence": 0.68, "approved_tfs": ["30m", "15m"],       "wr": 49.4, "total_pnl": 6838},

    # ── 26 · S19_MON_GAP · Monday Gap Fade ───────────────────────────────────
    "MON_GAP_LONG":     {"active": True, "min_confidence": 0.65, "approved_tfs": ["5m", "15m", "30m"], "wr": 37.5, "total_pnl": 6567},
    "MON_GAP_SHORT":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["5m", "15m", "30m"], "wr": 37.5, "total_pnl": 6567},

    # ── 27 · C01_LN_HANDOFF · London → NY Handoff ────────────────────────────
    "LN_HANDOFF_LONG":  {"active": True, "min_confidence": 0.65, "approved_tfs": ["5m"],               "wr": 45.4, "total_pnl": 6059},
    "LN_HANDOFF_SHORT": {"active": True, "min_confidence": 0.65, "approved_tfs": ["5m"],               "wr": 45.4, "total_pnl": 6059},

    # ── 28 · S26_PREV_HL · Previous Day High/Low ─────────────────────────────
    "PREV_HL_LONG":     {"active": True, "min_confidence": 0.65, "approved_tfs": ["4h"],               "wr": 42.2, "total_pnl": 5384},
    "PREV_HL_SHORT":    {"active": True, "min_confidence": 0.65, "approved_tfs": ["4h"],               "wr": 42.2, "total_pnl": 5384},

    # ── v19 NEW STRATEGIES — Walk-Forward Validated (5yr, 3 symbols) ─────────

    # ── 29 · N21_LON_NY · London-to-NY Continuation ──────────────────────────
    # London breaks Asia range and holds above/below into NY open → NY continues
    # v19: 54.3% WR (15m native) | 690 trades | +$20,293 P&L | CONS
    "LON_NY_LONG":      {"active": True, "min_confidence": 0.72, "approved_tfs": ["15m", "5m", "30m"], "wr": 54.3, "total_pnl": 20293},
    "LON_NY_SHORT":     {"active": True, "min_confidence": 0.72, "approved_tfs": ["15m", "5m", "30m"], "wr": 54.3, "total_pnl": 20293},

    # ── 30 · N19_MON_PWR · Monday Open Power Move ────────────────────────────
    # Monday 9:30-10 AM ET strong body + EMA200 regime + no adverse gap
    # v19: 58.0% WR (5m) | 288 trades | +$6,867 P&L | CONS
    "MON_PWR_LONG":     {"active": True, "min_confidence": 0.72, "approved_tfs": ["5m"],               "wr": 58.0, "total_pnl": 6867},
    "MON_PWR_SHORT":    {"active": True, "min_confidence": 0.72, "approved_tfs": ["5m"],               "wr": 58.0, "total_pnl": 6867},

    # ── 31 · N22_ASIA_RET · Asia Break Retest ────────────────────────────────
    # London breaks Asia range, price retests the broken level and bounces
    # v19: 51.8% WR (5m) | 1,163 trades | +$4,478 P&L | CONS
    "ASIA_RET_LONG":    {"active": True, "min_confidence": 0.72, "approved_tfs": ["5m", "15m"],        "wr": 51.8, "total_pnl": 4478},
    "ASIA_RET_SHORT":   {"active": True, "min_confidence": 0.72, "approved_tfs": ["5m", "15m"],        "wr": 51.8, "total_pnl": 4478},

    # ── v20 NEW STRATEGIES — Walk-Forward Validated (5yr, 3 symbols) ─────────

    # ── 32 · N27_LON_DCONF · London Double Confirm ───────────────────────────
    # London: Asia break + EMA8/21 cross in same direction within 4-bar window
    # v20: 51.4% WR (5m) | 691 trades | +$9,995 P&L | CONS
    "LON_DCONF_LONG":   {"active": True, "min_confidence": 0.74, "approved_tfs": ["5m", "15m"],        "wr": 51.4, "total_pnl": 9995},
    "LON_DCONF_SHORT":  {"active": True, "min_confidence": 0.74, "approved_tfs": ["5m", "15m"],        "wr": 51.4, "total_pnl": 9995},

    # ── 33 · N24_IB_RETEST · Initial Balance Retest ──────────────────────────
    # 10:30 AM–Noon ET: price retests IB hi/lo with EMA200 regime alignment
    # v20: 59.8% WR (5m) | 107 trades | +$5,140 P&L | VARI — highest WR in roster
    "IB_RETEST_LONG":   {"active": True, "min_confidence": 0.73, "approved_tfs": ["5m", "15m", "30m"], "wr": 59.8, "total_pnl": 5140},
    "IB_RETEST_SHORT":  {"active": True, "min_confidence": 0.73, "approved_tfs": ["5m", "15m", "30m"], "wr": 59.8, "total_pnl": 5140},

    # ── 34 · N26_VWAP_TAP · VWAP Double Tap ─────────────────────────────────
    # RTH: two consecutive VWAP tags then bounce; EMA8/21 + RSI filter
    # v20: 46.4% WR (5m) | 5,427 trades | +$56,690 P&L — highest P&L contributor
    "VWAP_TAP_LONG":    {"active": True, "min_confidence": 0.73, "approved_tfs": ["5m", "15m", "30m"], "wr": 46.4, "total_pnl": 56690},
    "VWAP_TAP_SHORT":   {"active": True, "min_confidence": 0.73, "approved_tfs": ["5m", "15m", "30m"], "wr": 46.4, "total_pnl": 56690},

    # ── v21 NEW STRATEGIES — Walk-Forward Validated (5yr, 3 symbols) ─────────

    # ── 35 · N29_ORB_PULLBACK · Opening Range Pullback ───────────────────────
    # 9:45-10:30 AM ET: first pullback to ORB hi/lo after the opening range forms
    # v21: 50.4% WR (5m) | 504 trades | +$5,334 P&L | CONS ✅ PASS
    "ORB_PULLBACK_LONG":  {"active": True, "min_confidence": 0.73, "approved_tfs": ["5m", "15m"],        "wr": 50.4, "total_pnl": 5334},
    "ORB_PULLBACK_SHORT": {"active": True, "min_confidence": 0.73, "approved_tfs": ["5m", "15m"],        "wr": 50.4, "total_pnl": 5334},

    # ── 36 · N30_PDM_BOUNCE · Prior Day Midpoint Bounce ──────────────────────
    # RTH: pin bar rejection at prior day's (H+L)/2 midpoint with EMA alignment
    # v21: 49.1% WR (5m) | 491 trades | +$18,062 P&L | CONS
    "PDM_BOUNCE_LONG":    {"active": True, "min_confidence": 0.74, "approved_tfs": ["5m", "15m", "1H"], "wr": 49.1, "total_pnl": 18062},
    "PDM_BOUNCE_SHORT":   {"active": True, "min_confidence": 0.74, "approved_tfs": ["5m", "15m", "1H"], "wr": 49.1, "total_pnl": 18062},

    # ── 37 · N34_ORB_BREAK · Classic ORB Breakout ────────────────────────────
    # 9:45 AM-Noon ET: close outside 9:30-9:44 opening range with EMA200 regime
    # v21: 48.9% WR (5m) | 1,805 trades | +$19,936 P&L | CONS — highest P&L of v21
    "ORB_BREAK_LONG":     {"active": True, "min_confidence": 0.74, "approved_tfs": ["5m", "15m", "30m"], "wr": 48.9, "total_pnl": 19936},
    "ORB_BREAK_SHORT":    {"active": True, "min_confidence": 0.74, "approved_tfs": ["5m", "15m", "30m"], "wr": 48.9, "total_pnl": 19936},

    # ── 38 · N32_WED_PWR · Wednesday Power Hour ──────────────────────────────
    # Wednesday 2-4 PM ET: fresh EMA8/21 cross + VWAP alignment + RSI momentum
    # v21: 49.6% WR (15m) | 117 trades | +$3,693 P&L | VARI
    "WED_PWR_LONG":       {"active": True, "min_confidence": 0.74, "approved_tfs": ["15m", "30m"],        "wr": 49.6, "total_pnl": 3693},
    "WED_PWR_SHORT":      {"active": True, "min_confidence": 0.74, "approved_tfs": ["15m", "30m"],        "wr": 49.6, "total_pnl": 3693},
}


# ── Convenience maps ──────────────────────────────────────────────────────────

def is_strategy_active(strategy_code: str) -> bool:
    return STRATEGY_REGISTRY.get(strategy_code, {}).get("active", False)


def get_approved_tfs(strategy_code: str) -> list:
    """Return approved timeframes in priority order (best P&L first)."""
    return STRATEGY_REGISTRY.get(strategy_code, {}).get("approved_tfs", ["15m"])


def get_best_tf(strategy_code: str) -> str:
    """Return the single highest-priority approved timeframe."""
    tfs = get_approved_tfs(strategy_code)
    return tfs[0] if tfs else "15m"


def get_min_confidence(strategy_code: str) -> float:
    return STRATEGY_REGISTRY.get(strategy_code, {}).get("min_confidence", 0.65)


def get_wr(strategy_code: str) -> float:
    return STRATEGY_REGISTRY.get(strategy_code, {}).get("wr", 0.0)


def pause_strategy(strategy_code: str, reason: str) -> bool:
    if strategy_code in STRATEGY_REGISTRY:
        STRATEGY_REGISTRY[strategy_code]["active"] = False
        STRATEGY_REGISTRY[strategy_code]["pause_reason"] = reason
        return True
    return False


def resume_strategy(strategy_code: str) -> bool:
    if strategy_code in STRATEGY_REGISTRY:
        STRATEGY_REGISTRY[strategy_code]["active"] = True
        STRATEGY_REGISTRY[strategy_code].pop("pause_reason", None)
        return True
    return False


def active_strategies() -> list:
    return [k for k, v in STRATEGY_REGISTRY.items() if v.get("active")]


def roster_summary() -> dict:
    active = active_strategies()
    return {
        "total_strategies": len(STRATEGY_REGISTRY) // 2,
        "active_pairs":     len(active),
        "combined_wr":      41.7,
        "combined_pnl":     672835,
        "total_trades":     228204,
    }
