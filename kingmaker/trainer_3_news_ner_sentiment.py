import os
import requests
import spacy
from textblob import TextBlob
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Try to load the NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    nlp = None
    print(f"[NER Sentiment] spaCy model failed to load: {e}")

def fetch_recent_news(ticker):
    if not NEWS_API_KEY:
        raise ValueError("Missing NEWS_API_KEY in environment.")
    try:
        params = {
            "q": ticker,
            "sortBy": "publishedAt",
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "pageSize": 5
        }
        response = requests.get(NEWS_API_URL, params=params, timeout=5)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [article["title"] for article in articles if "title" in article]
    except Exception as e:
        print(f"[NER Sentiment] News API error: {e}")
        return []

def is_relevant(doc, ticker):
    if not doc:
        return False
    for ent in doc.ents:
        if ent.label_ in {"ORG", "GPE", "PRODUCT"} and ticker.lower() in ent.text.lower():
            return True
    return ticker.lower() in doc.text.lower()

def score_sentiment(text):
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity  # -1 to 1
    except Exception as e:
        print(f"[NER Sentiment] Sentiment analysis error: {e}")
        return 0

def run_model(ticker: str):
    if not nlp:
        return {"score": 0, "error": "spaCy model not available"}

    articles = fetch_recent_news(ticker)
    if not articles:
        return {"score": 0, "error": "No news articles found"}

    relevant_scores = []
    for article in articles:
        doc = nlp(article)
        if is_relevant(doc, ticker):
            relevant_scores.append(score_sentiment(article))

    if not relevant_scores:
        return {
            "score": 0,
            "details": {
                "model": "NER News Sentiment",
                "note": "No relevant news found"
            }
        }

    avg_score = sum(relevant_scores) / len(relevant_scores)
    return {
        "score": round(avg_score, 4),
        "details": {
            "model": "NER News Sentiment",
            "articles_considered": articles,
            "avg_sentiment_score": round(avg_score, 4)
        }
    }

# ✅ Fusion-compatible interface
def get_signal(ticker: str):
    try:
        return run_model(ticker)
    except Exception as e:
        return {"score": 0, "error": str(e)}
