import requests
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta

NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"
API_KEY = "0de95c014fa249419f4c8a7b839ae2a9" 
DEFAULT_ARTICLE_LIMIT = 20
DAYS_LOOKBACK = 3

analyzer = SentimentIntensityAnalyzer()

def fetch_news_headlines(ticker: str, limit: int = DEFAULT_ARTICLE_LIMIT) -> list:
    try:
        query_date = (datetime.utcnow() - timedelta(days=DAYS_LOOKBACK)).strftime("%Y-%m-%d")
        params = {
            "q": ticker,
            "from": query_date,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": limit,
            "apiKey": API_KEY
        }
        response = requests.get(NEWS_API_ENDPOINT, params=params)
        data = response.json()
        if data.get("status") != "ok" or not data.get("articles"):
            return []
        return [article["title"] for article in data["articles"]]
    except Exception as e:
        print(f"[trainer_2_sentiment] Error fetching news: {e}")
        return []

def analyze_sentiment(headlines: list) -> dict:
    if not headlines:
        return {
            "score": 0.0,
            "confidence": 0.0,
            "headline_count": 0,
            "avg_score": 0.0
        }

    scores = []
    for title in headlines:
        vs = analyzer.polarity_scores(title)
        scores.append(vs["compound"])

    avg_score = sum(scores) / len(scores)

    # Normalize to range [-0.05, +0.05] for fusion scaling
    scaled_score = max(-0.05, min(0.05, avg_score))

    # Confidence: based on # of headlines (up to 1.0)
    confidence = min(1.0, len(headlines) / 20)

    return {
        "score": round(scaled_score, 5),
        "confidence": round(confidence, 3),
        "headline_count": len(headlines),
        "avg_score": round(avg_score, 4)
    }

def predict(ticker: str, horizon: str = "day") -> dict:
    headlines = fetch_news_headlines(ticker)
    sentiment = analyze_sentiment(headlines)

    return {
        "trainer": "sentiment",
        "prediction": sentiment["score"],        # Normalized sentiment score
        "confidence": sentiment["confidence"],   # Confidence for fusion
        "meta": {
            "headline_count": sentiment["headline_count"],
            "avg_score": sentiment["avg_score"]
        }
    }
