# ICT model rules

Read this reference for concept definitions, chart annotation, or manual review
of the scanner output.

## Evidence hierarchy

Use the hierarchy in order. Lower layers cannot repair a missing higher layer.

1. **Narrative**: HTF order flow and the next external liquidity objective.
2. **Location**: premium/discount inside a defined dealing range and a relevant
   PD array.
3. **Time**: a session window in `America/New_York` and absence of disqualifying
   event risk.
4. **Confirmation**: sweep, displacement, and MSS on closed candles.
5. **Execution**: retrace, invalidation, opposing-liquidity target, and R:R.

## Liquidity map

- Buyside liquidity (BSL): stop and breakout orders expected above visible
  highs.
- Sellside liquidity (SSL): stop and breakout orders expected below visible
  lows.
- External liquidity: boundaries of the active dealing range, old highs/lows,
  equal highs/lows, and prior day/week/session extremes.
- Internal liquidity: swing points, FVGs, and other imbalances inside the range.

A sweep requires penetration and rejection. For a bullish SSL raid, price trades
below the reference low and closes back above it. A candle that closes below the
level is a break until later evidence proves otherwise. Apply the mirror rule to
a bearish BSL raid.

Equal highs/lows are liquidity candidates, not promises that price must visit
them. State the level and why it is meaningful.

## Swing and market structure

A swing high has lower highs on both sides; a swing low has higher lows on both
sides. The pivot width must match the execution timeframe and should be stated.

- BOS normally confirms continuation in the current structural direction.
- MSS is the first meaningful closed-candle break against the prior short-term
  structure after a liquidity event and displacement.
- A wick through the protected swing is not a confirmed MSS.

Do not use CHoCH, MSS, and BOS as interchangeable labels. When the data cannot
distinguish them, say `structure break` and describe the candle evidence.

## Displacement

Displacement is expansion, not merely direction. Seek several aligned clues:

- real body materially larger than its recent median;
- range at least comparable to recent ATR;
- decisive close away from the origin;
- strict FVG created by the move;
- opposing swing closed through.

The scanner uses configurable body and ATR thresholds. These thresholds make
the rule reproducible; they do not prove institutional activity.

## FVG and inversion

For candles A, B, C in chronological order:

- bullish FVG: `A.high < C.low`; zone is `[A.high, C.low]`;
- bearish FVG: `A.low > C.high`; zone is `[C.high, A.low]`;
- consequent encroachment (CE): zone midpoint.

Any overlap between A and C wicks fails the strict definition. Track whether a
later candle touches, partially fills, fully fills, or closes through the zone.
Only a displacement close through plus a later opposite-side retest supports
an IFVG label.

## Dealing range, premium, discount, and OTE

Use a named structural low and high to define the range:

- equilibrium = 50%;
- discount = below equilibrium;
- premium = above equilibrium.

For a bullish impulse from low to high, the OTE retracement band is the price
area reached after a 0.62-0.79 pullback from the high, centered at 0.705. For a
bearish impulse, mirror from high to low. The impulse anchors must be printed in
the result. OTE without a liquidity narrative and confirmation is not a setup.

## Order block

A candidate OB is the final opposite candle before the displacement leg. It is
valid only if the leg creates imbalance and breaks relevant structure. Record:

- candle time and full high-low range;
- body range and 50% mean threshold;
- the displaced swing and associated FVG;
- whether a later close invalidated the block.

Use full range for conservative invalidation. Body or mean-threshold entries
are refinements and must be labeled as such.

## Breaker block

A breaker needs this sequence:

1. a prior OB or structural block;
2. a liquidity sweep in its original direction;
3. failure and a decisive close through the block;
4. a retest from the opposite side.

Without the sequence, call the area a support/resistance flip, not a breaker.

## Strict ICT setup state machine

For a bullish setup; mirror for bearish:

```text
HTF bullish narrative
  -> meaningful SSL sweep
  -> bullish displacement creates FVG
  -> closed-candle MSS above opposing swing
  -> FVG/OB/Breaker is in discount or at equilibrium
  -> retrace respects the PD array
  -> target BSL offers net R:R >= 2
```

State transitions:

- before sweep: `waiting_for_liquidity`;
- after sweep, before displacement: `swept_unconfirmed`;
- after displacement, before MSS: `displaced_waiting_mss`;
- after MSS, before retrace: `developing_waiting_retrace`;
- after valid retrace: `confirmed`;
- structural stop crossed: `invalidated`;
- target reached before retrace or setup becomes too late: `no-trade`.

## No-trade rules

Use no-trade when any of these applies:

- HTF bias and intended direction conflict without a reversal confirmation;
- the sweep reference is trivial or cannot be identified;
- no displacement/FVG or no closed-candle MSS;
- entry PD array is on the wrong side of equilibrium;
- target liquidity is already taken;
- net R:R is under 2;
- spread, fees, event risk, or candle freshness is unknown and material;
- the only evidence is a named pattern without sequence and context.
