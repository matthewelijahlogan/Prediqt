# file: kingmaker/trainer_11_rsi.py

import yfinance as yf
import pandas as pd

def calculate_rsi(prices, period=14):
    """
    Manually calculate RSI using pandas.
    """
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def train_and_predict(ticker: str, period=14):
    """
    Generate RSI-based sentiment score for a given ticker.
    Score is normalized from -1 (bearish) to +1 (bullish).
    """
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        if data.empty or 'Close' not in data:
            return {"score": 0, "error": "No price data available"}

        rsi_series = calculate_rsi(data['Close'], period)
        latest_rsi = rsi_series.dropna().iloc[-1]

        if pd.isna(latest_rsi):
            return {"score": 0, "error": "RSI calculation failed"}

        if latest_rsi < 30:
            score = (30 - latest_rsi) / 30  # Normalize to +1
        elif latest_rsi > 70:
            score = (70 - latest_rsi) / 30 * -1  # Normalize to -1
        else:
            score = 0.0

        score = max(min(score, 1), -1)  # Clip to [-1, 1]

        return {
            "score": round(score, 4),
            "details": {
                "model": "RSISentimentModel",
                "latest_rsi": round(latest_rsi, 2),
                "note": "RSI calculated manually (no pandas-ta)"
            }
        }

    except Exception as e:
        return {"score": 0, "error": f"RSI analysis failed: {str(e)}"}

# ✅ Required fusion interface
def get_signal(ticker: str):
    return train_and_predict(ticker)
