# file: fusion_fuser.py

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths to logs
LOG_DIR = os.path.join(BASE_DIR, "predictive_logs")
ORIGINAL_LOG_FILE = os.path.join(LOG_DIR, "predictions_log.json")
ORIGINAL_ACCURACY_FILE = os.path.join(LOG_DIR, "accuracy_log.json")
KINGMAKER_LOG_FILE = os.path.join(LOG_DIR, "predictions_log2.json")
KINGMAKER_ACCURACY_FILE = os.path.join(LOG_DIR, "accuracy_log2.json")

FUSED_ACCURACY_FILE = os.path.join(LOG_DIR, "fused_accuracy_log.json")

def load_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def fuse_accuracy_metrics(original_acc, kingmaker_acc):
    """
    Simple fusion logic: average the latest accuracy metrics.
    More complex weighting or ensemble fusion can replace this.
    """
    if not original_acc or not kingmaker_acc:
        return None

    latest_orig = original_acc[-1]
    latest_king = kingmaker_acc[-1]

    fused = {
        "timestamp": datetime.utcnow().isoformat(),
        "average_accuracy": None,
        "within_threshold_pct": None,
        "num_predictions": 0
    }

    # Average accuracies weighted by number of predictions
    total_preds = latest_orig.get("num_predictions", 0) + latest_king.get("num_predictions", 0)
    if total_preds == 0:
        return None

    avg_acc = 0
    within_thresh = 0
    if latest_orig.get("average_accuracy") is not None:
        avg_acc += latest_orig["average_accuracy"] * latest_orig.get("num_predictions", 0)
        within_thresh += latest_orig.get("within_threshold_pct", 0) * latest_orig.get("num_predictions", 0)
    if latest_king.get("average_accuracy") is not None:
        avg_acc += latest_king["average_accuracy"] * latest_king.get("num_predictions", 0)
        within_thresh += latest_king.get("within_threshold_pct", 0) * latest_king.get("num_predictions", 0)

    fused["average_accuracy"] = avg_acc / total_preds
    fused["within_threshold_pct"] = within_thresh / total_preds
    fused["num_predictions"] = total_preds

    return fused

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def main():
    original_acc = load_json(ORIGINAL_ACCURACY_FILE)
    kingmaker_acc = load_json(KINGMAKER_ACCURACY_FILE)

    fused_entry = fuse_accuracy_metrics(original_acc, kingmaker_acc)
    if fused_entry:
        fused_log = load_json(FUSED_ACCURACY_FILE)
        fused_log.append(fused_entry)
        save_json(FUSED_ACCURACY_FILE, fused_log)
        print(f"[fusion_fuser] Fused accuracy updated at {fused_entry['timestamp']}")
        print(f"[fusion_fuser] Average accuracy: {fused_entry['average_accuracy']:.4f}")
        print(f"[fusion_fuser] Within threshold %: {fused_entry['within_threshold_pct']:.4f}")
        print(f"[fusion_fuser] Total predictions: {fused_entry['num_predictions']}")
    else:
        print("[fusion_fuser] No data to fuse.")
        

if __name__ == "__main__":
    main()
