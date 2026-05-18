# Best timeframe per strategy — backtested across 6 pairs (May 2026)
# TF codes: "1m","5m","15m","1h","4h","1d"   |   "live" = session-based, TradingView only
STRATEGY_TIMEFRAMES = {
    "ORB":               "15m",
    "BREAK_RETEST":      "5m",
    "SWEEP_REVERSAL":    "15m",
    "MEAN_REVERSION":    "1d",
    "FVG":               "1d",
    "IFVG":              "1d",
    "FIB_RETRACEMENT":   "1d",
    "VWAP_RECLAIM":      "1h",
    "VWAP_REJECTION":    "1h",
    "FADE":              "1d",
    "RANGE":             "1h",
    "ASIA_RANGE":        "live",
    "NEWS_CONTINUATION": "5m",
    "GAP_GO":            "5m",
    "BOS":               "15m",
    "SMC":               "1h",
    "MOMENTUM":          "1h",
    "BREAKOUT":          "1h",
    "SCALP":             "1h",
    "TREND_FOLLOW":      "1d",
    "REVERSAL":          "1h",
    "AMD_DISTRIBUTION":  "live",
    "ORDER_BLOCK":       "1h",
    "SUPPLY_ZONE":       "1d",
    "DEMAND_ZONE":       "1d",
    "VWAP_BAND":         "1h",
    "INSIDE_BAR":        "4h",
    "EMA_CROSS":         "1h",
    "BB_SQUEEZE":        "4h",
    "PREV_DAY_HL":      "4h",
    "GAP_FILL":         "5m",
    "GAP_GO":           "1h",
    "VWAP_2SD":         "4h",
    "OPENING_DRIVE":    "4h",
    "WILLIAMS_R":       "1d",
    "MONTHLY_OPEN":     "1d",
    "TREND_GAP_FILL":   "1d",   # 77.7% avg WR, PF 1.17-1.50 backtested May 2026
    "MONDAY_GAP_FILL":  "1d",   # 65% avg WR, B-grade
    "QUARTERLY_OPEN":   "1d",   # 58% avg WR, B-grade (PF 2.1)
    "OVERNIGHT_DRIFT":  "1d",   # 55.6% avg WR, B-grade
}

