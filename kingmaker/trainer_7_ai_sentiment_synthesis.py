# file: kingmaker/trainer_7_ai_sentiment_synthesis.py

import os
import requests
import yfinance as yf
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import praw
from dotenv import load_dotenv

load_dotenv()

# Load Reddit API keys
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='prediqt-sentiment-agent'
)

analyzer = SentimentIntensityAnalyzer()
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

def get_news_sentiment(ticker):
    try:
        params = {"q": ticker, "language": "en", "sortBy": "publishedAt", "pageSize": 10, "apiKey": NEWS_API_KEY}
        response = requests.get("https://newsapi.org/v2/everything", params=params).json()
        articles = response.get("articles", [])
        scores = [
            analyzer.polarity_scores(f"{a.get('title', '')} {a.get('description', '')}")['compound']
            for a in articles
        ]
        return sum(scores) / len(scores) if scores else 0.0
    except Exception as e:
        return 0.0

def get_social_sentiment(ticker, subreddit="stocks", limit=50):
    try:
        posts = reddit.subreddit(subreddit).search(ticker, limit=limit, sort="new")
        scores = [analyzer.polarity_scores(f"{p.title} {p.selftext}")['compound'] for p in posts]
        return sum(scores) / len(scores) if scores else 0.0
    except Exception:
        return 0.0

def get_rsi_sentiment(ticker, period: int = 14):
    try:
        data = yf.Ticker(ticker).history(period="2mo", interval="1d")
        if data.empty or len(data) < period:
            return 0.0
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        last_rsi = rsi.iloc[-1]
        if last_rsi <= 30:
            return 1.0  # Oversold (bullish)
        elif last_rsi >= 70:
            return -1.0  # Overbought (bearish)
        else:
            return 0.0  # Neutral
    except:
        return 0.0

def run_model(ticker: str):
    news = get_news_sentiment(ticker)
    social = get_social_sentiment(ticker)
    rsi_sentiment = get_rsi_sentiment(ticker)

    # Weighted average
    combined_raw = (news * 0.4) + (social * 0.4) + (rsi_sentiment * 0.2)
    score = round((combined_raw + 1) / 2, 4)  # Normalize to 0–1

    return {
        "score": score,
        "details": {
            "model": "AISentimentSynth",
            "news": round(news, 4),
            "social": round(social, 4),
            "rsi_sentiment": rsi_sentiment
        }
    }

def get_signal(ticker: str):
    return run_model(ticker)

if __name__ == "__main__":
    print(get_signal("AAPL"))
