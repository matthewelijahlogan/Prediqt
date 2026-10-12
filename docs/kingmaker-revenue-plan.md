# Prediqt: first revenue, then evidence-based scale

## Starting position, audited 2026-10-08

Kingmaker v1 is a price-feature Ridge forecaster. It uses three purged expanding
validation folds, compares prediction error with a no-change baseline, and records
first-seen forecasts. These are useful foundations, but do not establish tradable
net profit. Its confidence score is validation quality, not a probability of profit.

The scanner supports up to 20 symbols. Automation supports approved Alpaca paper
orders only. Forecast records default to local SQLite; proposal state is held in
memory. The Render blueprint disables the trainer scheduler and supplies no durable
ledger storage. Actual deployed configuration must be inspected before changing it.

Hourly and daily forecasts currently share a four-calendar-day freshness ceiling.
That is insufficient as an intraday execution gate. Signals use fixed move thresholds,
not an explicit expected-return calculation after spread, slippage, and trading costs.

## Objective

Build first revenue quickly, then scale only a measured, repeatable advantage.
Neither a profit deadline nor a promised income amount is justified by current evidence.

Pending user choices: trading versus research/product revenue, starting capital,
maximum acceptable dollar loss, and intended meaning of "fast". Until answered,
plan both revenue paths, retain paper execution, and do not choose live position sizes.

## Trading track: prove economics before increasing capital

1. Define one executable strategy, initially a liquid-stock/ETF daily-horizon
   candidate evaluated against hourly trading. Fix its instrument universe,
   signal threshold, next executable entry, exits, holding period, and sizing rules
   before evaluating the final holdout. This is a research starting point, not a
   recommendation to buy specific securities.
2. Add a portfolio backtest with chronological train/validation/final-test boundaries.
   Train each decision only on outcomes then available; use the next executable
   price rather than the bar that generated the prediction. Account for overlapping
   holdings, cash limits, spread, slippage, commissions/fees and corporate actions.
3. Report net P&L, drawdown, exposure, turnover, trade count, average win/loss,
   uncertainty, and benchmark performance. Forecast direction accuracy alone is
   insufficient. Compare with cash, a passive exposure-matched baseline, and a
   simple strategy appropriate to the same universe.
4. Forward-test frozen rules with timestamps and actual quotes/fills. Record missed
   and rejected trades as well as completed ones. Paper fills must be stressed for
   costs and latency; paper performance is not a live profit record.
5. Establish horizon-aware freshness and market-session checks, persistent orders,
   reconciliation, account-level exposure and dollar-loss limits, and a kill switch.
6. Consider a separately authorized small live pilot only after economic evidence
   and operational checks pass. Its size depends on the user's capital and loss
   budget. Scale in increments after observed live net performance, execution costs,
   drawdown, and liquidity justify each increase. Reduce exposure or stop when
   predefined limits fail; do not increase risk to meet an income deadline.

## Product track: validate paying demand while trading evidence develops

Offer a narrow research terminal: daily ranked watchlist, evidence behind each
forecast, data age, explicit HOLD cases, and an unedited outcome ledger. Label all
backtests and paper results accurately. Avoid profit promises or implying a quality
score is a probability of making money.

Before substantial feature work, validate one target customer and paid-pilot demand.
Set pricing from interviews and serving costs, not from hypothetical market size.
Confirm data redistribution rights and requirements applicable to the proposed
product before a public paid launch.

Measure first payment, repeat use, renewal/cancellation, conversion, serving cost,
and contribution margin. Expand only when paying users show that the offering is
useful. A subscription is a proposed revenue channel, not an established business.

## Implementation order

- First: durable forecast and proposal storage; audit actual deployed configuration.
- Second: reproducible after-cost portfolio evaluation and a profit-evidence API.
- Third: horizon/session-aware freshness, quotes, and forward paper execution ledger.
- Fourth: a focused dashboard and paid-pilot experiment, contingent on user direction.
- Fifth: independent review of evidence and separately authorized live pilot.

This document changes strategy direction only. No trades, live execution,
subscriptions, customer outreach, paid services, or deployments were initiated.

## Sources

- Current code: kingmaker/model.py, kingmaker/ledger.py,
  trainers/trainer_1_yfinance.py, backend/signals.py, backend/automation.py,
  backend/routers/kingmaker.py and render.yaml.
- Alpaca paper simulation limitations:
  https://docs.alpaca.markets/us/v1.4.2/docs/paper-trading
- SEC investor bulletin on costs reducing returns:
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/updated
