# ICT Trading Model

[![Tests](https://github.com/carreypro/ict-trading-model/actions/workflows/test.yml/badge.svg)](https://github.com/carreypro/ict-trading-model/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A Codex skill that combines multi-timeframe bias, liquidity mapping, premium/discount location, session context, displacement, market structure, and PD arrays into a strict ICT/SMC setup-validation framework. It supports chart screenshots, live candles, and OHLCV JSON across bullish, bearish, and no-trade scenarios. Every analysis returns one auditable status—`confirmed`, `developing`, `invalidated`, or `no-trade`—with the supporting evidence, exact trigger, structural invalidation, liquidity target, and estimated reward to risk.

Its core advantage is evidence-gated planning: an FVG, order block, or opposing candle cannot create a trade signal by itself. The complete sequence must be evaluated:

```text
Higher-timeframe bias
→ Liquidity objective
→ Premium / discount location
→ Liquidity sweep
→ Displacement and strict FVG
→ Close-confirmed MSS or BOS
→ Retracement into OB / FVG / Breaker / OTE
→ Invalidation and target
→ Risk-to-reward validation
```

The skill produces analysis and conditional trade plans only. It never executes orders.

## What It Delivers

| Capability | Output |
| --- | --- |
| Multi-timeframe context | Bias, dealing range, liquidity objective, and premium/discount location |
| Setup validation | Sweep, displacement, strict FVG, close-confirmed MSS/BOS, and retracement evidence |
| Execution planning | Exact trigger, structural invalidation, target liquidity, and reward to risk |
| Decision control | One status: `confirmed`, `developing`, `invalidated`, or `no-trade` |
| Auditability | Observed, derived, interpretive, and missing evidence kept separate |

## Installation

Install the skill directly from GitHub:

```bash
npx skills add https://github.com/carreypro/ict-trading-model --skill ict-trading-model
```

Invoke it explicitly in Codex:

```text
Use $ict-trading-model to analyze this chart.
```

It may also activate automatically when a request refers to ICT, SMC, liquidity sweeps, FVGs, order blocks, breakers, OTE, MSS, or BOS.

## Quick Start

### Review a chart screenshot

```text
Use $ict-trading-model to review this chart.

Reconstruct the setup in chronological order and identify:
- higher-timeframe bias;
- BSL and SSL;
- liquidity sweeps;
- displacement and strict FVGs;
- MSS or BOS;
- valid order blocks or breakers;
- entry conditions, invalidation, and targets;
- valid opportunities and false signals.
```

A screenshot supports visual analysis only. Any price level, candle boundary, or timestamp that cannot be read reliably must be marked `unverified`.

### Analyze a live market

```text
Use $ict-trading-model to analyze BTC-USDT-SWAP.

Bias timeframe: 4H
Structure timeframe: 15m
Execution timeframe: 5m

Return one status: confirmed, developing, invalidated, or no-trade.
List the evidence for every required condition. Do not execute a trade.
```

For live analysis, the agent should fetch current market data first and disclose the venue, data timestamp, and latest closed candle.

### Validate your own trade thesis

```text
I think price swept the previous high, formed a bearish MSS, and left a bearish FVG.

Use $ict-trading-model to verify the thesis strictly:
- Is the previous high valid liquidity?
- Was the move a sweep or an accepted breakout?
- Was there genuine bearish displacement?
- Was the MSS confirmed by a candle close?
- Does the FVG satisfy the three-candle definition?
- Did the proposed order block cause displacement and the structure break?
- Is the entry still available, or has price already moved too far?
```

The skill challenges the thesis against the evidence instead of forcing the chart to match it.

### Analyze an OHLCV file

```text
Use $ict-trading-model to analyze:
/absolute/path/to/candles.json

Scan both bullish and bearish structures and report the most recent candidates.
```

## Analysis Workflow

The skill follows the same nine-stage process for chart reviews, live markets, and historical OHLCV data.

### 1. Confirm the data context

Identify the instrument, venue, candle timeframe, intended holding period, data timestamp, and whether the active candle has closed. Example data and stale screenshots must never be presented as live market data.

### 2. Establish higher-timeframe bias

Determine higher-timeframe order flow, the active dealing range, and the primary external liquidity objective. The higher timeframe provides direction; it does not provide a precise entry by itself.

### 3. Build the liquidity map

Mark relevant liquidity and reference points:

- old highs and lows;
- equal highs and equal lows;
- previous day and previous week extremes;
- session highs and lows;
- internal swing points and imbalances.

### 4. Evaluate price location

Within a clearly defined dealing range, classify price as premium, equilibrium, or discount. Identify the next liquidity objective and any obstacle between current price and that objective.

Bearish setups are preferred in premium; bullish setups are preferred in discount.

### 5. Wait for a liquidity event

A bullish reversal model requires a valid sell-side liquidity sweep. A bearish reversal model requires a valid buy-side liquidity sweep. A break without rejection or displacement is not automatically a sweep.

### 6. Confirm displacement and structure

Valid displacement should show decisive expansion, meaningful candle bodies, a strong close, and a strict FVG.

- Use MSS to validate a potential reversal.
- Use BOS to validate continuation with the prevailing order flow.
- A wick through a swing is not a close-confirmed structure break.

### 7. Define the execution zone

Identify the order block that actually caused displacement and the structure break. Give the zone more weight when it overlaps with:

- a strict FVG;
- a breaker;
- the OTE retracement range;
- the correct premium or discount side of the dealing range.

OTE is the `0.62–0.79` retracement of the displacement leg. `0.705` is its midpoint, not a property of the order block itself.

### 8. Validate risk

Every plan must define:

- an exact trigger;
- structural invalidation;
- an opposing liquidity target;
- at least `1:2` estimated reward to risk before costs;
- time-based invalidation or a clear no-trade condition.

### 9. Return one decision status

| Status | Meaning |
| --- | --- |
| `confirmed` | Every required condition has been verified. |
| `developing` | The narrative is valid, but a required structure break, retracement, or confirmation is still missing. |
| `invalidated` | Price has breached the structural invalidation level. |
| `no-trade` | The entry is late, evidence conflicts, data is insufficient, or reward to risk is unacceptable. |

## Complete Usage Example

User prompt:

```text
Use $ict-trading-model to analyze the uploaded ETH 15-minute chart.

My thesis is that price swept the previous high and then broke the latest swing low.
Do not accept the thesis without verification. Check:

1. whether the previous high represents valid BSL;
2. whether the sweep produced bearish displacement and a strict bearish FVG;
3. whether a candle body closed below the swing low;
4. which bullish candle, if any, qualifies as the bearish order block;
5. whether the order block, FVG, and OTE overlap;
6. whether the setup is confirmed, developing, invalidated, or no-trade;
7. what must happen next if the setup is still developing.

Do not execute a trade.
```

Expected response shape:

```text
Status: developing
Direction: potential short

Verified:
- Liquidity above the previous high was reached and rejected.
- Downside expansion followed the rejection.

Not yet verified:
- The latest swing low was breached only by a wick, not by a candle close.
- Exact bearish FVG boundaries cannot be confirmed from the screenshot.

Required next steps:
- Wait for a 15-minute close below the swing low.
- Confirm that displacement creates a strict bearish FVG.
- Wait for price to retrace into a premium-side FVG or valid order block.

Invalidation:
- Price closes back above the sweep high.

Conclusion: the setup is not confirmed, and an early short is not justified.
```

The central rule is simple: missing evidence produces `developing` or `no-trade`, never an invented confirmation.

## Deterministic OHLCV Scanner

The included scanner provides repeatable mechanical detection for candle data:

```bash
python3 scripts/ict_scan.py \
  --input /absolute/path/to/candles.json \
  --direction auto \
  --swing-width 2 \
  --minimum-rr 2
```

It detects:

- swing highs and lows;
- strict bullish and bearish FVGs;
- BSL and SSL sweeps;
- displacement strength;
- close-confirmed structure breaks;
- dealing ranges and OTE overlap;
- retracement state;
- candidate targets and gross reward-to-risk ratios.

### Supported input formats

Object format:

```json
{
  "meta": {
    "instrument": "BTC-USDT-SWAP",
    "timeframe": "5m"
  },
  "candles": [
    {
      "timestamp": "2026-10-10T02:00:00Z",
      "open": 100,
      "high": 102,
      "low": 99,
      "close": 101,
      "volume": 1234
    }
  ]
}
```

Array format:

```json
[
  [1791597600000, 100, 102, 99, 101, 1234]
]
```

The scanner requires at least 10 candles. Reverse-chronological input is sorted automatically before analysis.

### Scanner output

The scanner returns a `mechanical_status` with the detected evidence and candidate setup. This is not the final trading decision. Higher-timeframe context, the quality of the liquidity pool, event risk, and actual execution costs still require human or agent review.

## Repository Structure

```text
ict-trading-model/
├── SKILL.md                       # Skill instructions and decision process
├── agents/openai.yaml             # Agent metadata
├── references/ict-model.md        # ICT/SMC definitions and validation rules
├── references/output-contract.md  # Required analysis output format
├── scripts/ict_scan.py            # Deterministic OHLCV scanner
└── tests/test_ict_scan.py         # Scanner test suite
```

## Limitations and Risk Notice

- ICT/SMC labels are a price-action framework, not direct proof of institutional activity.
- A screenshot cannot replace complete OHLCV data.
- The scanner reports gross reward to risk and does not include fees, spread, slippage, or funding.
- Inverse contracts, options, and non-linear instruments require instrument-specific sizing and risk calculations.
- Market structure is probabilistic. A technically valid setup can still fail.
- This project is for education and research and is not financial advice.

## Development and Testing

Run the test suite and syntax check from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/ict_scan.py
```

## License

Released under the [MIT License](LICENSE).
