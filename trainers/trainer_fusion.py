import numpy as np
import json
import os

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
    "volatility": 0.03
}

HORIZON_SCALING = {
    "hour": 0.75,
    "day": 1.0,
    "week": 1.05,
    "month": 1.1
}

MAX_SHORT_TERM_MOVE = 0.03  # 3% cap for hour-based predictions

def load_weights_from_summary(path="predictive_summary.json"):
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


def predict(
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
    weights=None,
    horizon="day"  # NEW: optional prediction horizon input
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
        "volatility": volatility
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

    # Voting system adjustment (kept for directional consensus)
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
