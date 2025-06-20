import numpy as np
import json
import os
import pandas as pd
import joblib

# --- Constants & defaults ---

DEFAULT_WEIGHTS = {
    "base": 0.4,
    "sentiment": 0.1,
    "pelosi": 0.1,
    "weather": 0.05,
    "earnings": 0.1,
    "social": 0.05,
    "sector": 0.05,
    "insider": 0.075,
    "options": 0.075,
    "technical": 0.05,
    "etf_sector": 0.05,
    "volume": 0.05,
    "patterns": 0.05,
    "volatility": 0.03,
    "macro": 0.07,          # Added macro
    "predictivelog": 0.05,  # Added predictivelog
    "news": 0.05            # Added news
}

HORIZON_SCALING = {
    "hour": 0.75,
    "day": 1.0,
    "week": 1.05,
    "month": 1.1
}

MAX_SHORT_TERM_MOVE = 0.03  # 3% cap for hour-based predictions

WEIGHTS_SUMMARY_PATH = "predictive_summary.json"
META_MODEL_PATH = "meta_model.pkl"


# --- Load heuristic weights from accuracy summary ---

def load_weights_from_summary(path=WEIGHTS_SUMMARY_PATH):
    if not os.path.exists(path):
        print(f"[fusion_model] Weights summary file '{path}' not found. Using default weights.")
        return DEFAULT_WEIGHTS

    try:
        with open(path, "r") as f:
            summary = json.load(f)
        model_accuracies = summary.get("model_accuracies", {})
        if not model_accuracies:
            print("[fusion_model] No model_accuracies found in summary. Using default weights.")
            return DEFAULT_WEIGHTS

        total = sum(model_accuracies.values())
        if total == 0:
            print("[fusion_model] Sum of model accuracies is zero. Using default weights.")
            return DEFAULT_WEIGHTS

        weights = {k: v / total for k, v in model_accuracies.items()}
        for key in DEFAULT_WEIGHTS:
            weights.setdefault(key, 0)

        print(f"[fusion_model] Loaded dynamic weights: {weights}")
        return weights

    except Exception as e:
        print(f"[fusion_model] Error loading weights from summary: {e}. Using default weights.")
        return DEFAULT_WEIGHTS


# --- Extract features from trainer results for meta-model ---

def extract_features_from_trainer_results(trainer_results):
    features = {}
    models = list(DEFAULT_WEIGHTS.keys())

    for model in models:
        sub = trainer_results.get(model, {})
        prefix = f"{model}_"

        if isinstance(sub, dict):
            if "adjustment" in sub:
                features[prefix + "adjustment"] = float(sub["adjustment"])
            if "options_signal_strength" in sub:
                features[prefix + "signal_strength"] = float(sub["options_signal_strength"])
            if "options_prediction_confidence" in sub:
                features[prefix + "prediction_confidence"] = float(sub["options_prediction_confidence"])
            if "sentiment_score" in sub:
                features[prefix + "sentiment_score"] = float(sub["sentiment_score"])
            if "pattern_score" in sub:
                features[prefix + "pattern_score"] = float(sub["pattern_score"])
            if "rsi_score" in sub:
                features[prefix + "rsi_score"] = float(sub["rsi_score"])
            if "macd_score" in sub:
                features[prefix + "macd_score"] = float(sub["macd_score"])
            if "bollinger_score" in sub:
                features[prefix + "bollinger_score"] = float(sub["bollinger_score"])
            if "total_score" in sub:
                features[prefix + "total_score"] = float(sub["total_score"])
            if "prediction" in sub:
                # For macro, predictivelog, news etc. use generic 'prediction' field
                features[prefix + "prediction"] = float(sub["prediction"])
        else:
            if model == "base" and "predicted_next_close" in trainer_results:
                features[prefix + "predicted_next_close"] = float(trainer_results["predicted_next_close"])

    # Fill missing keys with zeros for consistent feature vector
    for model in models:
        prefix = f"{model}_"
        expected_keys = [
            "adjustment", "signal_strength", "prediction_confidence", "sentiment_score",
            "pattern_score", "rsi_score", "macd_score", "bollinger_score", "total_score",
            "predicted_next_close", "prediction"
        ]
        for key in expected_keys:
            features.setdefault(prefix + key, 0.0)

    return features


