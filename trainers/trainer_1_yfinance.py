import yfinance as yf
import numpy as np

def fetch_yfinance_data(ticker: str, period="6mo", interval="1d"):
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if data.empty:
            print(f"[trainer_1_yfinance] Warning: No data returned for ticker {ticker}")
            return None
        return data
    except Exception as e:
        print(f"[trainer_1_yfinance] Error fetching data for {ticker}: {e}")
        return None

def calculate_features_numpy(close_prices):
    # close_prices is a numpy array (1D)
    returns = np.diff(close_prices) / close_prices[:-1]
    ma5 = np.convolve(close_prices, np.ones(5)/5, mode='valid')
    ma10 = np.convolve(close_prices, np.ones(10)/10, mode='valid')
    
    # Volatility: rolling std of returns (window 10)
    vol = np.array([np.std(returns[i:i+10]) for i in range(len(returns)-9)])
    
    # Momentum: difference of close price - close price 5 steps ago
    momentum = close_prices[5:] - close_prices[:-5]
    
    # Align lengths (shortest length to use for prediction)
    min_len = min(len(ma10), len(vol), len(momentum))
    
    # Truncate all to min_len
    ma10 = ma10[-min_len:]
    vol = vol[-min_len:]
    momentum = momentum[-min_len:]
    ma5 = ma5[-min_len:]
    
    return {
        "returns": returns[-min_len:],
        "ma5": ma5,
        "ma10": ma10,
        "volatility": vol,
        "momentum": momentum
    }

def exponential_smoothing(values, alpha=0.5):
    if len(values) == 0:
        return 0.0
    smoothed = values[0]
    for v in values[1:]:
        smoothed = alpha * v + (1 - alpha) * smoothed
    return smoothed

def predict(ticker: str, horizon="day"):
    print(f"[trainer_1_yfinance] Starting prediction for {ticker} horizon={horizon}")
    df = fetch_yfinance_data(ticker)
    if df is None or len(df) < 20:
        return {
            "trainer": "base",
            "error": "Insufficient data",
            "confidence": 0.0,
            "predicted_next_close": 0.0,
            "meta": {}
        }

    close_prices = df['Close'].to_numpy().flatten()  # <-- Flatten here

    features = calculate_features_numpy(close_prices)

    if len(features['ma10']) < 5:
        return {
            "trainer": "base",
            "error": "Not enough data after feature calculation",
            "confidence": 0.0,
            "predicted_next_close": float(close_prices[-1]),
            "meta": {}
        }

    current_price = close_prices[-1]
    
    # Simple trend: smooth ma10[-5:]
    smoothed_trend = exponential_smoothing(features['ma10'][-5:])

    predicted_pct_change = (smoothed_trend - current_price) / current_price
    predicted_pct_change = np.clip(predicted_pct_change, -0.1, 0.1)

    recent_vol = features['volatility'][-1]
    confidence = float(np.clip(1.0 - recent_vol * 5, 0.1, 1.0))

    predicted_next_close = current_price * (1 + predicted_pct_change)

    meta = {
        "current_price": round(current_price, 2),
        "smoothed_trend": round(smoothed_trend, 2),
        "volatility": round(recent_vol, 4),
        "predicted_pct_change": round(predicted_pct_change, 5)
    }

    print(f"[trainer_1_yfinance] Prediction complete: {predicted_next_close:.2f} (conf={confidence:.3f})")

    return {
        "trainer": "base",
        "prediction": round(predicted_pct_change, 5),
        "confidence": round(confidence, 3),
        "predicted_next_close": round(predicted_next_close, 2),
        "meta": meta
    }

# Local test
if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = predict(ticker)
    print(result)
