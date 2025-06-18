from fastapi import APIRouter
import yfinance as yf
import os
import time

router = APIRouter()

CACHE = {
    "tickers": [],
    "last_updated": 0
}

@router.get("/api/ticker-tape")
def get_ticker_tape():
    # Refresh every hour
    if time.time() - CACHE["last_updated"] > 3600:
        tickers_path = os.path.join(os.getcwd(), "tickers.txt")
        if not os.path.exists(tickers_path):
            return {"error": "tickers.txt not found."}

        with open(tickers_path, "r") as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
        
        tickers = tickers[:100]  # Limit to top 100

        try:
            data = yf.download(tickers=tickers, period="1d", interval="1m", group_by='ticker', progress=False)
            result = []
            for ticker in tickers:
                try:
                    last_price = data[ticker]['Close'].dropna().iloc[-1]
                    result.append({"symbol": ticker, "price": round(float(last_price), 2)})
                except Exception:
                    result.append({"symbol": ticker, "price": "N/A"})
            CACHE["tickers"] = result
            CACHE["last_updated"] = time.time()
        except Exception as e:
            print("Failed to download ticker prices:", e)
            return {"tickers": CACHE["tickers"]}  # Return old cache if error

    return {"tickers": CACHE["tickers"]}
