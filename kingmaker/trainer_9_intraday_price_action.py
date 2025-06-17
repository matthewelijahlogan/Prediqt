# file: kingmaker/trainer_9_intraday_price_action.py

import yfinance as yf
import numpy as np

def run_model(ticker: str):
    print(f"[Kingmaker: IntradayPriceAction] 📈 Analyzing intraday action for {ticker}")

    try:
        # Fetch 5 days of 1-minute interval data
        data = yf.Ticker(ticker).history(period="5d", interval="1m")
        if data.empty:
            return {
                "score": 0,
                "error": "No intraday data available"
            }

        # Calculate minute returns and volatility
        data['minute_return'] = data['Close'].pct_change()
        avg_return = data['minute_return'].mean()
        volatility = data['minute_return'].std()

        # Volume spike: latest minute volume vs. 5-day avg
        avg_volume = data['Volume'].mean()
        latest_volume = data['Volume'].iloc[-1]
        volume_spike_ratio = latest_volume / avg_volume if avg_volume > 0 else 1.0

        # Heuristic next close prediction using weighted indicators
        base_price = data['Close'].iloc[-1]
        predicted_change = avg_return * 10 + (volume_spike_ratio - 1) * 0.01
        predicted_price = base_price * (1 + predicted_change)

        return {
            "score": round(predicted_price, 2),
            "details": {
                "model": "IntradayPriceAction",
                "features": {
                    "avg_minute_return": round(avg_return, 6),
                    "volatility": round(volatility, 6),
                    "volume_spike_ratio": round(volume_spike_ratio, 3),
                    "base_price": round(base_price, 2),
                    "predicted_change_pct": round(predicted_change * 100, 4),
                }
            }
        }

    except Exception as e:
        return {
            "score": 0,
            "error": f"Intraday analysis error: {str(e)}"
        }

# Required fusion interface
def get_signal(ticker: str):
    return run_model(ticker)

if __name__ == "__main__":
    print(get_signal("AAPL"))
