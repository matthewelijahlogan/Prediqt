# file: kingmaker/news_fetcher.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_recent_news(ticker: str, max_articles: int = 5) -> list[str]:
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={ticker}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize={max_articles}&"
        f"apiKey={NEWS_API_KEY}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [
            f"{article['title']} - {article.get('description', '')}".strip()
            for article in articles
        ]
    except Exception as e:
        print(f"[NewsFetcher] Error fetching news: {e}")
        return []
