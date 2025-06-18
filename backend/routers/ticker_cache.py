import yfinance as yf
import time

CACHE = {
    "tickers": [],
    "last_updated": 0
}

def get_cached_ticker_tape():
    now = time.time()
    if now - CACHE["last_updated"] > 3600:  # 1 hour
        print("Refreshing ticker cache...")
        try:
            # Option 1: use hardcoded popular tickers
            # tickers = ['AAPL', 'TSLA', 'AMZN', 'MSFT', ...][:100]

            # Option 2: Use yfinance to get top 100 most active tickers
            most_active = yf.get_day_most_active()
            tickers = most_active['Symbol'].tolist()[:100]

            # Fetch latest prices for those tickers
            prices = yf.download(tickers=tickers, period="1d", interval="1m", group_by='ticker', progress=False)

            ticker_data = []
            for symbol in tickers:
                try:
                    last_price = prices[symbol]['Close'].dropna().iloc[-1]
                    ticker_data.append({"symbol": symbol, "price": round(float(last_price), 2)})
                except Exception:
                    ticker_data.append({"symbol": symbol, "price": "N/A"})

            CACHE["tickers"] = ticker_data
            CACHE["last_updated"] = now
        except Exception as e:
            print("Failed to refresh ticker cache:", e)

    return CACHE["tickers"]
