# file: kingmaker/trainer_14_sma_crossover.py

import yfinance as yf
import pandas as pd

def train_and_predict(ticker: str, short_window: int = 10, long_window: int = 50):
    """
    Simple Moving Average Crossover:
    +1 = bullish crossover
    -1 = bearish crossover
     0 = no crossover
    """
    try:
        data = yf.download(ticker, period="3mo", interval="1d")
        if data.empty or len(data) < long_window:
            return {"score": 0, "error": "Insufficient data"}

        close = data["Close"]
        sma_short = close.rolling(window=short_window).mean()
        sma_long = close.rolling(window=long_window).mean()

        if pd.isna(sma_short.iloc[-2]) or pd.isna(sma_long.iloc[-2]) or pd.isna(sma_short.iloc[-1]) or pd.isna(sma_long.iloc[-1]):
            return {"score": 0, "error": "Not enough SMA data points"}

        if sma_short.iloc[-2] < sma_long.iloc[-2] and sma_short.iloc[-1] > sma_long.iloc[-1]:
            signal = 1  # Bullish crossover
        elif sma_short.iloc[-2] > sma_long.iloc[-2] and sma_short.iloc[-1] < sma_long.iloc[-1]:
            signal = -1  # Bearish crossover
        else:
            signal = 0

        return {
            "score": signal,
            "details": {
                "model": "SMACrossoverModel",
                "sma_short": round(sma_short.iloc[-1], 2),
                "sma_long": round(sma_long.iloc[-1], 2),
                "sma_signal": signal
            }
        }

    except Exception as e:
        return {"score": 0, "error": f"SMA crossover failed: {e}"}

# ✅ Required fusion interface
def get_signal(ticker: str):
    return train_and_predict(ticker)
