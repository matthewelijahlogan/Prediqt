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
    from collections import defaultdict

    accuracies = []
    within_threshold_count = 0
    total_count = 0
    model_scores = defaultdict(list)

    for entry in batch_results:
        result = entry.get("result", {})
        actual = get_actual_price(entry["ticker"])
        if not actual:
            continue

        # Check fusion model accuracy
        fusion_pred = result.get("predicted_next_close")
        if fusion_pred:
            total_count += 1
            error = abs(fusion_pred - actual) / actual
            accuracies.append(1 - error)
            if error <= threshold:
                within_threshold_count += 1

        # Score each model
        for model, model_result in result.items():
            if isinstance(model_result, dict) and "predicted_close" in model_result:
                pred = model_result["predicted_close"]
                error = abs(pred - actual) / actual
                model_scores[model].append(1 - error)

    # Averages
    average_accuracy = sum(accuracies) / len(accuracies) if accuracies else None
    within_threshold_pct = (within_threshold_count / total_count) if total_count else None

    # Per-model average
    model_averages = {k: sum(v) / len(v) for k, v in model_scores.items() if v}

    accuracy_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "average_accuracy": average_accuracy,
        "num_predictions": total_count,
        "within_threshold_pct": within_threshold_pct,
        "model_accuracies": model_averages
    }

    append_to_json_log(ACCURACY_LOG_FILE, [accuracy_entry])
    print(f"[auto_trainer] Avg: {average_accuracy:.4f}, Within {threshold*100:.1f}%: {within_threshold_pct:.2%}")
    update_from_log(LOG_FILE)  # update fusion weights from the log


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
