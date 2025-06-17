import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_1 = os.path.join(BASE_DIR, 'predictive_logs', 'accuracy_log.json')
LOG_2 = os.path.join(BASE_DIR, 'predictive_logs', 'accuracy_log2.json')
OUTPUT_JS = os.path.join(BASE_DIR, 'www', 'js', 'accuracy_merged.js')

def load_logs(log_file):
    if not os.path.exists(log_file):
        return []
    with open(log_file, 'r') as f:
        return json.load(f)
    
def average_accuracy(logs):
    valid_entries = [
        e for e in logs 
        if isinstance(e.get("actual"), (int, float)) and isinstance(e.get("predicted"), (int, float))
    ]
    if not valid_entries:
        return 0
    return sum(1 - (abs(e["predicted"] - e["actual"]) / e["actual"]) for e in valid_entries) / len(valid_entries)

def generate_merged():
    logs1 = load_logs(LOG_1)
    logs2 = load_logs(LOG_2)

    avg1 = average_accuracy(logs1)
    avg2 = average_accuracy(logs2)

    total_predictions = len(logs1) + len(logs2)
    overall_accuracy = (avg1 * len(logs1) + avg2 * len(logs2)) / total_predictions if total_predictions > 0 else 0

    js_object = {
        "last_updated": str(datetime.utcnow()),
        "total_predictions": total_predictions,
        "overall_accuracy": overall_accuracy,
        "model_accuracies": {
            "model_1": avg1,
            "model_2": avg2
        }
    }

    js_content = f"const mergedAccuracyData = {json.dumps(js_object, indent=2)};\n" \
                 f"displayMergedReport();\n"

    os.makedirs(os.path.dirname(OUTPUT_JS), exist_ok=True)
    with open(OUTPUT_JS, 'w') as f:
        f.write(js_content)

    print(f"✅ Merged JS written to {OUTPUT_JS}")

if __name__ == "__main__":
    generate_merged()
