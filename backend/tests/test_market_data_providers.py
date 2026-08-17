import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from backend import market_data


def history_frame():
    return pd.DataFrame({
        "Open": np.arange(40) + 100,
        "High": np.arange(40) + 101,
        "Low": np.arange(40) + 99,
        "Close": np.arange(40) + 100.5,
        "Volume": np.arange(40) + 1000,
    })


class MarketDataProviderTests(unittest.TestCase):
    def setUp(self):
        market_data._cache.clear()

    def test_uses_alpha_vantage_when_alpaca_is_unavailable(self):
        frame = history_frame()
        with patch.object(market_data, "_alpaca_history", side_effect=RuntimeError("down")), patch.object(
            market_data, "_alpha_vantage_history", return_value=frame
        ), patch.object(market_data, "_yahoo_history") as yahoo:
            result, source = market_data.get_daily_history("AAPL")

        self.assertEqual(source, "alpha_vantage")
        self.assertEqual(len(result), 40)
        yahoo.assert_not_called()

    def test_uses_yahoo_as_last_network_provider(self):
        frame = history_frame()
        with patch.object(market_data, "_alpaca_history", side_effect=RuntimeError("down")), patch.object(
            market_data, "_alpha_vantage_history", side_effect=RuntimeError("down")
        ), patch.object(market_data, "_yahoo_history", return_value=frame):
            _, source = market_data.get_daily_history("MSFT")

        self.assertEqual(source, "yahoo")

    def test_reuses_fresh_last_known_good_history(self):
        frame = history_frame()
        with patch.object(market_data, "_alpaca_history", return_value=frame) as alpaca:
            first, first_source = market_data.get_daily_history("NVDA")
            second, second_source = market_data.get_daily_history("NVDA")

        self.assertEqual(first_source, "alpaca")
        self.assertEqual(second_source, "alpaca")
        self.assertEqual(len(first), len(second))
        alpaca.assert_called_once()


if __name__ == "__main__":
    unittest.main()
