from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from datetime import datetime
import asyncio
import os

from auto_trainer import start_scheduler
from train_predictor import train_and_predict
from enum import Enum

# Enum for prediction horizon
class HorizonEnum(str, Enum):
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"

# Initialize FastAPI app
app = FastAPI()

# Environment-based origin config
is_dev = os.environ.get("ENV", "dev") == "dev"

allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

if not is_dev:
    allowed_origins.append("https://prediqt.onrender.com")

# Only ONE CORS middleware registration!
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    start_scheduler()

# --- PREDICTION ROUTE ---
@app.get("/predict/{ticker}")
async def predict(ticker: str, horizon: HorizonEnum = HorizonEnum.hour):
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, train_and_predict, ticker, horizon)
        return {
            "ticker": ticker.upper(),
            "horizon": horizon,
            "predicted_next_close": result["predicted_next_close"],
            "model_mse": result.get("model_mse"),
            "used_models": result.get("used_models")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- TICKER ROUTE (LAST MARKET CLOSE) ---
@app.get("/ticker/{ticker}")
async def get_ticker_data(ticker: str):
    import yfinance as yf
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="1d")
        if hist.empty:
            raise HTTPException(status_code=404, detail="Ticker data not found")
        data = hist.iloc[-1]
        return {
            "ticker": ticker.upper(),
            "current_price": data["Close"],
            "open_price": data["Open"],
            "high_price": data["High"],
            "low_price": data["Low"],
            "volume": data["Volume"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- NEW REAL-TIME QUOTE ROUTE ---
@app.get("/api/quote")
async def get_realtime_quote(ticker: str = Query(...)):
    import yfinance as yf
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        return {
            "ticker": ticker.upper(),
            "price": info.get("regularMarketPrice"),
            "change": info.get("regularMarketChange"),
            "percent_change": info.get("regularMarketChangePercent"),
            "volume": info.get("volume"),
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- FRONTEND SETUP ---
frontend_path = os.path.join(os.path.dirname(__file__), "www")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/index.html")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/about.html")
def serve_about():
    return FileResponse(os.path.join(frontend_path, "about.html"))

@app.get("/contact.html")
def serve_contact():
    return FileResponse(os.path.join(frontend_path, "contact.html"))

# Serve static files like JS/CSS/images
app.mount("/css", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_path, "js")), name="js")
app.mount("/img", StaticFiles(directory=os.path.join(frontend_path, "img")), name="img")
app.mount("/fonts", StaticFiles(directory=os.path.join(frontend_path, "fonts")), name="fonts")

# --- LOCAL DEV ENTRY POINT ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
