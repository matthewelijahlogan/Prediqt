# backend/routers/ticker_tape.py

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import os
import time

router = APIRouter()

# Global cache to avoid repeated API hits
TICKER_CACHE = {
    "tickers": [],
    "last_updated": 0
}

# Path to tickers.txt at the project root (two levels up from this file)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TICKER_FILE = os.path.join(BASE_DIR, "..", "..", "tickers.txt")

@router.get("/api/ticker-tape")
def get_ticker_tape():
    """
    Returns a simple ticker tape of up to 100 symbols with their latest minute-close price.
    Cached for one hour to avoid hammering yfinance.
    """
    try:
        try:
            import yfinance as yf
        except ImportError:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "yfinance is not installed on the server."}
            )

        current_time = time.time()
        # If cache is stale (>1h), refresh
        if current_time - TICKER_CACHE["last_updated"] > 3600:
            if not os.path.exists(TICKER_FILE):
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": "tickers.txt not found on server."}
                )

            # Read up to 100 tickers from file
            with open(TICKER_FILE, "r") as f:
                tickers = [line.strip().upper() for line in f if line.strip()]
            tickers = tickers[:100]

            # Download today's 1-minute data
            data = yf.download(
                tickers=tickers,
                period="1d",
                interval="1m",
                group_by="ticker",
                threads=True,
                progress=False
            )

            result = []
            for symbol in tickers:
                try:
                    # Last available close price
                    last_price = data[symbol]["Close"].dropna().iloc[-1]
                    result.append({
                        "symbol": symbol,
                        "price": round(float(last_price), 2)
                    })
                except Exception:
                    result.append({
                        "symbol": symbol,
                        "price": "N/A"
                    })

            # Update cache
            TICKER_CACHE["tickers"] = result
            TICKER_CACHE["last_updated"] = current_time

        # Always return JSON
        return {"tickers": TICKER_CACHE["tickers"]}

    except Exception as e:
        # Log server-side error and return JSON 500
        print(f"[ticker-tape] unexpected error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error fetching tickers."}
        )