# --- Load meta-model ---

def load_meta_model():
    if not os.path.exists(META_MODEL_PATH):
        print(f"[fusion_model] Meta-model not found at {META_MODEL_PATH}. Please train it first.")
        return None
    return joblib.load(META_MODEL_PATH)


# --- Heuristic fusion prediction ---

def heuristic_predict(
    base=None,
    sentiment=None,
    pelosi=None,
    weather=None,
    earnings=None,
    social=None,
    sector=None,
    insider=None,
    options=None,
    technical=None,
    etf_sector=None,
    volume=None,
    patterns=None,
    volatility=None,
    macro=None,           # Added macro param
    predictivelog=None,   # Added predictivelog param
    news=None,            # Added news param
    weights=None,
    horizon="day"
):
    if weights is None:
        weights = load_weights_from_summary()

    def extract_value(name, result):
        if not result:
            return None
        if name == "base":
            return result.get("predicted_next_close")
        elif name == "sentiment":
            return 1 + (result.get("sentiment_score", 0) * 0.05)
        elif name in [
            "pelosi", "weather", "earnings", "social", "sector",
            "insider", "technical", "etf_sector", "volume",
            "patterns", "volatility"
        ]:
            return result.get("adjustment")
        elif name == "options":
            strength = result.get("options_signal_strength", 1)
            confidence = result.get("options_prediction_confidence", 1)
            return 1 + (strength * 0.05 * confidence)
        elif name in ["macro", "predictivelog", "news"]:
            return result.get("prediction")  # assuming macro, predictivelog, news use 'prediction' key
        return None

    inputs = {
        "base": base,
        "sentiment": sentiment,
        "pelosi": pelosi,
        "weather": weather,
        "earnings": earnings,
        "social": social,
        "sector": sector,
        "insider": insider,
        "options": options,
        "technical": technical,
        "etf_sector": etf_sector,
        "volume": volume,
        "patterns": patterns,
        "volatility": volatility,
        "macro": macro,               # added
        "predictivelog": predictivelog, # added
        "news": news                  # added
    }

    base_price = base.get("predicted_next_close") if base and "predicted_next_close" in base else 100
    if base_price == 100:
        print("[fusion_model] Warning: base price not found. Using default 100.")

    weighted_values = []
    total_weight = 0
    used_models = []

    for model_name, res in inputs.items():
        val = extract_value(model_name, res)
        if val is not None:
            w = weights.get(model_name, 0)
            if model_name == "base":
                weighted_values.append(val * w)
            else:
                weighted_values.append(base_price * val * w)
            total_weight += w
            used_models.append(model_name)

    if total_weight == 0:
        print("[fusion_model] Warning: no valid model predictions found, returning base_price")
        return {
            "predicted_next_close": base_price,
            "used_models": used_models,
            "model_mse": base.get("model_mse") if base else None
        }

    fused_prediction = sum(weighted_values) / total_weight

    # Voting system adjustment (directional consensus)
    direction_votes = 0
    for model_name, res in inputs.items():
        val = extract_value(model_name, res)
        if model_name != "base" and val is not None:
            predicted_price = base_price * val
            if predicted_price > base_price:
                direction_votes += 1
            elif predicted_price < base_price:
                direction_votes -= 1

    if abs(direction_votes) >= 4:
        fused_prediction *= 1.01 if direction_votes > 0 else 0.99

    # Volatility smoothing using past prices
    if base and "recent_prices" in base:
        recent_prices = base["recent_prices"]
        if len(recent_prices) >= 10:
            volatility = np.std(recent_prices[-10:])
            volatility_adjustment = 1 / (1 + volatility / base_price)
            fused_prediction *= volatility_adjustment

    # Apply horizon scaling
    fused_prediction *= HORIZON_SCALING.get(horizon, 1.0)

    # Clamp short-term overreactions
    if horizon == "hour":
        delta = fused_prediction / base_price - 1
        if abs(delta) > MAX_SHORT_TERM_MOVE:
            print(f"[fusion_model] Clamping short-term prediction from {round(delta * 100, 2)}% to ±{MAX_SHORT_TERM_MOVE*100}%")
            fused_prediction = base_price * (1 + np.clip(delta, -MAX_SHORT_TERM_MOVE, MAX_SHORT_TERM_MOVE))

    return {
        "predicted_next_close": round(fused_prediction, 2),
        "used_models": used_models,
        "model_mse": base.get("model_mse") if base else None,
        "weights_used": weights
    }


