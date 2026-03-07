import json
import os
from typing import List, Dict, Optional
from datetime import datetime

LOG_FILE_PATH = "predictive_logs/predictions_log.json"  # Ensure path matches your logging
SUMMARY_OUTPUT_PATH = "predictive_summary.json"

def load_predictive_log(path: str) -> List[Dict]:
    """Load the prediction log JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Log file not found at {path}")
    with open(path, "r") as f:
        data = json.load(f)
    return data

def calculate_error(predicted: float, actual: float) -> float:
    """Calculate relative error (absolute relative difference)."""
    if actual == 0:
        return float("inf")
    return abs(predicted - actual) / actual

def get_actual_close_from_entry(entry: Dict) -> Optional[float]:
    """
    Extract the actual close price from the log entry.
    Adjust if your logs store actual prices differently.
    """
    actual = entry.get("actual_close")
    if actual is not None:
        return actual

    result = entry.get("result", {})
    return result.get("actual_close")

def extract_predicted_value(model_name: str, submodel_data: dict, full_result: dict) -> Optional[float]:
    """
    Extract predicted value from submodel result for error calculation.
    Adjust logic to fit your prediction data structure.
    """
    base_price = full_result.get("predicted_next_close")
    if model_name == "base":
        return submodel_data.get("predicted_next_close")

    if base_price is None:
        return None

    if model_name == "sentiment":
        sentiment_score = submodel_data.get("sentiment_score", 0)
        return base_price * (1 + (sentiment_score * 0.05))

    if model_name in ["pelosi", "weather", "earnings", "social", "sector", 
                      "insider", "technical", "etf_sector", "volume", "patterns", "volatility"]:
        adjustment = submodel_data.get("adjustment")
        if adjustment is None:
            return None
        return base_price * adjustment

    if model_name == "options":
        strength = submodel_data.get("options_signal_strength", 1)
        confidence = submodel_data.get("options_prediction_confidence", 1)
        return base_price * (1 + (strength * 0.05 * confidence))

    return None

def summarize_predictions(logs: List[Dict]) -> Dict:
    """Summarize prediction logs to evaluate accuracy and stats."""
    total_predictions = 0
    total_error = 0.0
    skipped_entries = 0

    model_error_sums = {}
    model_counts = {}

    for entry in logs:
        total_predictions += 1
        actual = get_actual_close_from_entry(entry)
        if actual is None:
            skipped_entries += 1
            continue

        result = entry.get("result", {})
        predicted = result.get("predicted_next_close")
        if predicted is None:
            skipped_entries += 1
            continue

        total_error += calculate_error(predicted, actual)

        # Evaluate sub-models
        for model_key in [
            "base", "sentiment", "pelosi", "weather", "earnings",
            "social", "sector", "insider", "options", "technical",
            "etf_sector", "volume", "patterns", "volatility"
        ]:
            submodel_data = result.get(model_key)
            if not submodel_data:
                continue

            pred_val = extract_predicted_value(model_key, submodel_data, result)
            if pred_val is None:
                continue

            model_error_sums.setdefault(model_key, 0)
            model_counts.setdefault(model_key, 0)

            sub_err = calculate_error(pred_val, actual)
            model_error_sums[model_key] += sub_err
            model_counts[model_key] += 1

    valid_predictions = total_predictions - skipped_entries
    overall_accuracy = None
    if valid_predictions > 0:
        overall_accuracy = round(1 - (total_error / valid_predictions), 4)
    else:
        print("[trainer_16_predictivelog] Warning: No valid predictions found in logs.")

    model_accuracies = {}
    for model_key, err_sum in model_error_sums.items():
        count = model_counts.get(model_key, 0)
        if count > 0:
            model_accuracies[model_key] = round(1 - (err_sum / count), 4)
        else:
            model_accuracies[model_key] = None

    return {
        "total_predictions": total_predictions,
        "valid_predictions": valid_predictions,
        "skipped_entries": skipped_entries,
        "overall_accuracy": overall_accuracy,
        "model_accuracies": model_accuracies,
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }

def save_summary(summary: Dict, path: str):
    """Save the summary dict to a JSON file."""
    with open(path, "w") as f:
        json.dump(summary, f, indent=4)
    print(f"[trainer_16_predictivelog] Summary saved to {path}")

def predict(ticker: str, horizon: str = "day") -> Dict:
    """
    Build a small adjustment signal from historical predictive accuracy.
    """
    try:
        if not os.path.exists(SUMMARY_OUTPUT_PATH):
            return {
                "trainer": "predictivelog",
                "adjustment": 1.0,
                "confidence": 0.2,
                "meta": {"reason": "summary_missing", "horizon": horizon}
            }

        with open(SUMMARY_OUTPUT_PATH, "r", encoding="utf-8") as f:
            summary = json.load(f)

        overall_accuracy = summary.get("overall_accuracy")
        if overall_accuracy is None:
            return {
                "trainer": "predictivelog",
                "adjustment": 1.0,
                "confidence": 0.2,
                "meta": {"reason": "overall_accuracy_missing", "horizon": horizon}
            }

        adjustment = max(0.95, min(1.05, 1 + ((overall_accuracy - 0.5) * 0.1)))
        confidence = max(0.2, min(0.9, float(overall_accuracy)))

        return {
            "trainer": "predictivelog",
            "adjustment": round(adjustment, 4),
            "confidence": round(confidence, 4),
            "meta": {
                "overall_accuracy": overall_accuracy,
                "valid_predictions": summary.get("valid_predictions"),
                "last_updated": summary.get("last_updated"),
                "horizon": horizon
            }
        }
    except Exception as e:
        return {
            "trainer": "predictivelog",
            "adjustment": 1.0,
            "confidence": 0.2,
            "meta": {"reason": f"predictive_log_error:{e}", "horizon": horizon}
        }

def update_from_log(log_path: str = LOG_FILE_PATH, summary_path: str = SUMMARY_OUTPUT_PATH):
    """Load logs, summarize, and save summary."""
    try:
        logs = load_predictive_log(log_path)
    except FileNotFoundError:
        print(f"[trainer_16_predictivelog] Log file {log_path} not found, skipping summary update.")
        return

    summary = summarize_predictions(logs)
    save_summary(summary, summary_path)

if __name__ == "__main__":
    update_from_log()
