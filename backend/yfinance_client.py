import yfinance as yf

def get_quote(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "ticker": ticker.upper(),
        "price": info.get("regularMarketPrice"),
        "change_percent": info.get("regularMarketChangePercent"),
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "sector": info.get("sector"),
    }
