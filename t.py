from trainer_8_sector import predict as sector_predict

def test_sector():
    tickers = ["AAPL", "TSLA", "GOOGL"]
    for ticker in tickers:
        print(f"\nTesting sector trainer for {ticker}...")
        result = sector_predict(ticker)
        print(result)
        assert "prediction" in result
        assert "adjustment" in result
        assert "confidence" in result
        assert "meta" in result
        print("Test passed.")

if __name__ == "__main__":
    test_sector()
