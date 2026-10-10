#!/usr/bin/env python3
"""Scan OHLCV candles for strict ICT setup evidence.

Input accepts either a JSON candle array or {"candles": [...], "meta": {...}}.
Candles may be objects with timestamp/open/high/low/close/volume fields or OKX-
style arrays [timestamp, open, high, low, close, volume, ...].
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


NY = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def span(self) -> float:
        return self.high - self.low

    @property
    def bullish(self) -> bool:
        return self.close > self.open

    @property
    def bearish(self) -> bool:
        return self.close < self.open


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000.0
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if text.replace(".", "", 1).isdigit():
            return _parse_timestamp(float(text))
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    raise ValueError(f"unsupported timestamp: {value!r}")


def _float(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc


def parse_candles(payload: Any) -> tuple[list[Candle], dict[str, Any]]:
    if isinstance(payload, dict):
        rows = payload.get("candles")
        meta = payload.get("meta", {})
    else:
        rows = payload
        meta = {}
    if not isinstance(rows, list) or len(rows) < 10:
        raise ValueError("at least 10 candles are required")
    if not isinstance(meta, dict):
        raise ValueError("meta must be an object")

    candles: list[Candle] = []
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            timestamp = row.get("timestamp", row.get("ts", row.get("time")))
            values = (
                row.get("open", row.get("o")),
                row.get("high", row.get("h")),
                row.get("low", row.get("l")),
                row.get("close", row.get("c")),
            )
            volume_raw = row.get("volume", row.get("vol", row.get("v")))
        elif isinstance(row, (list, tuple)) and len(row) >= 5:
            timestamp = row[0]
            values = row[1:5]
            volume_raw = row[5] if len(row) > 5 else None
        else:
            raise ValueError(f"candle {index} has an unsupported shape")

        candle = Candle(
            timestamp=_parse_timestamp(timestamp),
            open=_float(values[0], f"candle {index} open"),
            high=_float(values[1], f"candle {index} high"),
            low=_float(values[2], f"candle {index} low"),
            close=_float(values[3], f"candle {index} close"),
            volume=_float(volume_raw, f"candle {index} volume") if volume_raw is not None else None,
        )
        if candle.low > min(candle.open, candle.close) or candle.high < max(candle.open, candle.close):
            raise ValueError(f"candle {index} OHLC values are inconsistent")
        if candle.high < candle.low:
            raise ValueError(f"candle {index} high is below low")
        candles.append(candle)

    candles.sort(key=lambda candle: candle.timestamp)
    if len({c.timestamp for c in candles}) != len(candles):
        raise ValueError("candle timestamps must be unique")
    return candles, meta


def iso(candle: Candle) -> str:
    return candle.timestamp.isoformat().replace("+00:00", "Z")


def detect_swings(candles: list[Candle], width: int) -> list[dict[str, Any]]:
    if width < 1:
        raise ValueError("swing width must be at least 1")
    swings: list[dict[str, Any]] = []
    for index in range(width, len(candles) - width):
        candle = candles[index]
        left = candles[index - width:index]
        right = candles[index + 1:index + width + 1]
        if all(candle.high > other.high for other in left + right):
            swings.append({"kind": "high", "index": index, "price": candle.high, "time": iso(candle)})
        if all(candle.low < other.low for other in left + right):
            swings.append({"kind": "low", "index": index, "price": candle.low, "time": iso(candle)})
    return swings


def detect_fvgs(candles: list[Candle]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for end in range(2, len(candles)):
        first = candles[end - 2]
        third = candles[end]
        if first.high < third.low:
            lower, upper, direction = first.high, third.low, "bullish"
        elif first.low > third.high:
            lower, upper, direction = third.high, first.low, "bearish"
        else:
            continue
        gaps.append(
            {
                "direction": direction,
                "start_index": end - 2,
                "middle_index": end - 1,
                "end_index": end,
                "time": iso(candles[end - 1]),
                "zone": [lower, upper],
                "ce": (lower + upper) / 2.0,
                "size": upper - lower,
            }
        )
    return gaps


def atr_at(candles: list[Candle], index: int, period: int) -> float | None:
    start = max(1, index - period + 1)
    values = []
    for position in range(start, index + 1):
        candle = candles[position]
        previous = candles[position - 1]
        values.append(
            max(
                candle.high - candle.low,
                abs(candle.high - previous.close),
                abs(candle.low - previous.close),
            )
        )
    return sum(values) / len(values) if values else None


def _median_body_before(candles: list[Candle], index: int, window: int = 20) -> float:
    bodies = [c.body for c in candles[max(0, index - window):index]]
    nonzero = [body for body in bodies if body > 0]
    return statistics.median(nonzero) if nonzero else 0.0


def _session_name(moment: datetime) -> str:
    local = moment.astimezone(NY)
    minute = local.hour * 60 + local.minute
    if 120 <= minute < 300:
        return "london_focus"
    if 420 <= minute < 600:
        return "new_york_open"
    if 600 <= minute < 660:
        return "silver_bullet"
    if 720 <= minute < 810:
        return "lunch_no_trade"
    if 810 <= minute < 960:
        return "afternoon_conditional"
    return "outside_preferred_window"


def detect_sweeps(
    candles: list[Candle],
    swings: list[dict[str, Any]],
    lookback: int,
) -> list[dict[str, Any]]:
    sweeps: list[dict[str, Any]] = []
    for index, candle in enumerate(candles):
        prior = [s for s in swings if 0 < index - s["index"] <= lookback]
        prior_lows = [s for s in prior if s["kind"] == "low"]
        prior_highs = [s for s in prior if s["kind"] == "high"]
        if prior_lows:
            reference = max(prior_lows, key=lambda item: item["index"])
            if candle.low < reference["price"] and candle.close > reference["price"]:
                sweeps.append(
                    {
                        "direction": "long",
                        "kind": "sellside_sweep",
                        "index": index,
                        "time": iso(candle),
                        "ny_time": candle.timestamp.astimezone(NY).isoformat(),
                        "session": _session_name(candle.timestamp),
                        "extreme": candle.low,
                        "reference": reference,
                    }
                )
        if prior_highs:
            reference = max(prior_highs, key=lambda item: item["index"])
            if candle.high > reference["price"] and candle.close < reference["price"]:
                sweeps.append(
                    {
                        "direction": "short",
                        "kind": "buyside_sweep",
                        "index": index,
                        "time": iso(candle),
                        "ny_time": candle.timestamp.astimezone(NY).isoformat(),
                        "session": _session_name(candle.timestamp),
                        "extreme": candle.high,
                        "reference": reference,
                    }
                )
    return sweeps


def _latest_swing(
    swings: Iterable[dict[str, Any]], kind: str, before_index: int
) -> dict[str, Any] | None:
    choices = [s for s in swings if s["kind"] == kind and s["index"] < before_index]
    return max(choices, key=lambda item: item["index"]) if choices else None


def _candidate_target(
    swings: list[dict[str, Any]], direction: str, before_index: int, threshold: float
) -> dict[str, Any] | None:
    prior = [s for s in swings if s["index"] < before_index]
    if direction == "long":
        choices = [s for s in prior if s["kind"] == "high" and s["price"] > threshold]
        return min(choices, key=lambda item: item["price"]) if choices else None
    choices = [s for s in prior if s["kind"] == "low" and s["price"] < threshold]
    return max(choices, key=lambda item: item["price"]) if choices else None


def build_candidate(
    candles: list[Candle],
    swings: list[dict[str, Any]],
    fvgs: list[dict[str, Any]],
    sweep: dict[str, Any],
    *,
    lookahead: int,
    atr_period: int,
    displacement_body_multiple: float,
    displacement_atr_multiple: float,
    minimum_rr: float,
) -> dict[str, Any]:
    direction = sweep["direction"]
    sweep_index = sweep["index"]
    opposite_kind = "high" if direction == "long" else "low"
    mss_reference = _latest_swing(swings, opposite_kind, sweep_index)
    end = min(len(candles) - 1, sweep_index + lookahead)

    mss_index = None
    if mss_reference:
        for index in range(sweep_index + 1, end + 1):
            close = candles[index].close
            crossed = close > mss_reference["price"] if direction == "long" else close < mss_reference["price"]
            if crossed:
                mss_index = index
                break

    matching_fvgs = []
    desired = "bullish" if direction == "long" else "bearish"
    for gap in fvgs:
        if gap["direction"] != desired:
            continue
        if gap["middle_index"] < sweep_index or gap["end_index"] > end:
            continue
        middle = candles[gap["middle_index"]]
        median_body = _median_body_before(candles, gap["middle_index"])
        atr = atr_at(candles, gap["middle_index"], atr_period)
        body_ok = median_body > 0 and middle.body >= median_body * displacement_body_multiple
        atr_ok = atr is not None and middle.span >= atr * displacement_atr_multiple
        direction_ok = middle.bullish if direction == "long" else middle.bearish
        if body_ok and atr_ok and direction_ok:
            matching_fvgs.append({**gap, "body_multiple": middle.body / median_body, "range_atr": middle.span / atr})

    fvg = min(matching_fvgs, key=lambda item: item["end_index"]) if matching_fvgs else None
    range_end = mss_index if mss_index is not None else (fvg["end_index"] if fvg else sweep_index)
    segment = candles[sweep_index:range_end + 1]
    range_low = min(c.low for c in segment)
    range_high = max(c.high for c in segment)
    equilibrium = (range_low + range_high) / 2.0

    if direction == "long":
        ote = [range_high - 0.79 * (range_high - range_low), range_high - 0.62 * (range_high - range_low)]
    else:
        ote = [range_low + 0.62 * (range_high - range_low), range_low + 0.79 * (range_high - range_low)]

    location_ok = None
    entry = None
    if fvg:
        entry = fvg["ce"]
        location_ok = entry <= equilibrium if direction == "long" else entry >= equilibrium
    ote_overlap = None
    if fvg:
        ote_overlap = max(fvg["zone"][0], ote[0]) <= min(fvg["zone"][1], ote[1])

    target_threshold = range_high if direction == "long" else range_low
    target = _candidate_target(swings, direction, sweep_index, target_threshold) if entry is not None else None
    stop = sweep["extreme"]
    rr = None
    if entry is not None and target:
        risk = abs(entry - stop)
        reward = target["price"] - entry if direction == "long" else entry - target["price"]
        if risk > 0:
            rr = reward / risk

    retest_index = None
    invalidation_index = None
    target_before_retest = False
    start_check = max(
        sweep_index + 1,
        (mss_index + 1) if mss_index is not None else sweep_index + 1,
        (fvg["end_index"] + 1) if fvg else sweep_index + 1,
    )
    if fvg:
        for index in range(start_check, len(candles)):
            candle = candles[index]
            invalidated = candle.low < stop if direction == "long" else candle.high > stop
            target_hit = False
            if target:
                target_hit = candle.high >= target["price"] if direction == "long" else candle.low <= target["price"]
            touched = candle.low <= fvg["zone"][1] and candle.high >= fvg["zone"][0]
            if invalidated:
                invalidation_index = index
                break
            if target_hit and not touched:
                target_before_retest = True
                break
            if touched:
                retest_index = index
                break

    checks = {
        "meaningful_sweep": True,
        "displacement_and_strict_fvg": fvg is not None,
        "closed_candle_mss": mss_index is not None,
        "correct_premium_discount_side": location_ok,
        "retrace_observed": retest_index is not None,
        "minimum_rr": rr is not None and rr >= minimum_rr,
    }

    if invalidation_index is not None:
        mechanical_status = "invalidated"
        reason = "structural sweep extreme was crossed before a valid retest"
    elif target_before_retest:
        mechanical_status = "no-trade"
        reason = "candidate target was reached before the retrace; entry is late"
    elif location_ok is False:
        mechanical_status = "no-trade"
        reason = "entry FVG is on the wrong side of equilibrium"
    elif rr is not None and rr < minimum_rr:
        mechanical_status = "no-trade"
        reason = f"candidate R:R {rr:.2f} is below {minimum_rr:.2f}"
    elif all(checks.values()):
        mechanical_status = "confirmed"
        reason = "all mechanical ICT setup gates passed on closed candles"
    else:
        mechanical_status = "developing"
        missing = [name for name, value in checks.items() if value is not True]
        reason = "waiting for: " + ", ".join(missing)

    return {
        "mechanical_status": mechanical_status,
        "final_status_requires_manual_context": True,
        "reason": reason,
        "direction": direction,
        "sweep": sweep,
        "displacement_fvg": fvg,
        "mss": {
            "reference": mss_reference,
            "break_index": mss_index,
            "break_time": iso(candles[mss_index]) if mss_index is not None else None,
            "break_close": candles[mss_index].close if mss_index is not None else None,
        },
        "dealing_range": {
            "low": range_low,
            "high": range_high,
            "equilibrium": equilibrium,
            "ote_zone": ote,
            "fvg_ote_overlap": ote_overlap,
        },
        "entry": {
            "zone": fvg["zone"] if fvg else None,
            "ce": entry,
            "retest_index": retest_index,
            "retest_time": iso(candles[retest_index]) if retest_index is not None else None,
        },
        "invalidation": {
            "structural_level": stop,
            "instruction": "place any operational buffer beyond this level using venue tick/volatility data",
            "crossed_index": invalidation_index,
            "crossed_time": iso(candles[invalidation_index]) if invalidation_index is not None else None,
        },
        "target": target,
        "gross_rr_to_candidate_target": rr,
        "minimum_rr": minimum_rr,
        "checks": checks,
    }


def scan(
    candles: list[Candle],
    meta: dict[str, Any],
    *,
    swing_width: int = 2,
    sweep_lookback: int = 80,
    setup_lookahead: int = 12,
    atr_period: int = 14,
    displacement_body_multiple: float = 1.5,
    displacement_atr_multiple: float = 1.0,
    minimum_rr: float = 2.0,
    direction: str = "auto",
) -> dict[str, Any]:
    if direction not in {"auto", "long", "short"}:
        raise ValueError("direction must be auto, long, or short")
    swings = detect_swings(candles, swing_width)
    fvgs = detect_fvgs(candles)
    sweeps = detect_sweeps(candles, swings, sweep_lookback)
    if direction != "auto":
        sweeps = [sweep for sweep in sweeps if sweep["direction"] == direction]

    candidates = [
        build_candidate(
            candles,
            swings,
            fvgs,
            sweep,
            lookahead=setup_lookahead,
            atr_period=atr_period,
            displacement_body_multiple=displacement_body_multiple,
            displacement_atr_multiple=displacement_atr_multiple,
            minimum_rr=minimum_rr,
        )
        for sweep in sweeps
    ]
    candidates.sort(key=lambda item: item["sweep"]["index"])

    return {
        "meta": {
            **meta,
            "candle_count": len(candles),
            "first_candle": iso(candles[0]),
            "last_candle": iso(candles[-1]),
            "timezone_for_sessions": "America/New_York",
        },
        "parameters": {
            "swing_width": swing_width,
            "sweep_lookback": sweep_lookback,
            "setup_lookahead": setup_lookahead,
            "atr_period": atr_period,
            "displacement_body_multiple": displacement_body_multiple,
            "displacement_atr_multiple": displacement_atr_multiple,
            "minimum_rr": minimum_rr,
            "direction": direction,
        },
        "counts": {
            "swings": len(swings),
            "strict_fvgs": len(fvgs),
            "liquidity_sweeps": len(sweeps),
            "candidates": len(candidates),
        },
        "latest_candidate": candidates[-1] if candidates else None,
        "candidates": candidates[-20:],
        "recent_swings": swings[-30:],
        "recent_fvgs": fvgs[-30:],
        "warnings": [
            "Mechanical detections require manual HTF narrative and meaningful-level validation.",
            "A mechanical confirmed result is not a final confirmed trade setup until context is verified.",
            "R:R is gross and excludes fees, spread, slippage, and contract specifications.",
            "ICT labels are price-action hypotheses, not proof of institutional activity.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON path, or - for stdin")
    parser.add_argument("--output", help="Optional output JSON path")
    parser.add_argument("--direction", choices=("auto", "long", "short"), default="auto")
    parser.add_argument("--swing-width", type=int, default=2)
    parser.add_argument("--sweep-lookback", type=int, default=80)
    parser.add_argument("--setup-lookahead", type=int, default=12)
    parser.add_argument("--atr-period", type=int, default=14)
    parser.add_argument("--body-multiple", type=float, default=1.5)
    parser.add_argument("--atr-multiple", type=float, default=1.0)
    parser.add_argument("--minimum-rr", type=float, default=2.0)
    args = parser.parse_args()

    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        candles, meta = parse_candles(json.loads(raw))
        result = scan(
            candles,
            meta,
            swing_width=args.swing_width,
            sweep_lookback=args.sweep_lookback,
            setup_lookahead=args.setup_lookahead,
            atr_period=args.atr_period,
            displacement_body_multiple=args.body_multiple,
            displacement_atr_multiple=args.atr_multiple,
            minimum_rr=args.minimum_rr,
            direction=args.direction,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
