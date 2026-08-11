import unittest
import sys
from types import ModuleType
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class SignalApiTests(unittest.TestCase):
    def test_prediction_response_includes_classified_signal(self):
        result = {
            "current_price": 100.0,
            "predicted_next_close": 103.0,
            "model_mse": 1.0,
            "used_models": ["base", "technical"],
            "weights_used": {"base": 0.7, "technical": 0.3},
        }

        trainer = ModuleType("train_predictor")
        trainer.train_and_predict = lambda _ticker, _horizon: result
        with patch.dict(sys.modules, {"train_predictor": trainer}):
            response = TestClient(app).get("/predict/AAPL?horizon=day")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["signal"]["action"], "BUY")
        self.assertEqual(payload["signal"]["expected_move_percent"], 3.0)
        self.assertEqual(payload["current_price"], 100.0)


if __name__ == "__main__":
    unittest.main()
