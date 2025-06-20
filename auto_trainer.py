# file: auto_trainer.py

import random
import json
import os
import sys
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

# --- Fix pathing so we can import from trainers and root ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "trainers"))

from train_predictor import train_and_predict
from trainer_16_predictivelog import update_from_log

# Constants and paths
TICKER_LIST_FILE = os.path.join(BASE_DIR, "tickers.txt")  # one ticker per line
LOG_DIR = os.path.join(BASE_DIR, "predictive_logs")
LOG_FILE = os.path.join(LOG_DIR, "predictions_log.json")
ACCURACY_LOG_FILE = os.path.join(LOG_DIR, "accuracy_log.json")
BATCH_SIZE = 100

os.makedirs(LOG_DIR, exist_ok=True)


def load_tickers():
    if not os.path.exists(TICKER_LIST_FILE):
        print(f"[auto_trainer] ❌ Ticker list file not found: {TICKER_LIST_FILE}")
        return ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]  # fallback tickers

    with open(TICKER_LIST_FILE, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
    if not tickers:
        print("[auto_trainer] ❌ No tickers found in file. Using fallback list.")
        return ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]
    return tickers


async def run_predictions():
    tickers = load_tickers()
    selected = random.sample(tickers, min(BATCH_SIZE, len(tickers)))

    batch_results = []
    print(f"[auto_trainer] 🚀 Starting prediction batch at {datetime.utcnow().isoformat()}")

    loop = asyncio.get_running_loop()
    for ticker in selected:
        try:
            # Run sync function in executor to prevent blocking
            result = await loop.run_in_executor(None, train_and_predict, ticker, "day")
            result_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": ticker,
                "result": result
            }
            batch_results.append(result_log)
            print(f"[auto_trainer] ✅ Prediction done for {ticker}")
        except Exception as e:
            print(f"[auto_trainer] ❌ Error for {ticker}: {e}")

    append_to_json_log(LOG_FILE, batch_results)

    try:
        update_metrics_and_fusion(batch_results)
    except Exception as e:
        print(f"[auto_trainer] ⚠️ Error updating fusion model: {e}")


def append_to_json_log(filepath, new_data):
    data = []
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"[auto_trainer] ⚠️ JSON decode error in {filepath}. Starting fresh.")
                data = []

    data.extend(new_data)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def update_metrics_and_fusion(batch_results, threshold=0.01):
    """
    Evaluate prediction accuracy on batch_results,
    append accuracy and 'within threshold' metric to accuracy log,
    and update fusion model weights.
    """
    accuracies = []
    within_threshold_count = 0
    total_count = 0

    for entry in batch_results:
        pred = entry["result"].get("predicted_next_close")
        actual = get_actual_price(entry["ticker"])
        if actual and pred:
            total_count += 1
            relative_error = abs(pred - actual) / actual
            acc = 1 - relative_error
            accuracies.append(acc)
            if relative_error <= threshold:
                within_threshold_count += 1
        else:
            print(f"[auto_trainer] ⚠️ Missing prediction or actual for {entry['ticker']}")

    average_accuracy = sum(accuracies) / len(accuracies) if accuracies else None
    within_threshold_pct = (within_threshold_count / total_count) if total_count else None

    accuracy_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "average_accuracy": average_accuracy,
        "num_predictions": len(batch_results),
        "within_threshold_pct": within_threshold_pct
    }
    append_to_json_log(ACCURACY_LOG_FILE, [accuracy_entry])

    print(f"[auto_trainer] 📊 Avg accuracy: {average_accuracy:.4f}" if average_accuracy else "[auto_trainer] No accuracy stats.")
    print(f"[auto_trainer] ✅ {within_threshold_pct:.2%} within ±{threshold*100:.2f}%") if within_threshold_pct else None

    update_from_log(LOG_FILE)


def get_actual_price(ticker: str):
    import yfinance as yf
    try:
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) >= 2:
            return data["Close"].iloc[-1]
    except Exception as e:
        print(f"[auto_trainer] ⚠️ Failed to get actual price for {ticker}: {e}")
    return None


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_predictions, "interval", hours=2, next_run_time=datetime.utcnow())
    scheduler.start()
    print("[auto_trainer] 🕒 Scheduler started (every 2 hours).")


async def main():
    start_scheduler()
    await asyncio.Event().wait()  # keep running


if __name__ == "__main__":
    try:
        asyncio.run(run_predictions())  # Run one batch immediately
        start_scheduler()

        loop = asyncio.get_event_loop()
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("[auto_trainer] 🛑 Shutting down gracefully.")
