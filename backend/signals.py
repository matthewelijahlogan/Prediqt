import math
from typing import Any


MOVE_THRESHOLDS = {
    "hour": 0.01,
    "day": 0.02,
    "week": 0.04,
    "month": 0.075,
}
MINIMUM_CONFIDENCE = 55.0


def classify_signal(
    current_price: float | None,
    predicted_price: float | None,
    model_mse: float | None,
    horizon: str,
) -> dict[str, Any]:
    """Turn a prospective price forecast into a transparent action signal."""
    threshold = MOVE_THRESHOLDS.get(horizon, MOVE_THRESHOLDS["day"])
    if current_price is None or predicted_price is None or current_price <= 0:
        return {
            "action": "HOLD",
            "expected_move_percent": None,
            "confidence": 0.0,
            "threshold_percent": round(threshold * 100, 2),
            "qualified": False,
            "rationale": "HOLD: current and predicted prices are required.",
        }

    expected_move = (predicted_price - current_price) / current_price
    if model_mse is None or model_mse < 0:
        confidence = 0.0
    else:
        normalized_rmse = math.sqrt(model_mse) / current_price
        confidence = max(0.0, min(100.0, 100 / (1 + normalized_rmse * 10)))

    evidence_passes = confidence >= MINIMUM_CONFIDENCE
    if evidence_passes and expected_move >= threshold:
        action = "BUY"
    elif evidence_passes and expected_move <= -threshold:
        action = "SELL"
    else:
        action = "HOLD"

    move_text = f"{expected_move * 100:+.2f}%"
    if not evidence_passes:
        rationale = (
            f"HOLD: forecast confidence {confidence:.1f}% is below the "
            f"{MINIMUM_CONFIDENCE:.0f}% evidence gate."
        )
    elif action == "HOLD":
        rationale = (
            f"HOLD: expected move {move_text} does not clear the "
            f"+/-{threshold * 100:.2f}% {horizon} threshold."
        )
    else:
        rationale = (
            f"{action}: expected move {move_text} clears the "
            f"{threshold * 100:.2f}% {horizon} threshold at "
            f"{confidence:.1f}% confidence."
        )

    return {
        "action": action,
        "expected_move_percent": round(expected_move * 100, 2),
        "confidence": round(confidence, 1),
        "threshold_percent": round(threshold * 100, 2),
        "qualified": action != "HOLD",
        "rationale": rationale,
    }
