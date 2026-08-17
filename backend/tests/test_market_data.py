import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from backend.routers.ticker_tape import TICKER_CACHE
from backend.yfinance_client import get_quote
from trainers import trainer_1_yfinance


class MarketDataResilienceTests(unittest.TestCase):
    def test_quote_uses_ticker_tape_when_history_is_rate_limited(self):
        cached = {"tickers": [{"symbol": "AAPL", "price": 306.05}], "last_updated": 1}
        with patch.dict(TICKER_CACHE, cached, clear=True), patch(
            "yfinance.download", side_effect=RuntimeError("Too Many Requests")
        ):
            quote = get_quote("aapl")

        self.assertEqual(quote["price"], 306.05)
        self.assertEqual(quote["source"], "ticker_tape_cache")
        self.assertIsNone(quote["percent_change"])

    def test_base_forecast_includes_finite_model_error(self):
        closes = np.linspace(100.0, 125.0, 60)
        history = pd.DataFrame({"Close": closes})
        with patch.object(trainer_1_yfinance, "fetch_yfinance_data", return_value=history):
            result = trainer_1_yfinance.predict("AAPL", "hour")

        self.assertGreaterEqual(result["model_mse"], 0)
        self.assertTrue(np.isfinite(result["model_mse"]))
        self.assertIsInstance(result["predicted_next_close"], float)
        self.assertIsInstance(result["meta"]["current_price"], float)


if __name__ == "__main__":
    unittest.main()
