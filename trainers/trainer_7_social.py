from trainers.reddit_scraper import predict as reddit_predict

def predict(ticker: str, horizon: str = "day") -> dict:
    """
    Social sentiment trainer using Reddit data.
    """
    print(f"[trainer_7_social] Scraping social media buzz for {ticker}...")

    try:
        result = reddit_predict(ticker)
        prediction = result.get("adjustment", 1.0) - 1.0  # convert multiplier back to delta
        adjustment = result.get("adjustment", 1.0)

        # Buzz level logic
        num_posts = result.get("num_posts", 0)
        if num_posts > 20:
            buzz_level = "high"
        elif num_posts > 5:
            buzz_level = "medium"
        else:
            buzz_level = "low"

        return {
            "trainer": "social",
            "prediction": round(prediction, 5),
            "adjustment": round(adjustment, 5),
            "confidence": result.get("confidence", 0),
            "meta": {
                "buzz_level": buzz_level,
                "sentiment_score": result.get("sentiment_score", 0),
                "num_posts": num_posts,
            }
        }

    except Exception as e:
        print(f"[trainer_7_social] Error: {e}")
        return {
            "trainer": "social",
            "prediction": 0.0,
            "adjustment": 1.0,
            "confidence": 0.0,
            "meta": {
                "buzz_level": "unknown",
                "sentiment_score": 0,
                "num_posts": 0,
                "error": str(e)
            }
        }

if __name__ == "__main__":
    test_ticker = "AAPL"
    print(predict(test_ticker))
