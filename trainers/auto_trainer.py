import random
import json
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from train_predictor import train_and_predict
from trainers.trainer_16_predictivelog import update_from_log



# Constants and paths
TICKER_LIST_FILE = "tickers.txt"   # Plain text file with one ticker per line
LOG_DIR = "predictive_logs"
LOG_FILE = os.path.join(LOG_DIR, "predictions_log.json")
ACCURACY_LOG_FILE = os.path.join(LOG_DIR, "accuracy_log.json")
BATCH_SIZE = 100

os.makedirs(LOG_DIR, exist_ok=True)

def load_tickers():
    with open(TICKER_LIST_FILE, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
    return tickers

async def run_predictions():
    tickers = load_tickers()
    selected = random.sample(tickers, min(BATCH_SIZE, len(tickers)))

    batch_results = []
    print(f"[auto_trainer] Starting prediction batch at {datetime.utcnow().isoformat()}")

    loop = asyncio.get_running_loop()
    for ticker in selected:
        try:
            # Run synchronous train_and_predict in executor to avoid blocking event loop
            result = await loop.run_in_executor(None, train_and_predict, ticker, "day")

            result_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": ticker,
                "result": result
            }
            batch_results.append(result_log)
            print(f"[auto_trainer] Prediction done for {ticker}")
        except Exception as e:
            print(f"[auto_trainer] Error for {ticker}: {e}")

    append_to_json_log(LOG_FILE, batch_results)

    try:
        update_metrics_and_fusion(batch_results)
    except Exception as e:
        print(f"[auto_trainer] Error updating fusion model: {e}")

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

def update_metrics_and_fusion(batch_results):
    """
    Evaluate prediction accuracy on batch_results,
    append accuracy to accuracy log,
    and update fusion model weights.
    """
    accuracies = []
    for entry in batch_results:
        pred = entry["result"].get("predicted_next_close")
        actual = get_actual_price(entry["ticker"])
        if actual and pred:
            acc = 1 - abs(pred - actual) / actual
            accuracies.append(acc)
    average_accuracy = sum(accuracies) / len(accuracies) if accuracies else None

    accuracy_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "average_accuracy": average_accuracy,
        "num_predictions": len(batch_results)
    }
    append_to_json_log(ACCURACY_LOG_FILE, [accuracy_entry])

    print(f"[auto_trainer] Average accuracy for batch: {average_accuracy}")

    update_from_log(LOG_FILE)  # Update fusion model weights

def get_actual_price(ticker: str):
    import yfinance as yf
    try:
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) >= 2:
            # Close price of the most recent day
            return data["Close"].iloc[-1]
    except Exception as e:
        print(f"[auto_trainer] Failed to get actual price for {ticker}: {e}")
    return None

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_predictions, "interval", hours=2, next_run_time=datetime.utcnow())
    scheduler.start()
    print("[auto_trainer] Scheduler started, running every 2 hours.")

async def main():
    start_scheduler()
    await asyncio.Event().wait()  # Keep running forever

if __name__ == "__main__":
    import asyncio

    # Run a batch immediately for testing
    asyncio.run(run_predictions())

    # Then start the scheduler to run every 2 hours
    start_scheduler()
    asyncio.get_event_loop().run_forever()
