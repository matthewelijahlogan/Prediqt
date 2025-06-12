# trainer_11_technical_indicators.py

import yfinance as yf
import numpy as np
import pandas as pd

def predict(ticker: str):
    print(f"[trainer_11_technical_indicators] Evaluating technical indicators for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo", interval="1h")

        if hist.empty or len(hist) < 30:
            print("[technical_model] Not enough data to calculate indicators.")
            return {"adjustment": 1.0, "reason": "insufficient_data"}

        close = hist["Close"]

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / (avg_loss + 1e-6)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # MACD
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - signal
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_hist = macd_hist.iloc[-1]

        # Bollinger Bands
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        upper_band = sma_20 + (2 * std_20)
        lower_band = sma_20 - (2 * std_20)
        current_price = close.iloc[-1]
        upper = upper_band.iloc[-1]
        lower = lower_band.iloc[-1]

        # Scoring
        rsi_score = 1 if current_rsi < 30 else -1 if current_rsi > 70 else 0
        macd_score = 1 if current_macd > current_signal else -1 if current_macd < current_signal else 0
        bb_score = 1 if current_price < lower else -1 if current_price > upper else 0

        total_score = rsi_score + macd_score + bb_score
        adjustment = 1.0 + (total_score * 0.02)  # Scale gently to ±6%

        output = {
            "adjustment": round(adjustment, 3),
            "rsi": round(current_rsi, 2),
            "macd": round(current_macd, 4),
            "macd_signal": round(current_signal, 4),
            "macd_histogram": round(current_hist, 4),
            "bollinger_upper": round(upper, 2),
            "bollinger_lower": round(lower, 2),
            "price": round(current_price, 2),
            "rsi_score": rsi_score,
            "macd_score": macd_score,
            "bollinger_score": bb_score,
            "total_score": total_score
        }

        print(f"[technical_model] Output: {output}")
        return output

    except Exception as e:
        print(f"[technical_model] Error: {e}")
        return {"adjustment": 1.0, "error": str(e)}
