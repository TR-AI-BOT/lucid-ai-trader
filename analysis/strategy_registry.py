# Best timeframe per strategy — Final 24-entry roster (backtested May 2026)
# Combined portfolio: 72.1% weighted WR, 13,919 trades, S class
# TF codes: "1m","5m","15m","30m","1h","4h","1d" | "live" = session-based
STRATEGY_TIMEFRAMES = {
    # ── S class (70%+ WR) ────────────────────────────────────────────────────
    "TREND_GAP_FILL":        "30m",  # S  76% avg WR — also runs 5m/15m/1h/4h
    "GAP_FILL":              "5m",   # S  73-78% WR  — also runs 1h/15m
    "SILVER_BULLET_STRICT":  "30m",  # S  70.5% WR, PF 3.06 — strict 10am/2pm only
    "MONDAY_GAP_FILL":       "15m",  # S/B 73.4% on 15m, 66.3% on 1h
    # ── A class (62%+ WR, PF 1.3+) ───────────────────────────────────────────
    "ORDER_BLOCK":           "1h",   # A  62.4% WR, PF 2.85
    "BB_SQUEEZE":            "30m",  # A  63.1% WR, PF 1.52
    # ── B class (55%+ WR, all profitable) ────────────────────────────────────
    "SMC":                   "30m",  # B  61.7% WR, PF 1.38
    "SUPERTREND":            "30m",  # B  60.6% WR, PF 5.61
    "EMA_CROSS":             "1h",   # B  58.9% WR, PF 1.51
    "ORB":                   "1h",   # B  59.4% WR, PF 1.98
    "TREND_FOLLOW":          "30m",  # B  57.6% WR, PF 9.99
    "INSIDE_BAR":            "15m",  # B  58.1% WR on 15m, 57.6% on 30m
    "FVG":                   "30m",  # C  57.9% WR, PF 1.07
    "MOMENTUM":              "30m",  # B  56.1% WR, PF 2.37
    "DONCHIAN_BREAK":        "30m",  # B  55.6% WR, PF 2.94
    "MONTHLY_OPEN":          "15m",  # B  55.1% WR, PF 9.99
    # ── Not in final roster (kept for reference) ──────────────────────────────
    "ORB_RETEST":            "5m",
    "BREAK_RETEST":          "5m",
    "SWEEP_REVERSAL":        "15m",
    "MEAN_REVERSION":        "1d",
    "IFVG":                  "1d",
    "FIB_RETRACEMENT":       "1d",
    "VWAP_RECLAIM":          "1h",
    "FADE":                  "1d",
    "RANGE":                 "1h",
    "ASIA_RANGE":            "live",
    "NEWS_CONTINUATION":     "5m",
    "GAP_GO":                "1h",
    "BOS":                   "15m",
    "BREAKOUT":              "1h",
    "SCALP":                 "1h",
    "REVERSAL":              "1h",
    "AMD_DISTRIBUTION":      "live",
    "QUARTERLY_OPEN":        "1d",
    "OVERNIGHT_DRIFT":       "1d",
    "VWAP_2SD":              "4h",
    "OPENING_DRIVE":         "4h",
    "WILLIAMS_R":            "1d",
    "PREV_DAY_HL":           "4h",
}

