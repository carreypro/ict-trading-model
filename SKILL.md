---
name: ict-trading-model
description: >-
  Analyze liquid markets with a strict ICT/SMC framework that combines
  multi-timeframe bias, liquidity sweeps, displacement, close-confirmed
  MSS/BOS, FVG/OB/Breaker/OTE retracements, premium-discount location, session
  timing, invalidation, targets, and risk-to-reward. Use for ICT chart reviews,
  live-market analysis, OHLCV scans, or validating a user's trade thesis.
  Return an auditable setup status and conditional plan; do not use for generic
  indicator analysis, order execution, or claims of proven institutional intent.
---

# ICT Trading Model

Turn ICT vocabulary into a falsifiable, candle-by-candle model. Treat ICT/SMC
as a price-action framework, not a proven description of hidden institutional
orders. Label observations, interpretations, and unknowns separately.

This skill is analysis-only. Never place or modify an order unless the user
separately invokes an execution skill and explicitly authorizes that action.

## Modes

- **Explain**: define an ICT concept and show its bullish/bearish mirror.
- **Map**: mark HTF bias, dealing range, external/internal liquidity, PD arrays,
  and active session on supplied or live candles.
- **Validate**: test whether a claimed ICT setup meets every required gate.
- **Plan**: after validation, produce a conditional entry, invalidation, target,
  R:R, and no-trade condition. Account sizing requires explicit risk inputs.

For concept definitions or manual chart annotation, read
[references/ict-model.md](references/ict-model.md). For a plan, also read
[references/output-contract.md](references/output-contract.md).

## 1. Establish data and clock

Confirm instrument, venue, candle source, holding horizon, and execution
timeframe. For a live request, fetch fresh candles and state the query time.
Never reuse a fixture, screenshot estimate, or cached price as current market
data.

Use closed candles for confirmation. Report an open candle separately. Convert
session timestamps with the IANA zone `America/New_York`; do not hard-code UTC
offsets because daylight-saving time changes them.

Default timeframe stacks:

| Style | Bias | Context | Execution |
|---|---|---|---|
| Intraday | 4H or 1H | 15m | 5m or 1m |
| Swing | 1D | 4H | 1H or 15m |
| Position | 1W | 1D | 4H |

The highest timeframe sets the working bias, the middle timeframe maps the
dealing range and liquidity, and the lowest timeframe supplies the trigger.
When timeframes conflict, the result is developing or no-trade, not a forced
signal.

## 2. Build the narrative before the trigger

Map, in this order:

1. HTF order flow and the current dealing range;
2. external liquidity: old highs/lows, equal highs/lows, prior day/week highs
   and lows, and session boundaries;
3. internal liquidity and imbalances inside the range;
4. premium, equilibrium, and discount;
5. the next plausible liquidity draw and obstacles on the path;
6. active New York-time session and nearby high-impact events.

Do not start with a low-timeframe FVG and invent the narrative afterward.

## 3. Apply the strict ICT setup gate

A confirmed setup needs all six gates. For a bullish setup; mirror every rule
for bearish:

1. **Sell-side liquidity sweep**: price trades below a meaningful prior low and
   rejects back above it. A simple breakout close below is not a bullish sweep.
2. **Bullish displacement**: decisive expansion away from the sweep, with a
   large real body and a bullish FVG. A small bounce is insufficient.
3. **MSS**: a closed candle breaks the relevant opposing swing high. A wick
   through the level is not enough.
4. **Dealing-range location**: define the displacement range from the swept
   extreme to the MSS leg high; the entry PD array must be at equilibrium or in
   discount for a long, premium for a short.
5. **Retrace into a valid PD array**: prefer the displacement FVG; OB, breaker,
   or OTE may add confluence but cannot replace sweep + displacement + MSS.
6. **Executable risk**: stop beyond the sweep/structural invalidation, target
   opposing liquidity, and net R:R of at least 1:2 after costs.

Use `scripts/ict_scan.py` on OHLCV JSON to detect swing points, strict FVGs,
liquidity sweeps, displacement, MSS, OTE overlap, retest state, and candidate
R:R. The script is a consistency checker; visually verify meaningful levels
and HTF context before accepting its output. Its `mechanical_status` is not the
final skill status until the narrative, location, time, and data quality are
manually verified.

## 4. Validate PD arrays precisely

- **FVG**: a three-candle non-overlap. Bullish when candle 1 high is below
  candle 3 low; bearish when candle 1 low is above candle 3 high. Any wick
  overlap means no strict FVG.
- **OB**: the final opposite candle before displacement that causes structure
  to break. Do not label every opposite candle an order block.
- **Breaker**: a failed order block after a liquidity event, closed through and
  then retested from the other side. A generic support/resistance flip is not
  enough.
- **OTE**: the 0.62-0.79 retracement of a defined impulse, with 0.705 as the
  center. OTE is confluence, not a standalone entry.
- **IFVG**: an FVG closed through with displacement and later respected from the
  opposite side. A wick through alone does not invert it.

When a concept cannot be proven from the available candles, mark it
`unverified`; never upgrade it because the trade idea looks attractive.

## 5. Respect time and event filters

Express all windows in New York time and state the date:

- London focus: 02:00-05:00;
- New York opening focus: 07:00-10:00;
- Silver Bullet focus: 10:00-11:00;
- lunch 12:00-13:30 is normally no-trade;
- afternoon 13:30-16:00 is conditional on a clear trend-day narrative.

Time is a filter, not proof. A setup outside the preferred windows can be
reported, but confidence is lower. If high-impact news is imminent or its
schedule is unavailable, state the uncertainty and do not call the setup
high-confidence.

## 6. Classify, do not overclaim

Return exactly one status:

- `confirmed`: every gate is evidenced on closed candles and R:R passes;
- `developing`: the narrative is valid but a required gate or retrace is still
  pending;
- `invalidated`: price has crossed the structural invalidation or contradicted
  the HTF premise;
- `no-trade`: evidence is conflicting, late, stale, incomplete, or below the
  minimum R:R.

If the user requests a direction that contradicts the evidence, show the
conflict and the condition that would restore that direction. Do not force a
matching plan.

## 7. Present auditable evidence

Include candle timestamps and prices for the sweep, displacement/FVG, MSS,
retrace, invalidation, and target. Separate:

- **observed**: directly present in candles or market data;
- **derived**: swing, FVG, range midpoint, OTE, R:R;
- **interpretive**: bias, narrative, and likely liquidity draw;
- **missing**: unavailable HTF, session, news, spread, or fee inputs.

End with a short educational-risk notice. ICT labels are hypotheses and do not
guarantee price behavior or institutional participation.
