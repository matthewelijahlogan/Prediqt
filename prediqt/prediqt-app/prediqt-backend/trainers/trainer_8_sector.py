# trainer_8_sector.py

import yfinance as yf
from datetime import datetime, timedelta

# Map sectors to sector ETFs (examples)
SECTOR_ETFS = {
    "Technology": "XLK",
    "Consumer Discretionary": "XLY",
    "Health Care": "XLV",
    "Financial Services": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication Services": "XLC",
    "Consumer Staples": "XLP",
    # Add more if you want
}

def predict(ticker: str):
    print(f"[trainer_8_sector] Checking sector trends for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        sector = info.get("sector")
        if not sector:
            print("[sector_model] No sector info found, returning neutral adjustment.")
            return {"adjustment": 1.0, "sector": None, "reasoning": "No sector info"}

        sector_etf = SECTOR_ETFS.get(sector)
        if not sector_etf:
            print(f"[sector_model] No ETF mapped for sector '{sector}', returning neutral adjustment.")
            return {"adjustment": 1.0, "sector": sector, "reasoning": "No ETF mapping for sector"}

        etf = yf.Ticker(sector_etf)
        # Get recent history - last 2 days to calculate change (today and previous trading day)
        hist = etf.history(period="2d")
        if len(hist) < 2:
            print("[sector_model] Not enough ETF history data, returning neutral adjustment.")
            return {"adjustment": 1.0, "sector": sector, "reasoning": "Insufficient ETF data"}

        # Calculate percent change between last two closes
        last_close = hist['Close'][-1]
        prev_close = hist['Close'][-2]
        pct_change = (last_close - prev_close) / prev_close

        # Simple adjustment: 1 + pct_change, clamp between 0.9 and 1.1 to avoid extreme swings
        adjustment = max(0.9, min(1.1, 1 + pct_change))

        reasoning = f"Sector '{sector}' ETF ({sector_etf}) changed {pct_change*100:.2f}% recently"

        result = {
            "adjustment": round(adjustment, 4),
            "sector": sector,
            "sector_etf": sector_etf,
            "percent_change": round(pct_change * 100, 2),
            "reasoning": reasoning,
        }

        print(f"[sector_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[sector_model] Error: {e}")
        return {"adjustment": 1.0, "sector": None, "reasoning": "Error fetching sector data"}
