import yfinance as yf
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler

def build_and_train_linear_model(ticker):
    data = yf.Ticker(ticker).history(period="6mo")
    if len(data) < 60:
        raise ValueError("Not enough data to train model.")

    close_prices = data["Close"].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_prices = scaler.fit_transform(close_prices)

    lookback = 60
    X, y = [], []
    for i in range(lookback, len(scaled_prices)):
        X.append(scaled_prices[i - lookback:i].flatten())  # 60-day window
        y.append(scaled_prices[i][0])  # Next day's price (scaled)

    X, y = np.array(X), np.array(y)

    model = LinearRegression()
    model.fit(X, y)

    last_sequence = scaled_prices[-lookback:].flatten().reshape(1, -1)
    predicted_scaled_price = np.clip(model.predict(last_sequence)[0], 0, 1)
    predicted_price = scaler.inverse_transform([[predicted_scaled_price]])[0][0]

    recent_price = float(close_prices[-1][0])
    delta = predicted_price - recent_price
    score = delta / recent_price  # Normalized return

    return {
        "score": round(score, 4),
        "details": {
            "model": "LinearRegression_Price_Trend",
            "predicted_next_close": round(predicted_price, 2),
            "last_close_price": round(recent_price, 2)
        }
    }

# Required interface for fusion
def get_signal(ticker: str):
    try:
        return build_and_train_linear_model(ticker)
    except Exception as e:
        return {"score": 0, "error": str(e)}

# No default test runner — handled externally
