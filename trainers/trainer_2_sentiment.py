# trainer_2_sentiment.py

import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def get_news_headlines(ticker):
    # Use Finviz for fast access to public financial news
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[trainer_2_sentiment] Error fetching news: {e}")
        return []

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Finviz stores headlines in a table with class "fullview-news-outer"
    news_table = soup.find('table', class_='fullview-news-outer')
    if not news_table:
        return []

    rows = news_table.find_all('tr')
    headlines = [row.a.text for row in rows if row.a]

    return headlines[:10]  # limit to last 10 headlines


def analyze_sentiment(headlines):
    analyzer = SentimentIntensityAnalyzer()
    scores = []

    for headline in headlines:
        vs = analyzer.polarity_scores(headline)
        scores.append(vs['compound'])  # compound score is between -1 and 1

    if not scores:
        return 0.0, 0.0

    sentiment_score = sum(scores) / len(scores)
    confidence = min(1.0, len(scores) / 10.0 + 0.5)  # more headlines = more confidence

    return round(sentiment_score, 3), round(confidence, 3)


def predict(ticker: str) -> dict:
    print(f"[trainer_2_sentiment] Running sentiment analysis for {ticker}...")

    headlines = get_news_headlines(ticker)
    if not headlines:
        print("[trainer_2_sentiment] No headlines found. Defaulting to neutral sentiment.")
        return {
            "sentiment_score": 0.0,
            "confidence": 0.0
        }

    sentiment_score, confidence = analyze_sentiment(headlines)

    result = {
        "sentiment_score": sentiment_score,
        "confidence": confidence
    }

    print(f"[trainer_2_sentiment] Result: {result}")
    return result
