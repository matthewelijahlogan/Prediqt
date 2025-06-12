import numpy as np

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
    volatility=None
):
    weights = {
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
                weighted_values.append(val * weights[model_name])
            else:
                weighted_values.append(base_price * val * weights[model_name])
            total_weight += weights[model_name]
            used_models.append(model_name)

    if total_weight == 0:
        print("[fusion_model] Warning: no valid model predictions found, returning base_price")
        return {
            "predicted_next_close": base_price,
            "used_models": used_models,
            "model_mse": base.get("model_mse") if base else None
        }

    # Calculate weighted average prediction first
    fused_prediction = sum(weighted_values) / total_weight

    # Count how many models predict up or down relative to base_price
    direction_votes = 0
    for model_name, res in inputs.items():
        val = extract_value(model_name, res)
        if model_name != "base" and val is not None and base_price is not None:
            predicted_price = base_price * val
            if predicted_price > base_price:
                direction_votes += 1
            elif predicted_price < base_price:
                direction_votes -= 1

    # Boost if strong agreement (4+ models agree on direction)
    if abs(direction_votes) >= 4:
        fused_prediction *= 1.01 if direction_votes > 0 else 0.99

    # Volatility adjustment based on last 10 prices if available
    if base and "recent_prices" in base:
        recent_prices = base["recent_prices"]
        if len(recent_prices) >= 10:
            volatility = np.std(recent_prices[-10:])
            volatility_adjustment = 1 / (1 + volatility / base_price)
            fused_prediction *= volatility_adjustment

    return {
        "predicted_next_close": round(fused_prediction, 2),
        "used_models": used_models,
        "model_mse": base.get("model_mse") if base else None
    }
