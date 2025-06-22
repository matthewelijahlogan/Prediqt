from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import yfinance as yf
import os
import time

router = APIRouter()

# Global cache to avoid repeated API hits
TICKER_CACHE = {
    "tickers": [],
    "last_updated": 0
}

# Path to tickers.txt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TICKER_FILE = os.path.join(BASE_DIR, "..", "..", "tickers.txt")

@router.get("/api/ticker-tape")
def get_ticker_tape():
    # Refresh every 3600 seconds (1 hour)
    current_time = time.time()
    if current_time - TICKER_CACHE["last_updated"] > 3600:
        if not os.path.exists(TICKER_FILE):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "tickers.txt not found at expected location."}
            )

        # Load tickers
        try:
            with open(TICKER_FILE, "r") as f:
                tickers = [line.strip().upper() for line in f if line.strip()]
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"Failed to read tickers.txt: {str(e)}"}
            )

        tickers = tickers[:100]  # Limit to top 100 symbols

        # Try to fetch prices using yfinance
        try:
            data = yf.download(
                tickers=tickers,
                period="1d",
                interval="1m",
                group_by="ticker",
                threads=True,
                progress=False
            )

            result = []
            for ticker in tickers:
                try:
                    last_price = data[ticker]["Close"].dropna().iloc[-1]
                    result.append({
                        "symbol": ticker,
                        "price": round(float(last_price), 2)
                    })
                except Exception:
                    result.append({
                        "symbol": ticker,
                        "price": "N/A"
                    })

            # Update the cache
            TICKER_CACHE["tickers"] = result
            TICKER_CACHE["last_updated"] = current_time

        except Exception as e:
            print("[ticker-tape] yfinance error:", e)
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "Failed to fetch prices from yfinance."}
            )

    # Return either fresh or cached result
    return {"tickers": TICKER_CACHE["tickers"]}
