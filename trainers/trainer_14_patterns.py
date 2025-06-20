import yfinance as yf
import pandas as pd

def predict(ticker: str):
    print(f"[trainer_14_patterns] Scanning candlestick patterns for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d", interval="1h")

        if hist.empty or len(hist) < 5:
            return {
                "trainer": "pattern_model",
                "prediction": 0.0,
                "confidence": 0.0,
                "meta": {
                    "reason": "insufficient_data"
                }
            }

        candles = hist[-5:].copy()
        candles["Body"] = candles["Close"] - candles["Open"]
        candles["Range"] = candles["High"] - candles["Low"]

        patterns = []

        # Bullish Engulfing
        if (
            candles["Open"].iloc[-1] < candles["Close"].iloc[-2] and
            candles["Close"].iloc[-1] > candles["Open"].iloc[-2] and
            candles["Body"].iloc[-1] > abs(candles["Body"].iloc[-2])
        ):
            patterns.append("bullish_engulfing")

        # Bearish Engulfing
        if (
            candles["Open"].iloc[-1] > candles["Close"].iloc[-2] and
            candles["Close"].iloc[-1] < candles["Open"].iloc[-2] and
            abs(candles["Body"].iloc[-1]) > candles["Body"].iloc[-2]
        ):
            patterns.append("bearish_engulfing")

        # Morning Star (simplified)
        if (
            candles["Body"].iloc[-3] < 0 and  # Down candle
            abs(candles["Body"].iloc[-2]) < candles["Range"].iloc[-2] * 0.3 and  # Small candle (star)
            candles["Body"].iloc[-1] > 0 and  # Up candle
            candles["Close"].iloc[-1] > (candles["Open"].iloc[-3] + candles["Close"].iloc[-3]) / 2
        ):
            patterns.append("morning_star")

        # Evening Star (added)
        if (
            candles["Body"].iloc[-3] > 0 and  # Up candle
            abs(candles["Body"].iloc[-2]) < candles["Range"].iloc[-2] * 0.3 and  # Small candle (star)
            candles["Body"].iloc[-1] < 0 and  # Down candle
            candles["Close"].iloc[-1] < (candles["Open"].iloc[-3] + candles["Close"].iloc[-3]) / 2
        ):
            patterns.append("evening_star")

        # Three Black Crows
        if all(candles["Body"].iloc[-i] < 0 for i in [1, 2, 3]) and \
           candles["Close"].iloc[-1] < candles["Open"].iloc[-2] and \
           candles["Close"].iloc[-2] < candles["Open"].iloc[-3]:
            patterns.append("three_black_crows")

        # Three White Soldiers
        if all(candles["Body"].iloc[-i] > 0 for i in [1, 2, 3]) and \
           candles["Close"].iloc[-1] > candles["Open"].iloc[-2] and \
           candles["Close"].iloc[-2] > candles["Open"].iloc[-3]:
            patterns.append("three_white_soldiers")

        # Hammer (last candle)
        last_candle = candles.iloc[-1]
        body = abs(last_candle["Body"])
        lower_shadow = last_candle["Open"] - last_candle["Low"] if last_candle["Body"] > 0 else last_candle["Close"] - last_candle["Low"]
        upper_shadow = last_candle["High"] - last_candle["Close"] if last_candle["Body"] > 0 else last_candle["High"] - last_candle["Open"]
        if body < lower_shadow * 0.5 and upper_shadow < body * 0.3:
            patterns.append("hammer")

        # Inverted Hammer (last candle)
        if body < upper_shadow * 0.5 and lower_shadow < body * 0.3:
            patterns.append("inverted_hammer")

        # Scoring map
        score_map = {
            "bullish_engulfing": 2,
            "bearish_engulfing": -2,
            "morning_star": 3,
            "evening_star": -3,
            "three_black_crows": -3,
            "three_white_soldiers": 3,
            "hammer": 1,
            "inverted_hammer": 1
        }

        total_score = sum(score_map.get(p, 0) for p in patterns)
        prediction = round(total_score * 0.015, 5)  # Adjusted scale for prediction
        confidence = min(1.0, abs(total_score) * 0.4)  # Confidence scaled by pattern strength

        result = {
            "trainer": "pattern_model",
            "prediction": prediction,
            "confidence": round(confidence, 3),
            "meta": {
                "patterns_detected": patterns,
                "pattern_score": total_score,
                "candles_used": len(candles)
            }
        }

        print(f"[pattern_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[pattern_model] Error: {e}")
        return {
            "trainer": "pattern_model",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {
                "error": str(e)
            }
        }

if __name__ == "__main__":
    print(predict("AAPL"))

