import numpy as np
import json
import os

# Default weights fallback
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
    "volatility": 0.05
}

def load_weights_from_summary(path="predictive_summary.json"):
    """
    Loads model accuracies from a JSON summary file and converts
    them into normalized weights for fusion.
    Falls back to DEFAULT_WEIGHTS if file is missing or malformed.
    """
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
        
        # Ensure all expected keys are present, fallback to 0 if missing
        for key in DEFAULT_WEIGHTS.keys():
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
    weights=None  # Allow external weights to be passed
):
    if weights is None:
        weights = load_weights_from_summary()  # Load from summary by default
    
    def extract_value(name, result):
        if not result:
            return None
        if name == "base":
            return result.get("predicted_next_close")
        elif name == "sentiment":
            return 1 + (result.get("sentiment_score", 0) * 0.05)
        elif name in ["pelosi", "weather", "earnings", "social", "sector", 
                      "insider", "technical", "etf_sector", "volume", 
                      "patterns", "volatility"]:
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

    base_price = None
    if base and "predicted_next_close" in base:
        base_price = base["predicted_next_close"]
    else:
        print("[fusion_model] Warning: base model missing predicted_next_close, defaulting to 100")
        base_price = 100  # or any sensible default

    weighted_values = []
    total_weight = 0
    used_models = []

    for model_name, res in inputs.items():
        val = extract_value(model_name, res)
        if val is not None:
            if model_name == "base":
                weighted_values.append(val * weights.get(model_name, 0))
            else:
                weighted_values.append(base_price * val * weights.get(model_name, 0))
            total_weight += weights.get(model_name, 0)
            used_models.append(model_name)

    if total_weight == 0:
        print("[fusion_model] Warning: no valid model predictions found, returning base_price")
        return {
            "predicted_next_close": base_price,
            "used_models": used_models,
            "model_mse": base.get("model_mse") if base else None
        }

    fused_prediction = sum(weighted_values) / total_weight

    direction_votes = 0
    for model_name, res in inputs.items():
        val = extract_value(model_name, res)
        if model_name != "base" and val is not None and base_price is not None:
            predicted_price = base_price * val
            if predicted_price > base_price:
                direction_votes += 1
            elif predicted_price < base_price:
                direction_votes -= 1

    if abs(direction_votes) >= 4:
        fused_prediction *= 1.01 if direction_votes > 0 else 0.99

    if base and "recent_prices" in base:
        recent_prices = base["recent_prices"]
        if len(recent_prices) >= 10:
            volatility = np.std(recent_prices[-10:])
            volatility_adjustment = 1 / (1 + volatility / base_price)
            fused_prediction *= volatility_adjustment

    return {
        "predicted_next_close": round(fused_prediction, 2),
        "used_models": used_models,
        "model_mse": base.get("model_mse") if base else None,
        "weights_used": weights
    }