# --- Meta-model fusion prediction ---

def meta_model_predict(trainer_results):
    model = load_meta_model()
    if model is None:
        print("[fusion_model] Meta-model not available, falling back to heuristic fusion.")
        return heuristic_predict(**trainer_results)

    features = extract_features_from_trainer_results(trainer_results)
    X = pd.DataFrame([features])
    prediction = model.predict(X)[0]
    print(f"[fusion_model] Meta-model prediction: {prediction}")

    return {"predicted_next_close": round(prediction, 2)}


# --- Public predict interface ---

def predict(trainer_results, mode="heuristic", **kwargs):
    """
    Predict using fusion.

    :param trainer_results: dict with keys for each trainer result dict (e.g. base=..., sentiment=..., etc)
    :param mode: 'heuristic' or 'meta_model'
    :param kwargs: passed to heuristic_predict for extra params like horizon
    """
    if mode == "meta_model":
        return meta_model_predict(trainer_results)
    else:
        # Expect kwargs like horizon, weights
        return heuristic_predict(**trainer_results, **kwargs)


# --- CLI test ---

if __name__ == "__main__":
    # Dummy example data for manual testing
    dummy_base = {"predicted_next_close": 100}
    dummy_sentiment = {"sentiment_score": 0.2}
    dummy_pelosi = {"adjustment": 1.01}
    dummy_weather = {"adjustment": 1.0}
    dummy_earnings = {"adjustment": 0.98}
    dummy_social = {"adjustment": 1.03}
    dummy_sector = {"adjustment": 1.02}
    dummy_insider = {"adjustment": 1.0}
    dummy_options = {"options_signal_strength": 1, "options_prediction_confidence": 0.9}
    dummy_technical = {"adjustment": 1.01}
    dummy_etf_sector = {"adjustment": 1.0}
    dummy_volume = {"adjustment": 0.99}
    dummy_patterns = {"adjustment": 1.0}
    dummy_volatility = {"adjustment": 1.0}
    dummy_macro = {"prediction": 0.02}
    dummy_predictivelog = {"prediction": 0.01}
    dummy_news = {"prediction": 0.015}

    results = {
        "base": dummy_base,
        "sentiment": dummy_sentiment,
        "pelosi": dummy_pelosi,
        "weather": dummy_weather,
        "earnings": dummy_earnings,
        "social": dummy_social,
        "sector": dummy_sector,
        "insider": dummy_insider,
        "options": dummy_options,
        "technical": dummy_technical,
        "etf_sector": dummy_etf_sector,
        "volume": dummy_volume,
        "patterns": dummy_patterns,
        "volatility": dummy_volatility,
        "macro": dummy_macro,
        "predictivelog": dummy_predictivelog,
        "news": dummy_news
    }

    print("Heuristic fusion prediction:")
    print(predict(results, mode="heuristic", horizon="day"))

    print("Meta-model fusion prediction:")
    print(predict(results, mode="meta_model"))