STRATEGY_REGISTRY = {
    "ORB_LONG":                {"active": True,  "min_confidence": 0.65, "best_tf": "15m", "filters": [], "improvement_attempts": 0},
    "ORB_SHORT":               {"active": True,  "min_confidence": 0.65, "best_tf": "15m", "filters": [], "improvement_attempts": 0},
    "BREAK_RETEST_LONG":       {"active": False, "min_confidence": 0.65, "best_tf": "5m",  "filters": [], "improvement_attempts": 0},
    "BREAK_RETEST_SHORT":      {"active": False, "min_confidence": 0.65, "best_tf": "5m",  "filters": [], "improvement_attempts": 0},
    "SWEEP_REVERSAL_LONG":     {"active": False, "min_confidence": 0.65, "best_tf": "15m", "filters": [], "improvement_attempts": 0},
    "SWEEP_REVERSAL_SHORT":    {"active": False, "min_confidence": 0.65, "best_tf": "15m", "filters": [], "improvement_attempts": 0},
    "MEAN_REVERSION_LONG":     {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "MEAN_REVERSION_SHORT":    {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "FVG_LONG":                {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "FVG_SHORT":               {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "IFVG_LONG":               {"active": False, "min_confidence": 0.62, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "IFVG_SHORT":              {"active": False, "min_confidence": 0.62, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "FIB_RETRACEMENT_LONG":    {"active": False, "min_confidence": 0.67, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "FIB_RETRACEMENT_SHORT":   {"active": False, "min_confidence": 0.67, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "VWAP_RECLAIM_LONG":       {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "VWAP_REJECTION_SHORT":    {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "FADE_SHORT":              {"active": False, "min_confidence": 0.68, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "FADE_LONG":               {"active": False, "min_confidence": 0.68, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "RANGE_LONG":              {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "RANGE_SHORT":             {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "ASIA_RANGE_BULL":         {"active": True,  "min_confidence": 0.67, "best_tf": "live","filters": [], "improvement_attempts": 0},
    "ASIA_RANGE_BEAR":         {"active": True,  "min_confidence": 0.67, "best_tf": "live","filters": [], "improvement_attempts": 0},
    "NEWS_CONTINUATION_LONG":  {"active": False, "min_confidence": 0.68, "best_tf": "5m",  "filters": [], "improvement_attempts": 0},
    "NEWS_CONTINUATION_SHORT": {"active": False, "min_confidence": 0.68, "best_tf": "5m",  "filters": [], "improvement_attempts": 0},
    "GAP_GO_LONG":             {"active": False, "min_confidence": 0.68, "best_tf": "5m",  "filters": [], "improvement_attempts": 0},
    "GAP_GO_SHORT":            {"active": False, "min_confidence": 0.68, "best_tf": "5m",  "filters": [], "improvement_attempts": 0},
    "BOS_LONG":                {"active": True,  "min_confidence": 0.65, "best_tf": "15m", "filters": [], "improvement_attempts": 0},
    "BOS_SHORT":               {"active": True,  "min_confidence": 0.65, "best_tf": "15m", "filters": [], "improvement_attempts": 0},
    "SMC_LONG":                {"active": True,  "min_confidence": 0.72, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "SMC_SHORT":               {"active": True,  "min_confidence": 0.72, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "MOMENTUM_LONG":           {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "MOMENTUM_SHORT":          {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "BREAKOUT_LONG":           {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "BREAKOUT_SHORT":          {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "SCALP_LONG":              {"active": True,  "min_confidence": 0.70, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "SCALP_SHORT":             {"active": True,  "min_confidence": 0.70, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "TREND_FOLLOW_LONG":       {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "TREND_FOLLOW_SHORT":      {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "REVERSAL_LONG":           {"active": False, "min_confidence": 0.70, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "REVERSAL_SHORT":          {"active": False, "min_confidence": 0.70, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "AMD_DISTRIBUTION_LONG":   {"active": False, "min_confidence": 0.70, "best_tf": "live","filters": [], "improvement_attempts": 0},
    "AMD_DISTRIBUTION_SHORT":  {"active": False, "min_confidence": 0.70, "best_tf": "live","filters": [], "improvement_attempts": 0},

    # ── NEW STRATEGIES (added after backtest validation May 2026) ──────────────
    # ICT Order Block: 1H is best — 62% WR, PF 2.85 (Grade A)
    "ORDER_BLOCK_LONG":        {"active": True,  "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "ORDER_BLOCK_SHORT":       {"active": True,  "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},

    # Supply & Demand Zones: 1D best — 55.3% WR, PF 1.20 (Grade B)
    "SUPPLY_ZONE_SHORT":       {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "DEMAND_ZONE_LONG":        {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},

    # VWAP Bands: 1H best — 58.6% WR, PF 1.09 (Grade C)
    "VWAP_BAND_LONG":          {"active": True,  "min_confidence": 0.63, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "VWAP_BAND_SHORT":         {"active": True,  "min_confidence": 0.63, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},

    # Inside Bar: 4H best — 63% WR, PF 1.86 (Grade A)
    "INSIDE_BAR_LONG":         {"active": True,  "min_confidence": 0.62, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},
    "INSIDE_BAR_SHORT":        {"active": True,  "min_confidence": 0.62, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},

    # Dual EMA Cross: 1H best — 59% WR, PF 1.50 (Grade B)
    "EMA_CROSS_LONG":          {"active": True,  "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "EMA_CROSS_SHORT":         {"active": True,  "min_confidence": 0.65, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},

    # BB Squeeze: 4H best — 61% WR, PF 4.57 (Grade B)
    "BB_SQUEEZE_LONG":         {"active": True,  "min_confidence": 0.65, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},
    "BB_SQUEEZE_SHORT":        {"active": True,  "min_confidence": 0.65, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},

    # ── ROUND 2 ADDITIONS (backtested May 2026) ───────────────────────────────
    # Prev Day H/L Break: 4H best — 63.5% WR, PF 3.57 (Grade A)
    "PREV_DAY_HL_LONG":        {"active": True,  "min_confidence": 0.65, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},
    "PREV_DAY_HL_SHORT":       {"active": True,  "min_confidence": 0.65, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},

    # ── ROUND 3 ADDITIONS (backtested May 2026) ───────────────────────────────
    # Opening Gap Fill: 5m best — 80.7% WR, PF 2.11 (Grade S — all 6 pairs)
    "GAP_FILL_LONG":           {"active": True,  "min_confidence": 0.70, "best_tf": "5m",  "filters": [], "improvement_attempts": 0},
    "GAP_FILL_SHORT":          {"active": True,  "min_confidence": 0.70, "best_tf": "5m",  "filters": [], "improvement_attempts": 0},

    # ── ROUND 4 ADDITIONS (backtested May 2026) ───────────────────────────────
    # Gap and Go: 1H best — 64.2% WR, PF 4.18 (Grade A)
    "GAP_GO_LONG":             {"active": True,  "min_confidence": 0.68, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},
    "GAP_GO_SHORT":            {"active": True,  "min_confidence": 0.68, "best_tf": "1h",  "filters": [], "improvement_attempts": 0},

    # VWAP 2-Sigma Reversion: 4H best — 59.1% WR, PF 1.34 (Grade B)
    "VWAP_2SD_LONG":           {"active": True,  "min_confidence": 0.65, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},
    "VWAP_2SD_SHORT":          {"active": True,  "min_confidence": 0.65, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},

    # Opening Drive: 4H best — 57.0% WR, PF 1.90 (Grade B)
    "OPENING_DRIVE_LONG":      {"active": True,  "min_confidence": 0.65, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},
    "OPENING_DRIVE_SHORT":     {"active": True,  "min_confidence": 0.65, "best_tf": "4h",  "filters": [], "improvement_attempts": 0},

    # Williams %R Trend Pullback: 1D best — 56.9% WR, PF 2.45 (Grade B — all 6 pairs)
    "WILLIAMS_R_LONG":         {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "WILLIAMS_R_SHORT":        {"active": True,  "min_confidence": 0.65, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},

    # Monthly Open Respect: 1D best — 66.0% WR, PF 5.40 (Grade A — all 6 pairs)
    "MONTHLY_OPEN_LONG":       {"active": True,  "min_confidence": 0.68, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
    "MONTHLY_OPEN_SHORT":      {"active": True,  "min_confidence": 0.68, "best_tf": "1d",  "filters": [], "improvement_attempts": 0},
}


def is_strategy_active(strategy_code: str) -> bool:
    entry = STRATEGY_REGISTRY.get(strategy_code, {})
    return entry.get("active", False)


def get_min_confidence(strategy_code: str) -> float:
    entry = STRATEGY_REGISTRY.get(strategy_code, {})
    return entry.get("min_confidence", 0.65)


def get_best_tf(strategy_code: str) -> str:
    """Return the backtested optimal timeframe for this strategy signal."""
    entry = STRATEGY_REGISTRY.get(strategy_code, {})
    if entry.get("best_tf"):
        return entry["best_tf"]
    base = strategy_code.rsplit("_", 1)[0]  # strip _LONG / _SHORT
    return STRATEGY_TIMEFRAMES.get(base, "1h")


def add_filter(strategy_code: str, filter_dict: dict) -> bool:
    """Called by self_improvement_engine to add a filter to a strategy."""
    if strategy_code in STRATEGY_REGISTRY:
        STRATEGY_REGISTRY[strategy_code]["filters"].append(filter_dict)
        return True
    return False


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
