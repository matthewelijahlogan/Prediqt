# file: kingmaker/trainer_6_dark_pool_volume.py

import yfinance as yf

def run_model(ticker: str):
    print(f"[Kingmaker: DarkPoolVolume] 🕳️ Estimating dark pool proxy score for {ticker}")
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="10d", interval="1d")

        if hist.empty or len(hist) < 2:
            return {
                "score": 0,
                "details": {
                    "model": "DarkPoolVolume",
                    "note": "Not enough historical volume data"
                }
            }

        volumes = hist["Volume"]
        avg_vol = volumes.mean()
        latest_vol = volumes.iloc[-1]
        spike_ratio = latest_vol / avg_vol if avg_vol > 0 else 0
        spike_score = min(spike_ratio / 3, 1.0)  # Normalize to [0, 1]

        # Price change from previous day
        close_today = hist["Close"].iloc[-1]
        close_yesterday = hist["Close"].iloc[-2]
        price_change_pct = abs(close_today - close_yesterday) / close_yesterday
        price_momentum_score = min(price_change_pct * 10, 1.0)

        dark_pool_score = 0.7 * spike_score + 0.3 * price_momentum_score

        return {
            "score": round(dark_pool_score, 4),
            "details": {
                "model": "DarkPoolVolume",
                "latest_volume": int(latest_vol),
                "average_volume": int(avg_vol),
                "volume_spike_ratio": round(spike_ratio, 3),
                "price_change_pct": round(price_change_pct * 100, 2),
                "note": "Heuristic proxy based on volume spikes and price movement"
            }
        }

    except Exception as e:
        return {
            "score": 0,
            "error": f"DarkPoolVolume error: {str(e)}"
        }

# Required fusion interface
def get_signal(ticker: str):
    return run_model(ticker)

if __name__ == "__main__":
    print(get_signal("TSLA"))
