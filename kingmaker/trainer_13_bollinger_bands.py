# file: kingmaker/trainer_13_bollinger_bands.py

import yfinance as yf
import pandas as pd

def calculate_bollinger_bands(prices, length=20, std=2):
    """
    Calculate Bollinger Bands: lower, middle (SMA), upper.
    """
    sma = prices.rolling(window=length).mean()
    rolling_std = prices.rolling(window=length).std()
    upper_band = sma + (rolling_std * std)
    lower_band = sma - (rolling_std * std)
    return lower_band, sma, upper_band

def train_and_predict(ticker: str, length=20, std=2):
    """
    Signal:
    +1 if price <= lower band (buy)
    -1 if price >= upper band (sell)
    0 otherwise
    """
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        if data.empty or 'Close' not in data:
            return {"score": 0, "error": "No data"}

        close = data['Close'].iloc[-1]
        lower_band, _, upper_band = calculate_bollinger_bands(data['Close'], length, std)

        lower = lower_band.iloc[-1]
        upper = upper_band.iloc[-1]

        if pd.isna(lower) or pd.isna(upper):
            return {"score": 0, "error": "Insufficient data for Bollinger Bands"}

        if close <= lower:
            signal = 1
        elif close >= upper:
            signal = -1
        else:
            signal = 0

        return {
            "score": signal,
            "details": {
                "model": "BollingerBandsSentimentModel",
                "close": round(close, 2),
                "lower_band": round(lower, 2),
                "upper_band": round(upper, 2),
                "bb_signal": signal
            }
        }

    except Exception as e:
        return {"score": 0, "error": f"Bollinger Bands analysis failed: {str(e)}"}

# ✅ Required fusion interface
def get_signal(ticker: str):
    return train_and_predict(ticker)
