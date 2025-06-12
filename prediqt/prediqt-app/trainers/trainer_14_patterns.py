import yfinance as yf
import pandas as pd

def predict(ticker: str):
    print(f"[trainer_14_patterns] Scanning candlestick patterns for {ticker}...")
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d", interval="1h")
        if hist.empty or len(hist) < 5:
            return {"adjustment": 1.0, "reason": "insufficient_data"}

        candles = hist[-5:].copy()
        candles["Body"] = candles["Close"] - candles["Open"]
        candles["Range"] = candles["High"] - candles["Low"]

        scores = []

        # Bullish engulfing (last candle opens below previous close and closes above previous open)
        if (candles["Open"].iloc[-1] < candles["Close"].iloc[-2]) and (candles["Close"].iloc[-1] > candles["Open"].iloc[-2]):
            scores.append(1)

        # Bearish engulfing
        if (candles["Open"].iloc[-1] > candles["Close"].iloc[-2]) and (candles["Close"].iloc[-1] < candles["Open"].iloc[-2]):
            scores.append(-1)

        # Morning Star (gap down followed by strong up candle)
        if (
            candles["Close"].iloc[-3] > candles["Open"].iloc[-3] and
            candles["Close"].iloc[-2] < candles["Open"].iloc[-2] and
            candles["Close"].iloc[-1] > candles["Open"].iloc[-1] and
            candles["Open"].iloc[-1] > candles["Close"].iloc[-2]
        ):
            scores.append(1)

        # Three Black Crows
        if all(candles["Close"].iloc[-i] < candles["Open"].iloc[-i] for i in [1, 2, 3]):
            scores.append(-1)

        # Final scoring
        total_score = sum(scores)
        adjustment = 1.0 + (total_score * 0.01)  # Soft influence

        return {
            "adjustment": round(adjustment, 3),
            "pattern_score": total_score,
            "patterns": scores
        }

    except Exception as e:
        print(f"[trainer_14_patterns] Error: {e}")
        return {"adjustment": 1.0, "error": str(e)}
