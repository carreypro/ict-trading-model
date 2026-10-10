# Output contract

Use this structure for validation and plan requests. Keep fields with missing
data and mark them `unverified`; do not omit inconvenient gaps.

## Decision

- Status: `confirmed | developing | invalidated | no-trade`
- Direction: `long | short | neutral`
- Instrument / venue / query time
- HTF, context, and execution timeframes
- One-sentence reason for the status

## Evidence ledger

| Layer | Observation | Candle time / price | Classification |
|---|---|---|---|
| HTF bias | ... | ... | observed / derived / interpretive / missing |
| Liquidity draw | ... | ... | ... |
| Sweep | ... | ... | ... |
| Displacement + FVG | ... | ... | ... |
| MSS | ... | ... | ... |
| Location | premium / equilibrium / discount | ... | ... |
| Session / events | ... | America/New_York | ... |

## Strict gate

```text
[pass/fail/unverified] HTF narrative
[pass/fail/unverified] meaningful sweep
[pass/fail/unverified] displacement + strict FVG
[pass/fail/unverified] closed-candle MSS
[pass/fail/unverified] correct dealing-range side
[pass/fail/unverified] retrace + net R:R >= 2
```

One failed required gate prevents `confirmed`.

## Conditional plan

- Trigger: exact closed-candle or retest condition
- Entry zone: FVG/OB/Breaker boundaries and CE/MT if used
- Structural invalidation: exact level and why the thesis fails there
- Target 1: nearest opposing/internal liquidity
- Target 2: external liquidity or HTF PD array
- Gross and estimated net R:R
- Time stop or session expiry
- No-trade condition

If account sizing is requested, collect equity, maximum account loss, fee,
slippage, and contract-unit inputs. Position size follows the structural stop;
the stop must not be moved to fit a desired size.

## Missing-data block

List absent HTF candles, session data, event calendar, spread, fees, contract
specification, or cross-market confirmation. Explain which conclusion each
missing field prevents.

## Risk notice

State that ICT/SMC labels are interpretive price-action hypotheses, not proof of
institutional activity or a guarantee of performance. The output is educational
analysis and not investment advice.
