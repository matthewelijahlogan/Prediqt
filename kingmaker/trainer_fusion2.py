import os
import json
import numpy as np
from datetime import datetime

from kingmaker import (
    trainer_1_transformer_embeddings,
    trainer_2_lstm_price_trend,
    trainer_3_news_ner_sentiment,
    trainer_4_local_llm_sentiment,
    trainer_5_options_pressure,
    trainer_6_dark_pool_volume,
    trainer_7_ai_sentiment_synthesis,
    trainer_8_fund_flow_inference,
    trainer_9_intraday_price_action,
    trainer_11_rsi,
    trainer_12_macd,
    trainer_13_bollinger_bands,
    trainer_14_sma_crossover,
)

# === Logging setup ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "predictive_logs")
os.makedirs(LOG_DIR, exist_ok=True)
PREDICTIONS_LOG2_FILE = os.path.join(LOG_DIR, "predictions_log2.json")

# === Default Weights ===
DEFAULT_WEIGHTS = {
    "trainer_1": 0.08,
    "trainer_2": 0.08,
    "trainer_3": 0.08,
    "trainer_4": 0.08,
    "trainer_5": 0.08,
    "trainer_6": 0.08,
    "trainer_7": 0.08,
    "trainer_8": 0.08,
    "trainer_9": 0.08,
    "trainer_11": 0.07,
    "trainer_12": 0.07,
    "trainer_13": 0.07,
    "trainer_14": 0.07,
}

def append_prediction_to_log2(entry):
    try:
        if not os.path.exists(PREDICTIONS_LOG2_FILE):
            log = []
        else:
            with open(PREDICTIONS_LOG2_FILE, "r") as f:
                log = json.load(f)
    except json.JSONDecodeError:
        log = []

    log.append(entry)

    with open(PREDICTIONS_LOG2_FILE, "w") as f:
        json.dump(log, f, indent=2)

def load_weights_from_summary(path="predictive_summary.json"):
    if not os.path.exists(path):
        print(f"[fusion2] Weights summary '{path}' not found. Using default weights.")
        return DEFAULT_WEIGHTS

    try:
        with open(path, "r") as f:
            summary = json.load(f)
        acc = summary.get("model_accuracies", {})
        total = sum(acc.get(k, 0) for k in DEFAULT_WEIGHTS.keys())
        if total == 0:
            return DEFAULT_WEIGHTS
        weights = {k: acc.get(k, 0) / total for k in DEFAULT_WEIGHTS.keys()}
        return weights
    except Exception as e:
        print(f"[fusion2] Error loading weights: {e}")
        return DEFAULT_WEIGHTS

# === Signal extractors mapped ===
TRAINER_FUNCTIONS = {
    "trainer_1": lambda t: trainer_1_transformer_embeddings.predict(t),
    "trainer_2": lambda t: trainer_2_lstm_price_trend.predict(t),
    "trainer_3": lambda t: trainer_3_news_ner_sentiment.predict(t),
    "trainer_4": lambda t: trainer_4_local_llm_sentiment.predict(t),
    "trainer_5": lambda t: trainer_5_options_pressure.predict(t),
    "trainer_6": lambda t: trainer_6_dark_pool_volume.predict(t),
    "trainer_7": lambda t: trainer_7_ai_sentiment_synthesis.predict(t),
    "trainer_8": lambda t: trainer_8_fund_flow_inference.predict(t),
    "trainer_9": lambda t: trainer_9_intraday_price_action.train_and_predict(t),
    "trainer_11": lambda t: trainer_11_rsi.predict(t),
    "trainer_12": lambda t: trainer_12_macd.predict(t),
    "trainer_13": lambda t: trainer_13_bollinger_bands.predict(t),
    "trainer_14": lambda t: trainer_14_sma_crossover.predict(t),
}

# === Signal score extractors (adjust per trainer if needed) ===
def extract_score(trainer_key, res):
    key_map = {
        "trainer_1": "score",
        "trainer_2": "trend_signal",
        "trainer_3": "sentiment_score",
        "trainer_4": "score",
        "trainer_5": "options_pressure_score",
        "trainer_6": "dark_pool_score",
        "trainer_7": "synthetic_sentiment_score",
        "trainer_8": "fund_flow_score",
        "trainer_9": "predicted_next_close",
        "trainer_11": "rsi_signal",
        "trainer_12": "macd_signal",
        "trainer_13": "bb_signal",
        "trainer_14": "sma_crossover_signal",
    }

    if trainer_key == "trainer_9":
        try:
            import yfinance as yf
            data = yf.Ticker(res["ticker"]).history(period="5d", interval="1d")
            last_close = data['Close'].iloc[-1]
            predicted = res.get("predicted_next_close")
            return (predicted - last_close) / last_close
        except Exception:
            return None

    return res.get(key_map.get(trainer_key)) or res.get("score")

def fuse_all_trainer_signals(ticker: str):
    results = {}
    errors = {}
    weights = {}

    total_weight = 0.0
    weighted_sum = 0.0
    weighted_price_sum = 0.0  # <--- New

    for trainer in TRAINER_FUNCTIONS:
        try:
            result = TRAINER_FUNCTIONS[trainer](ticker)
            if result is None:
                raise ValueError("No result returned")

            if isinstance(result, dict):
                score = result.get("score")
                price = result.get("predicted_next_close")  # <--- Add this
            else:
                score = result
                price = None

            results[trainer] = score
            weight = TRAINER_WEIGHTS.get(trainer, 0.05)
            weights[trainer] = weight

            if score is not None:
                weighted_sum += score * weight
                total_weight += weight

            if price is not None:
                weighted_price_sum += price * weight  # <--- Add this
        except Exception as e:
            errors[trainer] = str(e)

    fused_score = (weighted_sum / total_weight) if total_weight else None
    fused_price = (weighted_price_sum / total_weight) if total_weight else None  # <--- Add this

    return {
        "ticker": ticker,
        "fused_score": fused_score,
        "predicted_next_close": fused_price,  # <--- Add this
        "individual_scores": results,
        "errors": errors,
        "weights_used": weights,
        "model": "trainer_fusion2"
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python trainer_fusion2.py <TICKER>")
        sys.exit(1)

    ticker = sys.argv[1].upper().strip()
    fusion_result = fuse_all_trainer_signals(ticker)

    print(json.dumps(fusion_result, indent=2))

    if "fused_score" in fusion_result:
        append_prediction_to_log2({
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "fused_score": fusion_result["fused_score"],
            "individual_scores": fusion_result["individual_scores"],
            "errors": fusion_result["errors"],
            "weights_used": fusion_result["weights_used"],
            "model": "trainer_fusion2"
        })
    
def update_from_log_kingmaker(log_file_path):
    try:
        with open(log_file_path, "r") as f:
            log_data = json.load(f)
    except Exception as e:
        print(f"[trainer_fusion2] ❌ Failed to read log: {e}")
        return

    print(f"[trainer_fusion2] 🔁 Updating fusion model from {log_file_path}...")

    for entry in log_data[-10:]:  # last 10 entries, as example
        ticker = entry.get("ticker")
        if not ticker:
            continue

        result = fuse_all_trainer_signals(ticker)
        if "fused_score" in result:
            append_prediction_to_log2({
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": ticker,
                "fused_score": result["fused_score"],
                "predicted_next_close": result["predicted_next_close"],
                "individual_scores": result["individual_scores"],
                "errors": result["errors"],
                "weights_used": result["weights_used"],
                "model": "trainer_fusion2"
            })
        else:
            print(f"[trainer_fusion2] ⚠️ Could not fuse signal for {ticker}: {result.get('error')}")
