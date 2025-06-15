import json
import os
from typing import List, Dict
from datetime import datetime

LOG_FILE_PATH = "predictive_logs/predictions_log.json"  # Match path used in auto_trainer.py
SUMMARY_OUTPUT_PATH = "predictive_summary.json"

def load_predictive_log(path: str) -> List[Dict]:
    """Load the prediction log JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Log file not found at {path}")
    with open(path, "r") as f:
        data = json.load(f)
    return data

def calculate_error(predicted: float, actual: float) -> float:
    """Calculate relative error or absolute error as needed."""
    if actual == 0:
        return float("inf")
    return abs(predicted - actual) / actual

def summarize_predictions(logs: List[Dict]) -> Dict:
    """Summarize prediction logs to evaluate accuracy and stats."""
    total_predictions = 0
    total_error = 0.0
    
    # Keep track of errors per model
    model_error_sums = {}
    model_counts = {}

    for entry in logs:
        total_predictions += 1
        result = entry.get("result", {})
        actual = get_actual_close_from_entry(entry)
        
        if actual is None:
            continue

        # Calculate overall error from base prediction
        predicted = result.get("predicted_next_close")
        if predicted is None:
            continue

        error = calculate_error(predicted, actual)
        total_error += error

        # For model accuracies, gather each sub-model prediction if present
        for model_key in [
            "base", "sentiment", "pelosi", "weather", "earnings",
            "social", "sector", "insider", "options", "technical",
            "etf_sector", "volume", "patterns", "volatility"
        ]:
            submodel_data = result.get(model_key)
            if not submodel_data:
                # Some models might not be present in every result
                continue
            
            # Extract predicted value for sub-model
            pred_val = extract_predicted_value(model_key, submodel_data, result)
            if pred_val is None:
                continue

            model_error_sums.setdefault(model_key, 0)
            model_counts.setdefault(model_key, 0)
            
            sub_err = calculate_error(pred_val, actual)
            model_error_sums[model_key] += sub_err
            model_counts[model_key] += 1

    overall_accuracy = 1 - (total_error / total_predictions) if total_predictions > 0 else None

    # Calculate per-model accuracies
    model_accuracies = {}
    for model_key, err_sum in model_error_sums.items():
        count = model_counts.get(model_key, 1)
        model_accuracies[model_key] = 1 - (err_sum / count) if count > 0 else 0.0

    summary = {
        "total_predictions": total_predictions,
        "overall_accuracy": overall_accuracy,
        "model_accuracies": model_accuracies,
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }
    return summary

def extract_predicted_value(model_name: str, submodel_data: dict, full_result: dict):
    """
    Extracts a predicted value from a submodel result for error calculation.
    This logic depends on your prediction structure — adapt if needed.
    """
    if model_name == "base":
        return submodel_data.get("predicted_next_close")
    elif model_name == "sentiment":
        return full_result.get("predicted_next_close") * (1 + (submodel_data.get("sentiment_score", 0) * 0.05))
    elif model_name in ["pelosi", "weather", "earnings", "social", "sector", 
                        "insider", "technical", "etf_sector", "volume", "patterns", "volatility"]:
        adjustment = submodel_data.get("adjustment")
        if adjustment is None:
            return None
        base_price = full_result.get("predicted_next_close")
        if base_price is None:
            return None
        return base_price * adjustment
    elif model_name == "options":
        strength = submodel_data.get("options_signal_strength", 1)
        confidence = submodel_data.get("options_prediction_confidence", 1)
        base_price = full_result.get("predicted_next_close")
        if base_price is None:
            return None
        return base_price * (1 + (strength * 0.05 * confidence))
    return None

def get_actual_close_from_entry(entry: Dict):
    """
    This assumes your log entries include actual close prices,
    or you can fetch them here if not included.
    """
    # Try to get actual_close from the entry itself
    actual = entry.get("actual_close")
    if actual is not None:
        return actual

    # If not in entry, try inside result if you store it there
    result = entry.get("result", {})
    return result.get("actual_close")

def save_summary(summary: Dict, path: str):
    """Save the summary dict to a JSON file."""
    with open(path, "w") as f:
        json.dump(summary, f, indent=4)
    print(f"[trainer_16_predictivelog] Summary saved to {path}")

def update_from_log(log_path: str = LOG_FILE_PATH, summary_path: str = SUMMARY_OUTPUT_PATH):
    """Main function to load logs, summarize and save summary."""
    try:
        logs = load_predictive_log(log_path)
    except FileNotFoundError:
        print(f"[trainer_16_predictivelog] Log file {log_path} not found, skipping summary update.")
        return
    
    summary = summarize_predictions(logs)
    save_summary(summary, summary_path)

if __name__ == "__main__":
    update_from_log()
