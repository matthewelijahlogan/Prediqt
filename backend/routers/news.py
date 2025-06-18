# backend/routers/news.py

import os
import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/api/news")
def get_news():
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return JSONResponse(content={"error": "Missing API key"}, status_code=500)

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "category": "business",
        "language": "en",
        "pageSize": 10,
        "apiKey": api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        headlines = [a["title"] for a in articles if "title" in a]
        return {"headlines": headlines}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
