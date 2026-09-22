import unittest

from backend.signals import classify_signal


class SignalClassificationTests(unittest.TestCase):
    def test_buy_requires_move_and_evidence_thresholds(self):
        result = classify_signal(100, 103, 1, "day")

        self.assertEqual(result["action"], "BUY")
        self.assertTrue(result["qualified"])
        self.assertEqual(result["expected_move_percent"], 3.0)

    def test_sell_requires_negative_move_beyond_threshold(self):
        result = classify_signal(100, 95, 1, "week")

        self.assertEqual(result["action"], "SELL")
        self.assertTrue(result["qualified"])

    def test_hold_when_move_does_not_clear_horizon_threshold(self):
        result = classify_signal(100, 101, 1, "day")

        self.assertEqual(result["action"], "HOLD")
        self.assertFalse(result["qualified"])

    def test_hold_when_model_error_is_missing(self):
        result = classify_signal(100, 110, None, "day")

        self.assertEqual(result["action"], "HOLD")
        self.assertEqual(result["confidence"], 0.0)

    def test_hold_when_prices_are_unavailable(self):
        result = classify_signal(None, 110, 1, "day")

        self.assertEqual(result["action"], "HOLD")
        self.assertIsNone(result["expected_move_percent"])

    def test_validation_confidence_caps_error_based_confidence(self):
        result = classify_signal(100, 103, 0.01, "day", validation_confidence=42)

        self.assertEqual(result["action"], "HOLD")
        self.assertEqual(result["confidence"], 42.0)


if __name__ == "__main__":
    unittest.main()
