# t.py - Test runner for trainer_17_news.py

from trainer_17_news import predict

tickers = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN"]

print("Starting news model tests...\n")

for ticker in tickers:
    print(f"Testing news model for {ticker}...")
    result = predict(ticker)
    print(result)
    print("Test completed.\n")
