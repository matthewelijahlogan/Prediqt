import json
import os

import joblib
import numpy as np
import pandas as pd

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
    "macro": 0.07,
    "predictivelog": 0.05,
    "news": 0.05,
}

# Supplemental trainers are heuristic signals, not independently validated
# price models. Keep their impact subordinate to the time-series base model.
AUXILIARY_RELIABILITY = 0.25

MAX_SHORT_TERM_MOVE = 0.03
MAX_MOVE_BY_HORIZON = {
    "hour": 0.03,
    "day": 0.08,
    "week": 0.18,
    "month": 0.30,
}

WEIGHTS_SUMMARY_PATH = "predictive_summary.json"
META_MODEL_PATH = "meta_model.pkl"


# --- Load heuristic weights from accuracy summary ---

def load_weights_from_summary(path=WEIGHTS_SUMMARY_PATH):
    if not os.path.exists(path):
        print(f"[fusion_model] Weights summary file '{path}' not found. Using default weights.")
        return DEFAULT_WEIGHTS

    try:
        with open(path, "r", encoding="utf-8") as f:
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
                features[prefix + "prediction"] = float(sub["prediction"])
        else:
            if model == "base" and "predicted_next_close" in trainer_results:
                features[prefix + "predicted_next_close"] = float(trainer_results["predicted_next_close"])

    for model in models:
        prefix = f"{model}_"
        expected_keys = [
            "adjustment",
            "signal_strength",
            "prediction_confidence",
            "sentiment_score",
            "pattern_score",
            "rsi_score",
            "macd_score",
            "bollinger_score",
            "total_score",
            "predicted_next_close",
            "prediction",
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
    macro=None,
    predictivelog=None,
    news=None,
    weights=None,
    horizon="day",
):
    if weights is None:
        weights = load_weights_from_summary()

    def extract_value(name, result):
        if not result:
            return None
        if name == "base":
            return result.get("predicted_next_close")

        adjustment = result.get("adjustment")
        if isinstance(adjustment, (int, float)):
            return float(adjustment)

        prediction = result.get("prediction")
        if isinstance(prediction, (int, float)):
            prediction = float(prediction)
            if -1.0 <= prediction <= 1.0:
                return 1.0 + prediction
            if 0.5 <= prediction <= 1.5:
                return prediction

        if name == "sentiment":
            sentiment_score = result.get("sentiment_score")
            if isinstance(sentiment_score, (int, float)):
                return 1 + (float(sentiment_score) * 0.05)

        if name == "options":
            strength = result.get("options_signal_strength")
            confidence = result.get("options_prediction_confidence")
            if isinstance(strength, (int, float)) and isinstance(confidence, (int, float)):
                return 1 + (float(strength) * 0.05 * float(confidence))

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
        "macro": macro,
        "predictivelog": predictivelog,
        "news": news,
    }

    base_price = base.get("predicted_next_close") if base and "predicted_next_close" in base else None
    current_price = base.get("meta", {}).get("current_price") if base else None
    if not isinstance(current_price, (int, float)) or current_price <= 0:
        current_price = base_price
    if not isinstance(current_price, (int, float)) or current_price <= 0:
        current_price = 100.0
        print("[fusion_model] Warning: current price not found. Using default 100.")
    if not isinstance(base_price, (int, float)) or base_price <= 0:
        base_price = current_price

    weighted_returns = []
    total_weight = 0
    used_models = []

    for model_name, res in inputs.items():
        val = extract_value(model_name, res)
        if val is not None:
            w = weights.get(model_name, 0)
            if model_name == "base":
                model_return = float(val) / current_price - 1
                # The base return has already been shrunk by out-of-sample skill.
                raw_confidence = 1.0
            else:
                model_return = float(val) - 1
                raw_confidence = res.get("confidence", 0.0)
                w *= AUXILIARY_RELIABILITY
            confidence = float(raw_confidence) if isinstance(raw_confidence, (int, float)) else 0.0
            confidence = float(np.clip(confidence, 0.0, 1.0))
            effective_weight = w * confidence
            if effective_weight <= 0:
                continue
            weighted_returns.append(model_return * effective_weight)
            total_weight += effective_weight
            used_models.append(model_name)

    if total_weight == 0:
        print("[fusion_model] Warning: no confidence-weighted predictions, returning current price")
        return {
            "predicted_next_close": current_price,
            "used_models": used_models,
            "model_mse": base.get("model_mse") if base else None,
            "validation_confidence": base.get("validation_confidence") if base else None,
        }

    fused_return = sum(weighted_returns) / total_weight

    direction_votes = 0
    for model_name, res in inputs.items():
        val = extract_value(model_name, res)
        if model_name != "base" and val is not None:
            predicted_price = current_price * val
            if predicted_price > current_price:
                direction_votes += 1
            elif predicted_price < current_price:
                direction_votes -= 1

    if abs(direction_votes) >= 4:
        fused_return += 0.0025 if direction_votes > 0 else -0.0025

    if base and "recent_prices" in base:
        recent_prices = base["recent_prices"]
        if len(recent_prices) >= 10:
            recent_volatility = np.std(recent_prices[-10:])
            volatility_adjustment = 1 / (1 + recent_volatility / current_price)
            fused_return *= volatility_adjustment

    max_move = MAX_MOVE_BY_HORIZON.get(horizon, MAX_SHORT_TERM_MOVE)
    if abs(fused_return) > max_move:
        print(
            f"[fusion_model] Clamping {horizon} prediction from {round(fused_return * 100, 2)}% "
            f"to +/-{max_move * 100}%"
        )
        fused_return = float(np.clip(fused_return, -max_move, max_move))
    fused_prediction = current_price * (1 + fused_return)

    return {
        "predicted_next_close": round(float(fused_prediction), 2),
        "used_models": used_models,
        "model_mse": base.get("model_mse") if base else None,
        "validation_confidence": base.get("validation_confidence") if base else None,
        "weights_used": weights,
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
    if mode == "meta_model":
        return meta_model_predict(trainer_results)
    return heuristic_predict(**trainer_results, **kwargs)


if __name__ == "__main__":
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
        "news": dummy_news,
    }

    print("Heuristic fusion prediction:")
    print(predict(results, mode="heuristic", horizon="day"))

    print("Meta-model fusion prediction:")
    print(predict(results, mode="meta_model"))
