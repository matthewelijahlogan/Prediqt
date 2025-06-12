import yfinance as yf
import numpy as np
import pandas as pd

def predict(ticker: str):
    print(f"[trainer_13_volume] Evaluating volume and market movement for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo", interval="1h")

        if hist.empty or len(hist) < 30:
            print("[volume_model] Not enough data to calculate volume indicators.")
            return {"adjustment": 1.0, "reason": "insufficient_data"}

        close = hist["Close"]
        volume = hist["Volume"]

        # Average Volume and Volume Spike Detection
        avg_volume_20 = volume.rolling(window=20).mean()
        current_volume = volume.iloc[-1]
        avg_volume = avg_volume_20.iloc[-1]
        volume_spike = current_volume > (avg_volume * 1.5)  # volume spike if 50%+ above avg

        # Price Movement Direction (last hour vs previous hour)
        price_change = close.diff()
        last_change = price_change.iloc[-1]

        # Volatility - std dev of returns last 20 hours
        returns = close.pct_change()
        volatility = returns.rolling(window=20).std().iloc[-1]

        # Scoring rules:
        # volume spike: +1
        # positive price change: +1, negative: -1
        # high volatility (> median volatility): -1 (risk caution)
        median_volatility = returns.rolling(window=100).std().median()
        volatility_score = -1 if volatility > median_volatility else 0

        volume_score = 1 if volume_spike else 0
        price_score = 1 if last_change > 0 else (-1 if last_change < 0 else 0)

        total_score = volume_score + price_score + volatility_score
        adjustment = 1.0 + (total_score * 0.03)  # Scale gently ±9%

        output = {
            "adjustment": round(adjustment, 3),
            "current_volume": int(current_volume),
            "average_volume_20": int(avg_volume),
            "volume_spike": volume_spike,
            "last_price_change": round(last_change, 4),
            "volatility": round(volatility, 5),
            "volume_score": volume_score,
            "price_score": price_score,
            "volatility_score": volatility_score,
            "total_score": total_score
        }

        print(f"[volume_model] Output: {output}")
        return output

    except Exception as e:
        print(f"[volume_model] Error: {e}")
        return {"adjustment": 1.0, "error": str(e)}
