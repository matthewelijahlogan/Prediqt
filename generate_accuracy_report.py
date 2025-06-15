import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'predictive_logs', 'accuracy_log.json')
OUTPUT_JS = os.path.join(BASE_DIR, 'www', 'js', 'accuracy_report.js')

def generate_js():
    with open(LOG_FILE, 'r') as f:
        data = json.load(f)

    js_content = f"const accuracyData = {json.dumps(data, indent=2)};\n"
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f_js:
        f_js.write(js_content)
    print(f"accuracy_report.js generated at {OUTPUT_JS}")

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        print(f"Error: {LOG_FILE} not found.")
    else:
        generate_js()
