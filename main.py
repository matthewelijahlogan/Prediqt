from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from datetime import datetime
import asyncio
import os

from train_predictor import train_and_predict
from predictor import get_top_movers_and_losers
from enum import Enum

class HorizonEnum(str, Enum):
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


top_movers = []
top_losers = []

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

@app.get("/top-movers")
async def top_movers_api():
    return {"top_movers": top_movers}

@app.get("/top-losers")
async def top_losers_api():
    return {"top_losers": top_losers}

def update_top_movers_job():
    global top_movers, top_losers
    print(f"[{datetime.now()}] Updating top movers and losers...")
    try:
        movers, losers = get_top_movers_and_losers()
        top_movers = movers
        top_losers = losers
        print(f"[{datetime.now()}] Top movers and losers updated successfully.")
    except Exception as e:
        print(f"[{datetime.now()}] Failed to update top movers: {e}")

scheduler = AsyncIOScheduler(timezone=pytz.timezone("US/Eastern"))
scheduler.add_job(update_top_movers_job, 'cron', hour=4, minute=0)

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, update_top_movers_job)

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
    
    
frontend_path = os.path.join(os.path.dirname(__file__), "www")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # fallback to 8000 locally
    uvicorn.run("main:app", host="0.0.0.0", port=port)
