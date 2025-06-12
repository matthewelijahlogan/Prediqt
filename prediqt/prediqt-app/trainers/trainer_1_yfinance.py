# trainer_1_yfinance.py
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pandas as pd

def predict(ticker, horizon="hour"):
    print(f"[trainer_1_yfinance] Predicting for {ticker} ({horizon})")

    # Set period/interval
    period, interval = {
        "hour": ("90d", "1h"),
        "day": ("1y", "1d"),
        "week": ("3y", "1wk"),
        "month": ("5y", "1mo")
    }[horizon]
    shift_periods = 1

    df = yf.download(ticker, period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}' with horizon '{horizon}'")

    df = df.dropna()
    df['Return'] = df['Close'].pct_change()
    df['Target'] = df['Close'].shift(-shift_periods)
    df = df.dropna()

    features = ['Open', 'High', 'Low', 'Close', 'Volume', 'Return']
    X = df[features]
    y = df['Target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    latest_features = X.iloc[-1].to_frame().T
    predicted_price = model.predict(latest_features)[0]
    mse = mean_squared_error(y_test, model.predict(X_test))

    return {
        "predicted_next_close": round(predicted_price, 2),
        "model_mse": round(mse, 4),
        "recent_prices": list(df["Close"][-10:])
    }
