import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def predict(ticker: str, horizon: str = "hour"):
    """
    Predicts near-term volatility for the given ticker and horizon.
    Volatility is modeled as rolling std deviation of returns.
    """
    print(f"[trainer_15_volatility] Predicting volatility for {ticker} ({horizon})")

    try:
        # Horizon settings
        period, interval = {
            "hour": ("90d", "1h"),
            "day": ("1y", "1d"),
            "month": ("5y", "1mo")
        }.get(horizon, ("90d", "1h"))

        df = yf.download(ticker, period=period, interval=interval, progress=False).dropna()

        if df.empty or len(df) < 30:
            return {
                "trainer": "volatility_model",
                "prediction": 0.0,
                "confidence": 0.0,
                "meta": {
                    "reason": "insufficient_data",
                    "horizon": horizon
                }
            }

        df['Return'] = df['Close'].pct_change()
        df['Volatility'] = df['Return'].rolling(window=10).std()
        df['TargetVolatility'] = df['Volatility'].shift(-1)
        df = df.dropna()

        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'Return', 'Volatility']
        X = df[features]
        y = df['TargetVolatility']

        # Time-aware train/test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)

        # Predict next-period volatility
        latest_input = X.iloc[-1].to_frame().T
        predicted_volatility = float(model.predict(latest_input)[0])
        baseline_vol = float(df['Volatility'].iloc[-1])
        prediction_delta = predicted_volatility - baseline_vol

        return {
            "trainer": "volatility_model",
            "prediction": round(prediction_delta, 6),
            "confidence": round(min(1.0, abs(prediction_delta * 100)), 3),
            "meta": {
                "predicted_volatility": round(predicted_volatility, 6),
                "baseline_volatility": round(baseline_vol, 6),
                "mse": round(mse, 6),
                "horizon": horizon,
                "features_used": features
            }
        }

    except Exception as e:
        print(f"[volatility_model] Error: {e}")
        return {
            "trainer": "volatility_model",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {
                "error": str(e),
                "horizon": horizon
            }
        }

if __name__ == "__main__":
    print(predict("AAPL", horizon="hour"))
