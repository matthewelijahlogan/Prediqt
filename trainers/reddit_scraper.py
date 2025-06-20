import requests
from textblob import TextBlob

def fetch_reddit_posts(ticker: str, limit: int = 30) -> list[str]:
    """
    Fetch recent Reddit posts mentioning the ticker symbol.
    Uses Reddit's public search API (no login needed).
    """
    url = f"https://www.reddit.com/search.json?q={ticker}&limit={limit}&sort=new"
    headers = {"User-Agent": "prediqt-bot/0.1"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        posts = data.get("data", {}).get("children", [])
        # Combine title + selftext for sentiment analysis
        return [post["data"]["title"] + " " + post["data"].get("selftext", "") for post in posts]
    except Exception as e:
        print(f"[reddit_scraper] Error fetching Reddit posts: {e}")
        return []

def analyze_sentiment(texts: list[str]) -> float:
    """
    Simple sentiment analysis using TextBlob.
    Returns average polarity (-1 negative, 1 positive).
    """
    if not texts:
        return 0.0
    total_polarity = sum(TextBlob(text).sentiment.polarity for text in texts)
    return total_polarity / len(texts)

def predict(ticker: str) -> dict:
    print(f"[reddit_scraper] Scraping Reddit posts for {ticker}...")
    posts = fetch_reddit_posts(ticker)
    sentiment_score = analyze_sentiment(posts)
    confidence = min(1.0, len(posts) / 30)  # Confidence based on number of posts found

    result = {
        "adjustment": 1 + sentiment_score * 0.05,  # small multiplier effect around 1.0
        "sentiment_score": round(sentiment_score, 3),
        "confidence": round(confidence, 2),
        "num_posts": len(posts),
    }

    print(f"[reddit_scraper] Result: {result}")
    return result

if __name__ == "__main__":
    test_ticker = "AAPL"
    predict(test_ticker)
