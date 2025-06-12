import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def predict(ticker, horizon="hour"):
    """
    Predicts future volatility for the given ticker and horizon.
    Volatility defined as rolling standard deviation of returns.
    """
    print(f"[trainer_15_volatility] Predicting volatility for {ticker} ({horizon})")

    # Set period/interval based on horizon
    period, interval = {
        "hour": ("90d", "1h"),
        "day": ("1y", "1d"),
        "month": ("5y", "1mo")
    }.get(horizon, ("90d", "1h"))

    # Fetch historical data
    df = yf.download(ticker, period=period, interval=interval)
    df = df.dropna()

    # Calculate returns
    df['Return'] = df['Close'].pct_change()

    # Calculate rolling volatility (std dev of returns)
    window_size = 10  # e.g., 10 periods rolling volatility
    df['Volatility'] = df['Return'].rolling(window=window_size).std()

    # Target: next period volatility
    shift_periods = 1
    df['TargetVolatility'] = df['Volatility'].shift(-shift_periods)

    df = df.dropna()

    features = ['Open', 'High', 'Low', 'Close', 'Volume', 'Return', 'Volatility']
    X = df[features]
    y = df['TargetVolatility']

    # Split without shuffling to preserve time series order
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    mse = mean_squared_error(y_test, model.predict(X_test))

    # Predict latest volatility
    latest_features = X.iloc[-1].to_frame().T
    predicted_volatility = model.predict(latest_features)[0]

    return {
        "predicted_volatility": round(predicted_volatility, 6),
        "model_mse": round(mse, 6)
    }