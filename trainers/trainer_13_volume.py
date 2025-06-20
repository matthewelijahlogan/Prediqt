import yfinance as yf
import numpy as np
import pandas as pd

def predict(ticker: str):
    print(f"[trainer_13_volume] Evaluating volume and market movement for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo", interval="1h")

        if hist.empty or len(hist) < 30:
            return {
                "trainer": "volume_model",
                "prediction": 0.0,
                "confidence": 0.0,
                "meta": {
                    "reason": "insufficient_data"
                }
            }

        close = hist["Close"]
        volume = hist["Volume"]

        # Volume analysis
        avg_volume_20 = volume.rolling(window=20).mean()
        current_volume = volume.iloc[-1]
        avg_volume = avg_volume_20.iloc[-1]
        volume_spike = current_volume > (avg_volume * 1.5)

        # Price movement
        price_change = close.diff()
        last_change = price_change.iloc[-1]

        # Volatility
        returns = close.pct_change()
        volatility = returns.rolling(window=20).std().iloc[-1]
        median_volatility = returns.rolling(window=100).std().median()
        high_volatility = volatility > median_volatility

        # Scoring
        volume_score = 1 if volume_spike else 0
        price_score = 1 if last_change > 0 else (-1 if last_change < 0 else 0)
        volatility_score = -1 if high_volatility else 0
        total_score = volume_score + price_score + volatility_score

        prediction = round(total_score * 0.03, 5)  # ±9% range
        confidence = min(1.0, abs(prediction) * 20)  # cap at 1.0 when |prediction| ≥ 0.05

        output = {
            "trainer": "volume_model",
            "prediction": prediction,
            "confidence": round(confidence, 3),
            "meta": {
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
        }

        print(f"[volume_model] Output: {output}")
        return output

    except Exception as e:
        print(f"[volume_model] Error: {e}")
        return {
            "trainer": "volume_model",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {
                "error": str(e)
            }
        }

if __name__ == "__main__":
    print(predict("AAPL"))
