import yfinance as yf
import numpy as np

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0  # Neutral RSI fallback
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / (down + 1e-6)
    rsi_series = [100 - 100 / (1 + rs)]

    for i in range(period, len(prices) - 1):
        delta = deltas[i]
        upval = max(delta, 0)
        downval = max(-delta, 0)
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / (down + 1e-6)
        rsi_series.append(100 - 100 / (1 + rs))
    return rsi_series[-1]

def ema(prices, span):
    alpha = 2 / (span + 1)
    ema_values = [prices[0]]
    for price in prices[1:]:
        ema_values.append(alpha * price + (1 - alpha) * ema_values[-1])
    return ema_values[-1]

def macd(prices):
    if len(prices) < 26:
        return 0.0  # Not enough data
    ema_fast = ema(prices, 12)
    ema_slow = ema(prices, 26)
    return ema_fast - ema_slow

def bollinger_bands(prices, window=20):
    if len(prices) < window:
        return None, None
    slice_ = prices[-window:]
    mid = np.mean(slice_)
    std = np.std(slice_)
    upper = mid + 2 * std
    lower = mid - 2 * std
    return upper, lower

def predict(ticker: str, horizon: str = "day") -> dict:
    print(f"[trainer_11_technical_indicators] Evaluating technical indicators for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo", interval="1h", auto_adjust=True)
        closes = hist['Close'].to_list()

        if len(closes) < 30:
            return {
                "trainer": "technical_indicators",
                "prediction": 0.0,
                "confidence": 0.0,
                "meta": {"reasoning": "insufficient_data"}
            }

        price = closes[-1]
        current_rsi = rsi(closes)
        current_macd = macd(closes)
        upper, lower = bollinger_bands(closes)

        rsi_score = 1 if current_rsi < 30 else -1 if current_rsi > 70 else 0
        macd_score = 1 if current_macd > 0 else -1 if current_macd < 0 else 0
        bb_score = 0
        if upper is not None and lower is not None:
            bb_score = 1 if price < lower else -1 if price > upper else 0

        total_score = rsi_score + macd_score + bb_score
        delta = total_score * 0.02  # ±6% max impact
        confidence = min(1.0, abs(total_score) / 3.0)  # Max confidence if all 3 agree

        result = {
            "trainer": "technical_indicators",
            "prediction": round(delta, 5),
            "confidence": round(confidence, 3),
            "meta": {
                "price": round(price, 2),
                "rsi": round(current_rsi, 2),
                "macd": round(current_macd, 4),
                "bollinger_upper": round(upper, 2) if upper is not None else None,
                "bollinger_lower": round(lower, 2) if lower is not None else None,
                "rsi_score": rsi_score,
                "macd_score": macd_score,
                "bollinger_score": bb_score,
                "total_score": total_score,
            }
        }

        print(f"[technical_indicators] Output: {result}")
        return result

    except Exception as e:
        print(f"[technical_indicators] Error: {e}")
        return {
            "trainer": "technical_indicators",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {"reasoning": str(e)}
        }

if __name__ == "__main__":
    print(predict("AAPL"))
