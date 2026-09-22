import unittest

from trainers.trainer_fusion import heuristic_predict


class FusionSafetyTests(unittest.TestCase):
    def test_hourly_cap_is_measured_from_live_price_not_base_forecast(self):
        base = {
            "predicted_next_close": 120.0,
            "confidence": 1.0,
            "model_mse": 1.0,
            "validation_confidence": 80.0,
            "meta": {"current_price": 100.0},
        }

        result = heuristic_predict(base=base, horizon="hour")

        self.assertLessEqual(result["predicted_next_close"], 103.0)
        self.assertGreaterEqual(result["predicted_next_close"], 97.0)

    def test_zero_confidence_auxiliary_model_cannot_move_forecast(self):
        base = {
            "predicted_next_close": 100.0,
            "confidence": 1.0,
            "model_mse": 1.0,
            "validation_confidence": 80.0,
            "meta": {"current_price": 100.0},
        }
        technical = {"prediction": 0.25, "confidence": 0.0}

        result = heuristic_predict(base=base, technical=technical, horizon="hour")

        self.assertEqual(result["predicted_next_close"], 100.0)


if __name__ == "__main__":
    unittest.main()
