"""
Uses transformer-based language models (like FinBERT or BERTweet) to extract
semantic embeddings from financial news, tweets, and sentiment sources. The embeddings
are then used to generate a predictive score for a given ticker.
"""

from transformers import pipeline, AutoTokenizer, AutoModel
import torch
import yfinance as yf
from kingmaker.news_fetcher import fetch_recent_news  # ✅ Use real news API

MODEL_NAME = "ProsusAI/finbert"

class TransformerEmbeddingPredictor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModel.from_pretrained(MODEL_NAME)
        self.sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL_NAME)

    def get_news(self, ticker):
        return fetch_recent_news(ticker)  # ✅ Pull real headlines

    def score_sentiment(self, news_texts):
        sentiments = self.sentiment_pipeline(news_texts)
        score = sum(
            s['score'] if s['label'].lower() == 'positive' else -s['score']
            for s in sentiments
        ) / len(sentiments)
        return score  # Should be roughly in range [-1, 1]

    def predict(self, ticker):
        news = self.get_news(ticker)
        if not news:
            return {
                "score": 0,
                "details": {
                    "news_used": [],
                    "predicted_next_close": None,
                    "note": "No news available"
                }
            }

        sentiment_score = self.score_sentiment(news)
        recent_price = yf.Ticker(ticker).history(period="5d")["Close"].mean()
        prediction = recent_price * (1 + sentiment_score * 0.05)

        return {
            "score": round(sentiment_score, 4),
            "details": {
                "news_used": news,
                "predicted_next_close": round(prediction, 2)
            }
        }

# ✅ Required fusion interface
def get_signal(ticker: str):
    try:
        model = TransformerEmbeddingPredictor()
        return model.predict(ticker)
    except Exception as e:
        return {"score": 0, "error": str(e)}

if __name__ == "__main__":
    print(get_signal("AAPL"))
