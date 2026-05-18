"""
Profit projection based on backtest metrics.
WR=72.1%, PF=2.92, ~5 signals/day (conservative live estimate).
"""

WR   = 0.721
PF   = 2.92
RR   = 1.13           # W/L ratio derived from PF
EV   = WR * RR - (1 - WR)   # expected value per unit risked = 0.536

RISK_PCT = 0.01        # risk 1% of account per trade
TRADES   = 5           # realistic live signals per day

EV_PER_TRADE = EV * RISK_PCT
DAILY_RAW    = EV_PER_TRADE * TRADES  # theoretical max per day

# Reality discount: live trading has slippage, commissions, missed signals,
# and live WR is typically 5-10% lower than backtest.
CONSERVATIVE = DAILY_RAW * 0.35
MODERATE     = DAILY_RAW * 0.55
OPTIMISTIC   = DAILY_RAW * 0.75

periods = [
    ("Daily",    1),
    ("2 Weeks",  10),
    ("Monthly",  21),
    ("6 Months", 126),
    ("1 Year",   252),
]

print()
print("=" * 78)
print("  PROJECTED RETURNS  --  72.1% WR | PF 2.92 | ~5 trades/day")
print("=" * 78)
print()
print("  Assumptions:")
print("    Risk per trade  : 1% of account")
print("    Trades per day  : ~5 live signals (conservative)")
print("    Expected value  : {:.2f}% of account per trade".format(EV_PER_TRADE * 100))
print("    Discount applied: slippage, commissions, live vs backtest gap")
print()
print("  Scenarios:")
print("    Conservative ({:.2f}%/day) -- safe estimate, bad days included".format(CONSERVATIVE*100))
print("    Moderate     ({:.2f}%/day) -- realistic for a well-run bot".format(MODERATE*100))
print("    Optimistic   ({:.2f}%/day) -- everything clicking".format(OPTIMISTIC*100))
print()

for capital in [100, 1_000, 10_000]:
    print("-" * 78)
    print("  STARTING CAPITAL: ${:,}".format(capital))
    if capital < 1000:
        print("  !! PAPER TRADING ONLY -- Real futures require ~$500+ margin per contract.")
        print("     Use $100 to practice. Build to $5,000+ before going live.")
    elif capital < 5000:
        print("  ** $1,000 = 1 MES micro contract possible (~$500 margin) but very tight.")
        print("     Recommended: paper trade until you have $5,000+.")
    else:
        print("  OK -- $10,000 is a solid start. Trade 1-2 MES/MNQ micro contracts.")
    print()
    print("  {:<12}  {:>14}  {:>14}  {:>14}".format(
          "Period", "Conservative", "Moderate", "Optimistic"))
    print("  " + "-" * 60)

    for label, days in periods:
        c = capital * ((1 + CONSERVATIVE) ** days) - capital
        m = capital * ((1 + MODERATE)     ** days) - capital
        o = capital * ((1 + OPTIMISTIC)   ** days) - capital
        print("  {:<12}  {:>+13,.2f}  {:>+13,.2f}  {:>+13,.2f}".format(
              label, c, m, o))
    print()

print("=" * 78)
print("  1-YEAR RETURN %  (compounded daily)")
print("=" * 78)
print()
print("  {:<14}  {:>14}  {:>14}  {:>14}".format(
      "Capital", "Conservative", "Moderate", "Optimistic"))
print("  " + "-" * 62)
for capital in [100, 1_000, 10_000]:
    yc = (capital * (1+CONSERVATIVE)**252 - capital) / capital * 100
    ym = (capital * (1+MODERATE)**252     - capital) / capital * 100
    yo = (capital * (1+OPTIMISTIC)**252   - capital) / capital * 100
    print("  ${:<13,}  {:>+13.0f}%  {:>+13.0f}%  {:>+13.0f}%".format(
          capital, yc, ym, yo))

print()
print("  IMPORTANT CAVEATS:")
print("  1. These are projections, not guarantees. Markets change.")
print("  2. Live WR will likely be 62-67% (not 72.1%) due to real-world conditions.")
print("  3. Drawdowns of 10-20% are normal even at 72% WR -- emotionally prepare.")
print("  4. Compound returns assume you re-invest ALL profits -- hard to maintain.")
print("  5. Do NOT trade real money until you have at least 30 days paper trading.")
print("  6. $100 is practice money. $10,000 is the real starting point.")
print()
