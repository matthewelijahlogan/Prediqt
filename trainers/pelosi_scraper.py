import requests

def get_pelosi_trades(page=1, page_size=50):
    url = f"https://bff.capitoltrades.com/trades?page={page}&pageSize={page_size}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://www.capitoltrades.com",
        "Referer": "https://www.capitoltrades.com/trades",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Just return raw trades data for now
        return data.get("trades", [])
    except requests.exceptions.RequestException as e:
        print(f"[pelosi_scraper] Error fetching API: {e}")
        return []

def predict(ticker):
    print(f"[trainer_3_pelosi] Checking trades for {ticker}...")
    trades = get_pelosi_trades()
    matched_trades = [t for t in trades if ticker.upper() in t.get("ticker", "").upper()]

    if not matched_trades:
        return {
            "trainer": "pelosi",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {"matched": False, "reason": "No recent trades found"}
        }

    # Example: dummy prediction based on number of matched trades
    confidence = min(1.0, len(matched_trades) / 10)
    prediction = 1.0 if confidence > 0.5 else 0.0

    return {
        "trainer": "pelosi",
        "prediction": prediction,
        "confidence": confidence,
        "meta": {"matched": True, "trade_count": len(matched_trades)}
    }

if __name__ == "__main__":
    test_tickers = ["AAPL", "TSLA", "GOOGL", "AMZN", "MSFT"]

    for ticker in test_tickers:
        result = predict(ticker)
        print(f"{ticker} result: {result}")
