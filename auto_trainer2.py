# file: auto_trainer2.py

import random
import json
import os
import sys
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

# --- Fix pathing to import from kingmaker and root ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "kingmaker"))

from train_predictor2 import train_and_predict2
from kingmaker.trainer_fusion2 import update_from_log_kingmaker

# Constants and paths
TICKER_LIST_FILE = os.path.join(BASE_DIR, "tickers.txt")  # Use the same ticker list
LOG_DIR = os.path.join(BASE_DIR, "predictive_logs")
KINGMAKER_LOG_FILE = os.path.join(LOG_DIR, "predictions_log2.json")
KINGMAKER_ACCURACY_LOG_FILE = os.path.join(LOG_DIR, "accuracy_log2.json")
BATCH_SIZE = 100

os.makedirs(LOG_DIR, exist_ok=True)

def load_tickers():
    with open(TICKER_LIST_FILE, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
    return tickers

def update_from_log_kingmaker(log_file_path):
    print(f"[trainer_fusion2] 🧭 Attempting to open log: {log_file_path}")


async def run_predictions_kingmaker():
    tickers = load_tickers()
    selected = random.sample(tickers, min(BATCH_SIZE, len(tickers)))

    batch_results = []
    print(f"[auto_trainer2] Starting kingmaker prediction batch at {datetime.utcnow().isoformat()}")

    loop = asyncio.get_running_loop()
    for ticker in selected:
        try:
            # Run sync function in executor to prevent blocking
            result = await loop.run_in_executor(None, train_and_predict2, ticker, "day")
            result_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": ticker,
                "result": result
            }
            batch_results.append(result_log)
            print(f"[auto_trainer2] ✅ Prediction done for {ticker}")
        except Exception as e:
            print(f"[auto_trainer2] ❌ Error for {ticker}: {e}")

    append_to_json_log(KINGMAKER_LOG_FILE, batch_results)

    try:
        update_metrics_and_fusion_kingmaker(batch_results)
    except Exception as e:
        print(f"[auto_trainer2] ⚠️ Error updating kingmaker fusion model: {e}")

def append_to_json_log(filepath, new_data):
    data = []
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    data.extend(new_data)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def update_metrics_and_fusion_kingmaker(batch_results, threshold=0.01):
    accuracies = []
    within_threshold_count = 0
    total_count = 0

    for entry in batch_results:
        pred = entry["result"].get("predicted_next_close")
        actual = get_actual_price(entry["ticker"])
        if actual and pred:
            total_count += 1
            acc = 1 - abs(pred - actual) / actual
            accuracies.append(acc)
            if abs(pred - actual) / actual <= threshold:
                within_threshold_count += 1

    average_accuracy = sum(accuracies) / len(accuracies) if accuracies else None
    within_threshold_pct = (within_threshold_count / total_count) if total_count else None

    accuracy_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "average_accuracy": average_accuracy,
        "num_predictions": len(batch_results),
        "within_threshold_pct": within_threshold_pct
    }
    append_to_json_log(KINGMAKER_ACCURACY_LOG_FILE, [accuracy_entry])

    print(f"[auto_trainer2] Average accuracy for batch: {average_accuracy}")
    print(f"[auto_trainer2] Predictions within {threshold*100:.2f}% of actual: {within_threshold_pct}")

    update_from_log_kingmaker(KINGMAKER_LOG_FILE)

def get_actual_price(ticker: str):
    import yfinance as yf
    try:
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) >= 2:
            return data["Close"].iloc[-1]
    except Exception as e:
        print(f"[auto_trainer2] ⚠️ Failed to get actual price for {ticker}: {e}")
    return None

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_predictions_kingmaker, "interval", hours=2, next_run_time=datetime.utcnow())
    scheduler.start()
    print("[auto_trainer2] 🕒 Scheduler started, running every 2 hours.")

async def main():
    start_scheduler()
    await asyncio.Event().wait()  # keep running

if __name__ == "__main__":
    asyncio.run(run_predictions_kingmaker())
    start_scheduler()
    asyncio.get_event_loop().run_forever()
