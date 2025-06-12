# trainer_7_social.py

from .reddit_scraper import predict as reddit_predict

def predict(ticker: str):
    """
    Social sentiment trainer using Reddit data.
    """
    print(f"[trainer_7_social] Scraping social media buzz for {ticker}...")
    try:
        result = reddit_predict(ticker)
        return {
            "adjustment": result.get("adjustment", 1.0),
            "buzz_level": "high" if result.get("num_posts", 0) > 20 else "medium" if result.get("num_posts", 0) > 5 else "low",
            "sentiment_score": result.get("sentiment_score", 0),
            "confidence": result.get("confidence", 0),
            "num_posts": result.get("num_posts", 0),
        }
    except Exception as e:
        print(f"[trainer_7_social] Error: {e}")
        return {
            "adjustment": 1.0,
            "buzz_level": "unknown",
            "sentiment_score": 0,
            "confidence": 0,
            "num_posts": 0,
        }

if __name__ == "__main__":
    # Test run
    test_ticker = "AAPL"
    print(predict(test_ticker))
