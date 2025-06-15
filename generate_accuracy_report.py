import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'predictive_logs', 'accuracy_log.json')
OUTPUT_JS = os.path.join(BASE_DIR, 'www', 'js', 'accuracy_report.js')

def generate_js():
    with open(LOG_FILE, 'r') as f:
        logs = json.load(f)

    if not logs:
        print("No logs found.")
        return

    latest_log = logs[-1]  # most recent accuracy entry
    total_predictions = sum(entry["num_predictions"] for entry in logs)
    weighted_accuracy = sum(entry["average_accuracy"] * entry["num_predictions"] for entry in logs) / total_predictions

    result = {
        "last_updated": latest_log["timestamp"],
        "total_predictions": total_predictions,
        "overall_accuracy": weighted_accuracy,
        "model_accuracies": {
            "average": latest_log["average_accuracy"]
        }
    }

    js_content = f"const accuracyData = {json.dumps(result, indent=2)};\n" \
                 f"displayAccuracyReport();\n"

    with open(OUTPUT_JS, 'w', encoding='utf-8') as f_js:
        f_js.write(js_content)

    print(f"✅ accuracy_report.js generated at {OUTPUT_JS}")

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        print(f"❌ Error: {LOG_FILE} not found.")
    else:
        generate_js()
