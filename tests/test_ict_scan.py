import unittest
from datetime import datetime, timedelta, timezone

from scripts.ict_scan import Candle, detect_fvgs, parse_candles, scan


def bullish_fixture():
    base = datetime(2026, 10, 9, 13, 30, tzinfo=timezone.utc)
    values = [
        (101, 103, 99, 102),
        (102, 115, 100, 110),
        (110, 111, 98, 100),
        (100, 103, 99, 102),
        (102, 105, 100, 104),
        (104, 104.5, 99, 100),
        (100, 101, 97, 99),
        (99, 104, 98.8, 103.8),
        (103.8, 110, 103, 106),
        (106, 107, 101.5, 103),
    ]
    return {
        "meta": {"instrument": "TEST-USDT", "timeframe": "5m"},
        "candles": [
            {
                "timestamp": (base + timedelta(minutes=index * 5)).isoformat(),
                "open": row[0],
                "high": row[1],
                "low": row[2],
                "close": row[3],
                "volume": 100 + index,
            }
            for index, row in enumerate(values)
        ],
    }


class FvgTests(unittest.TestCase):
    def test_strict_wick_non_overlap_is_required(self):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        candles = [
            Candle(base, 9, 10, 8, 9),
            Candle(base + timedelta(minutes=5), 9, 12, 8.5, 11),
            Candle(base + timedelta(minutes=10), 11, 12, 9.9, 11.5),
        ]
        self.assertEqual(detect_fvgs(candles), [])

    def test_bullish_fvg_zone_and_ce(self):
        candles, _ = parse_candles(bullish_fixture())
        gap = next(gap for gap in detect_fvgs(candles) if gap["middle_index"] == 7)
        self.assertEqual(gap["direction"], "bullish")
        self.assertEqual(gap["zone"], [101.0, 103.0])
        self.assertEqual(gap["ce"], 102.0)


class IctModelTests(unittest.TestCase):
    def run_fixture(self, payload=None):
        candles, meta = parse_candles(payload or bullish_fixture())
        return scan(
            candles,
            meta,
            swing_width=1,
            setup_lookahead=5,
            displacement_body_multiple=1.2,
            displacement_atr_multiple=0.5,
            minimum_rr=2.0,
            direction="long",
        )

    def test_complete_bullish_ict_sequence_confirms(self):
        result = self.run_fixture()
        candidate = result["latest_candidate"]
        self.assertEqual(candidate["mechanical_status"], "confirmed")
        self.assertEqual(candidate["sweep"]["session"], "silver_bullet")
        self.assertEqual(candidate["entry"]["zone"], [101.0, 103.0])
        self.assertEqual(candidate["mss"]["reference"]["price"], 105.0)
        self.assertEqual(candidate["target"]["price"], 115.0)
        self.assertGreaterEqual(candidate["gross_rr_to_candidate_target"], 2.0)
        self.assertTrue(all(candidate["checks"].values()))

    def test_wick_without_close_does_not_confirm_mss(self):
        payload = bullish_fixture()
        payload["candles"][8]["close"] = 104
        result = self.run_fixture(payload)
        candidate = result["latest_candidate"]
        self.assertEqual(candidate["mechanical_status"], "developing")
        self.assertFalse(candidate["checks"]["closed_candle_mss"])

    def test_okx_newest_first_arrays_are_sorted(self):
        payload = bullish_fixture()
        arrays = [
            [
                int(datetime.fromisoformat(row["timestamp"]).timestamp() * 1000),
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"],
            ]
            for row in reversed(payload["candles"])
        ]
        candles, _ = parse_candles(arrays)
        self.assertLess(candles[0].timestamp, candles[-1].timestamp)


if __name__ == "__main__":
    unittest.main()
