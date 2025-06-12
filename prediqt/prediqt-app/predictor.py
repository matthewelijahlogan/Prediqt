import yfinance as yf
from train_predictor import train_and_predict

WATCHLIST = ['AAPL', 'TSLA', 'AMZN', 'GOOG', 'MSFT']

def get_top_movers_and_losers():
    movers = []
    losers = []

    for ticker in WATCHLIST:
        try:
            pred_data = train_and_predict(ticker, "day")

            hist = yf.Ticker(ticker).history(period="1d")
            if hist.empty:
                print(f"No recent price data for {ticker}, skipping.")
                continue
            current_price = hist['Close'][-1]
            predicted_price = pred_data["predicted_next_close"]
            change_pct = (predicted_price - current_price) / current_price * 100
            direction = "Up" if change_pct > 0 else "Down"

            item = {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "predicted_next_close": round(predicted_price, 2),
                "percent_change": round(change_pct, 2),
                "direction": direction,
                "model_mse": pred_data.get("model_mse")
            }

            if direction == "Up":
                movers.append(item)
            else:
                losers.append(item)
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

    movers.sort(key=lambda x: x["percent_change"], reverse=True)
    losers.sort(key=lambda x: x["percent_change"])

    return movers, losers
