import os
import requests
from textblob import TextBlob
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_news_headlines(ticker, limit=20):
    """
    Fetch recent news articles for a given ticker using NewsAPI.
    Replace with your own news source if needed.
    """
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={ticker}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize={limit}&"
        f"apiKey={NEWS_API_KEY}"
    )
    headers = {"User-Agent": "prediqt-news/1.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [
            article.get("title", "") + ". " + (article.get("description") or "")
            for article in articles
        ]
    except Exception as e:
        print(f"[news_model] Error fetching news: {e}")
        return []

def analyze_sentiment(texts):
    """
    Analyze sentiment of a list of news texts using TextBlob.
    Returns average polarity.
    """
    if not texts:
        return 0.0
    polarity = sum(TextBlob(text).sentiment.polarity for text in texts)
    return polarity / len(texts)

def predict(ticker: str):
    print(f"[trainer_17_news] Fetching and analyzing news for {ticker}...")
    
    try:
        articles = fetch_news_headlines(ticker)
        sentiment_score = analyze_sentiment(articles)
        confidence = min(1.0, len(articles) / 20)  # Cap at 20 articles

        # Convert to adjustment: ±5% max impact
        adjustment = 1.0 + (sentiment_score * 0.05)

        result = {
            "trainer": "news_model",
            "adjustment": round(adjustment, 4),
            "confidence": round(confidence, 2),
            "sentiment_score": round(sentiment_score, 3),
            "num_articles": len(articles),
            "meta": {
                "source": "NewsAPI",
                "note": "Sentiment based on headlines and descriptions"
            }
        }

        print(f"[news_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[news_model] Error: {e}")
        return {
            "trainer": "news_model",
            "adjustment": 1.0,
            "confidence": 0.0,
            "sentiment_score": 0.0,
            "num_articles": 0,
            "meta": {
                "error": str(e)
            }
        }

if __name__ == "__main__":
    print(predict("AAPL"))
