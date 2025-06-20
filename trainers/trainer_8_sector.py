import yfinance as yf

# Mapping of sectors to representative ETFs, including "Consumer Cyclical"
SECTOR_ETFS = {
    "Technology": "XLK",
    "Consumer Discretionary": "XLY",
    "Consumer Cyclical": "XLY",           # Added this alias for TSLA etc.
    "Health Care": "XLV",
    "Financial Services": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication Services": "XLC",
    "Consumer Staples": "XLP",
}

def predict(ticker: str, horizon: str = "day") -> dict:
    print(f"[trainer_8_sector] Checking sector trends for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Try sector first, then fallback to industry if sector is missing
        sector = info.get("sector") or info.get("industry") or None

        if not sector:
            return {
                "trainer": "sector",
                "prediction": 0.0,
                "confidence": 0.0,
                "meta": {
                    "sector": None,
                    "reasoning": "No sector or industry info found"
                }
            }

        sector_etf = SECTOR_ETFS.get(sector)
        if not sector_etf:
            return {
                "trainer": "sector",
                "prediction": 0.0,
                "confidence": 0.0,
                "meta": {
                    "sector": sector,
                    "reasoning": f"No ETF mapping for sector '{sector}'"
                }
            }

        etf = yf.Ticker(sector_etf)
        hist = etf.history(period="2d")
        if len(hist) < 2:
            return {
                "trainer": "sector",
                "prediction": 0.0,
                "confidence": 0.5,
                "meta": {
                    "sector": sector,
                    "sector_etf": sector_etf,
                    "reasoning": "Insufficient ETF history data"
                }
            }

        # Use iloc to avoid pandas future warning on positional indexing
        last_close = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        pct_change = (last_close - prev_close) / prev_close

        # Clamp delta between -10% and +10%
        prediction = max(-0.1, min(0.1, pct_change))
        # Confidence scaled by absolute % move times 50, capped at 1.0
        confidence = min(1.0, abs(pct_change) * 50)

        result = {
            "trainer": "sector",
            "prediction": round(prediction, 5),
            "confidence": round(confidence, 3),
            "meta": {
                "sector": sector,
                "sector_etf": sector_etf,
                "percent_change": round(pct_change * 100, 2),
                "reasoning": f"{sector_etf} ETF changed {pct_change * 100:.2f}% over last 2 days"
            }
        }

        print(f"[sector_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[sector_model] Error: {e}")
        return {
            "trainer": "sector",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {
                "sector": None,
                "error": str(e),
                "reasoning": "Exception during sector ETF fetch"
            }
        }

if __name__ == "__main__":
    print(predict("AAPL"))