# ── FINAL ROSTER — 24 entries, 20 unique strategies, 72.1% combined WR ────────
STRATEGY_REGISTRY = {
    # ── S class: 70%+ WR ─────────────────────────────────────────────────────
    # Trend Gap Fill — S class on ALL timeframes tested
    "TREND_GAP_FILL_LONG":         {"active": True,  "min_confidence": 0.72, "best_tf": "30m", "grade": "S", "wr": 76.3, "filters": [], "improvement_attempts": 0},
    "TREND_GAP_FILL_SHORT":        {"active": True,  "min_confidence": 0.72, "best_tf": "30m", "grade": "S", "wr": 76.3, "filters": [], "improvement_attempts": 0},
    # Opening Gap Fill — S on 5m, B on 1h/15m
    "GAP_FILL_LONG":               {"active": True,  "min_confidence": 0.70, "best_tf": "5m",  "grade": "S", "wr": 73.0, "filters": [], "improvement_attempts": 0},
    "GAP_FILL_SHORT":              {"active": True,  "min_confidence": 0.70, "best_tf": "5m",  "grade": "S", "wr": 73.0, "filters": [], "improvement_attempts": 0},
    # ICT Silver Bullet — S class, strict 10am/2pm NY time windows only
    "SILVER_BULLET_LONG":          {"active": True,  "min_confidence": 0.75, "best_tf": "30m", "grade": "S", "wr": 70.5, "filters": [], "improvement_attempts": 0},
    "SILVER_BULLET_SHORT":         {"active": True,  "min_confidence": 0.75, "best_tf": "30m", "grade": "S", "wr": 70.5, "filters": [], "improvement_attempts": 0},
    # Monday Gap Fill — S on 15m (73.4%), B on 1h (66.3%)
    "MONDAY_GAP_FILL_LONG":        {"active": True,  "min_confidence": 0.68, "best_tf": "15m", "grade": "S", "wr": 73.4, "filters": [], "improvement_attempts": 0},
    "MONDAY_GAP_FILL_SHORT":       {"active": True,  "min_confidence": 0.68, "best_tf": "15m", "grade": "S", "wr": 73.4, "filters": [], "improvement_attempts": 0},

    # ── A class: 62%+ WR, PF 1.3+ ────────────────────────────────────────────
    "ORDER_BLOCK_LONG":            {"active": True,  "min_confidence": 0.65, "best_tf": "1h",  "grade": "A", "wr": 62.4, "filters": [], "improvement_attempts": 0},
    "ORDER_BLOCK_SHORT":           {"active": True,  "min_confidence": 0.65, "best_tf": "1h",  "grade": "A", "wr": 62.4, "filters": [], "improvement_attempts": 0},
    "BB_SQUEEZE_LONG":             {"active": True,  "min_confidence": 0.65, "best_tf": "30m", "grade": "A", "wr": 63.1, "filters": [], "improvement_attempts": 0},
    "BB_SQUEEZE_SHORT":            {"active": True,  "min_confidence": 0.65, "best_tf": "30m", "grade": "A", "wr": 63.1, "filters": [], "improvement_attempts": 0},

    # ── B class: 55%+ WR, all profitable ─────────────────────────────────────
    "SMC_LONG":                    {"active": True,  "min_confidence": 0.65, "best_tf": "30m", "grade": "B", "wr": 61.7, "filters": [], "improvement_attempts": 0},
    "SMC_SHORT":                   {"active": True,  "min_confidence": 0.65, "best_tf": "30m", "grade": "B", "wr": 61.7, "filters": [], "improvement_attempts": 0},
    "SUPERTREND_LONG":             {"active": True,  "min_confidence": 0.63, "best_tf": "30m", "grade": "B", "wr": 60.6, "filters": [], "improvement_attempts": 0},
    "SUPERTREND_SHORT":            {"active": True,  "min_confidence": 0.63, "best_tf": "30m", "grade": "B", "wr": 60.6, "filters": [], "improvement_attempts": 0},
    "EMA_CROSS_LONG":              {"active": True,  "min_confidence": 0.63, "best_tf": "1h",  "grade": "B", "wr": 58.9, "filters": [], "improvement_attempts": 0},
    "EMA_CROSS_SHORT":             {"active": True,  "min_confidence": 0.63, "best_tf": "1h",  "grade": "B", "wr": 58.9, "filters": [], "improvement_attempts": 0},
    "ORB_LONG":                    {"active": True,  "min_confidence": 0.63, "best_tf": "1h",  "grade": "B", "wr": 59.4, "filters": [], "improvement_attempts": 0},
    "ORB_SHORT":                   {"active": True,  "min_confidence": 0.63, "best_tf": "1h",  "grade": "B", "wr": 59.4, "filters": [], "improvement_attempts": 0},
    "TREND_FOLLOW_LONG":           {"active": True,  "min_confidence": 0.62, "best_tf": "30m", "grade": "B", "wr": 57.6, "filters": [], "improvement_attempts": 0},
    "TREND_FOLLOW_SHORT":          {"active": True,  "min_confidence": 0.62, "best_tf": "30m", "grade": "B", "wr": 57.6, "filters": [], "improvement_attempts": 0},
    "INSIDE_BAR_LONG":             {"active": True,  "min_confidence": 0.62, "best_tf": "15m", "grade": "B", "wr": 58.1, "filters": [], "improvement_attempts": 0},
    "INSIDE_BAR_SHORT":            {"active": True,  "min_confidence": 0.62, "best_tf": "15m", "grade": "B", "wr": 58.1, "filters": [], "improvement_attempts": 0},
    "FVG_LONG":                    {"active": True,  "min_confidence": 0.62, "best_tf": "30m", "grade": "C", "wr": 57.9, "filters": [], "improvement_attempts": 0},
    "FVG_SHORT":                   {"active": True,  "min_confidence": 0.62, "best_tf": "30m", "grade": "C", "wr": 57.9, "filters": [], "improvement_attempts": 0},
    "MOMENTUM_LONG":               {"active": True,  "min_confidence": 0.62, "best_tf": "30m", "grade": "B", "wr": 56.1, "filters": [], "improvement_attempts": 0},
    "MOMENTUM_SHORT":              {"active": True,  "min_confidence": 0.62, "best_tf": "30m", "grade": "B", "wr": 56.1, "filters": [], "improvement_attempts": 0},
    "DONCHIAN_BREAK_LONG":         {"active": True,  "min_confidence": 0.62, "best_tf": "30m", "grade": "B", "wr": 55.6, "filters": [], "improvement_attempts": 0},
    "DONCHIAN_BREAK_SHORT":        {"active": True,  "min_confidence": 0.62, "best_tf": "30m", "grade": "B", "wr": 55.6, "filters": [], "improvement_attempts": 0},
    "MONTHLY_OPEN_LONG":           {"active": True,  "min_confidence": 0.62, "best_tf": "15m", "grade": "B", "wr": 55.1, "filters": [], "improvement_attempts": 0},
    "MONTHLY_OPEN_SHORT":          {"active": True,  "min_confidence": 0.62, "best_tf": "15m", "grade": "B", "wr": 55.1, "filters": [], "improvement_attempts": 0},

    # ── Inactive (benched — D/F class or not in final roster) ─────────────────
    "BOS_LONG":                    {"active": False, "min_confidence": 0.65, "best_tf": "15m", "grade": "C", "wr": 54.0, "filters": [], "improvement_attempts": 0},
    "BOS_SHORT":                   {"active": False, "min_confidence": 0.65, "best_tf": "15m", "grade": "C", "wr": 54.0, "filters": [], "improvement_attempts": 0},
    "SCALP_LONG":                  {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "grade": "C", "wr": 54.0, "filters": [], "improvement_attempts": 0},
    "SCALP_SHORT":                 {"active": False, "min_confidence": 0.65, "best_tf": "1h",  "grade": "C", "wr": 54.0, "filters": [], "improvement_attempts": 0},
    "MEAN_REVERSION_LONG":         {"active": False, "min_confidence": 0.65, "best_tf": "1d",  "grade": "B", "wr": 55.0, "filters": [], "improvement_attempts": 0},
    "MEAN_REVERSION_SHORT":        {"active": False, "min_confidence": 0.65, "best_tf": "1d",  "grade": "B", "wr": 55.0, "filters": [], "improvement_attempts": 0},
    "PREV_DAY_HL_LONG":            {"active": False, "min_confidence": 0.65, "best_tf": "4h",  "grade": "D", "wr": 42.1, "filters": [], "improvement_attempts": 0},
    "PREV_DAY_HL_SHORT":           {"active": False, "min_confidence": 0.65, "best_tf": "4h",  "grade": "D", "wr": 42.1, "filters": [], "improvement_attempts": 0},
    "BREAK_RETEST_LONG":           {"active": False, "min_confidence": 0.65, "best_tf": "5m",  "grade": "-", "wr": None,  "filters": [], "improvement_attempts": 0},
    "BREAK_RETEST_SHORT":          {"active": False, "min_confidence": 0.65, "best_tf": "5m",  "grade": "-", "wr": None,  "filters": [], "improvement_attempts": 0},
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
