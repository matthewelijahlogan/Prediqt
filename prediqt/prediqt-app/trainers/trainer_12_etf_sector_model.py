# trainer_12_etf_sector_model.py

import yfinance as yf

ticker_to_etf = {
    # Tech
    "AAPL": "XLK", "MSFT": "XLK", "GOOGL": "XLK", "NVDA": "XLK",
    # Finance
    "JPM": "XLF", "BAC": "XLF", "WFC": "XLF",
    # Healthcare
    "JNJ": "XLV", "PFE": "XLV",
    # Energy
    "XOM": "XLE", "CVX": "XLE",
    # Consumer Discretionary
    "AMZN": "XLY", "TSLA": "XLY",
    # Industrial
    "BA": "XLI", "GE": "XLI",
    # Default fallback
    "DEFAULT": "SPY"
}

def get_correlated_etf(ticker):
    return ticker_to_etf.get(ticker.upper(), ticker_to_etf["DEFAULT"])

def predict(ticker: str):
    print(f"[trainer_12_etf_sector] Evaluating sector ETF correlation for {ticker}...")
    
    try:
        etf = get_correlated_etf(ticker)
        data = yf.Ticker(etf).history(period="2d", interval="1h")

        if data.empty or len(data) < 2:
            print("[etf_sector_model] Not enough ETF data.")
            return {"adjustment": 1.0, "reason": "insufficient_etf_data"}

        latest_close = data["Close"].iloc[-1]
        previous_close = data["Close"].iloc[-2]

        change_pct = (latest_close - previous_close) / previous_close
        adjustment = round(1 + change_pct, 4)  # e.g., +2% change => 1.02

        output = {
            "adjustment": adjustment,
            "etf": etf,
            "etf_price_change_pct": round(change_pct * 100, 2),
            "etf_latest_price": round(latest_close, 2),
            "etf_previous_price": round(previous_close, 2)
        }

        print(f"[etf_sector_model] Output: {output}")
        return output

    except Exception as e:
        print(f"[etf_sector_model] Error: {e}")
        return {"adjustment": 1.0, "error": str(e)}
