# file: app.py

from flask import Flask, send_from_directory
from generate_accuracy_report import generate_js
import os

app = Flask(__name__, static_folder="www")

@app.route("/")
def serve_index():
    generate_js()
    return send_from_directory("www", "accuracy_report.html")

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory("www/js", filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
