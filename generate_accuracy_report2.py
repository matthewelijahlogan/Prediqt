# generate_accuracy_report2.py

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'predictive_logs', 'accuracy_log2.json')
OUTPUT_JS = os.path.join(BASE_DIR, 'www', 'js', 'accuracy_data2.js')  

def generate_js():
    if not os.path.exists(LOG_FILE):
        print(f"❌ Log file not found at: {LOG_FILE}")
        return

    with open(LOG_FILE, 'r') as f:
        logs = json.load(f)

    if not logs:
        print("⚠️ No accuracy logs found.")
        return

    latest_log = logs[-1]
    total_predictions = len(logs)
    average_accuracy = sum(1 - (abs(e["predicted"] - e["actual"]) / e["actual"]) for e in logs if e["actual"]) / total_predictions

    js_object = {
        "last_updated": latest_log.get("timestamp", str(datetime.utcnow())),
        "total_predictions": total_predictions,
        "overall_accuracy": average_accuracy,
        "model_accuracies": {
            "average": average_accuracy
        }
    }

    js_content = f"const accuracyData2 = {json.dumps(js_object, indent=2)};\n" \
                 f"displayAccuracyReport2();\n"

    os.makedirs(os.path.dirname(OUTPUT_JS), exist_ok=True)
    with open(OUTPUT_JS, 'w', encoding='utf-8') as out:
        out.write(js_content)

    print(f"✅ JS file generated at: {OUTPUT_JS}")

if __name__ == "__main__":
    generate_js()
