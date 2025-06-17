# file: kingmaker/trainer_12_macd.py

import yfinance as yf
import pandas as pd

def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate MACD, signal line, and histogram.
    """
    fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
    slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def train_and_predict(ticker: str):
    """
    Detect bullish/bearish MACD crossovers.
    """
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        if data.empty or 'Close' not in data:
            return {"score": 0, "error": "No data"}

        macd_line, signal_line, _ = calculate_macd(data['Close'])

        if len(macd_line) < 2 or len(signal_line) < 2:
            return {"score": 0, "error": "MACD data insufficient"}

        # Detect crossover
        if macd_line.iloc[-2] < signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]:
            signal = 1  # Bullish
        elif macd_line.iloc[-2] > signal_line.iloc[-2] and macd_line.iloc[-1] < signal_line.iloc[-1]:
            signal = -1  # Bearish
        else:
            signal = 0  # Neutral

        return {
            "score": signal,
            "details": {
                "model": "MACDSentimentModel",
                "macd": round(macd_line.iloc[-1], 5),
                "signal_line": round(signal_line.iloc[-1], 5),
                "macd_signal": signal
            }
        }

    except Exception as e:
        return {"score": 0, "error": f"MACD analysis failed: {str(e)}"}

# ✅ Required fusion interface
def get_signal(ticker: str):
    return train_and_predict(ticker)
