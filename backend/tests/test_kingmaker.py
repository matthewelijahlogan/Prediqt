from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from main import app
from kingmaker.model import predict
from trainers import trainer_1_yfinance as base
import pytest


@pytest.fixture(autouse=True)
def isolate_ledger(tmp_path, monkeypatch):
    monkeypatch.setenv("KINGMAKER_LEDGER_PATH", str(tmp_path / "forecasts.sqlite3"))


def history():
    rng = np.random.default_rng(37)
    return pd.DataFrame({"Close": 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, 300)))},
                        index=pd.date_range(end=pd.Timestamp.now(tz="UTC"), periods=300, freq="D"))


def test_long_horizons_purge_overlapping_labels():
    with patch.object(base, "fetch_market_data", return_value=history()):
        for horizon, gap in [("week", 5), ("month", 21)]:
            result = base.predict("AAPL", horizon)
            for fold in result["meta"]["validation_folds"]:
                assert fold["train_samples"] - 1 + gap < fold["validation_start"]
            assert np.isfinite(result["model_mse"])


def test_stale_history_cannot_qualify():
    frame = history()
    frame.attrs["provider"] = "yahoo_stale"
    with patch.object(base, "fetch_market_data", return_value=frame):
        result = predict("aapl", "day")
    assert result["ticker"] == "AAPL"
    assert result["signal"]["action"] == "HOLD"
    assert result["validation_confidence"] == 0
    assert not result["data_quality"]["usable"]


def test_api_serves_model_evidence_and_handles_invalid_symbols():
    with patch.object(base, "fetch_market_data", return_value=history()):
        response = TestClient(app).get("/predict/AAPL?horizon=week")
    assert response.status_code == 200
    assert response.json()["model"] == "kingmaker-v1"
    assert response.json()["evidence"]["validation_method"] == "purged_expanding_window"
    assert TestClient(app).get("/predict/bad!symbol").status_code == 422


def test_scan_preserves_successes_when_one_provider_fails():
    with patch("backend.routers.kingmaker.predict", side_effect=[
        {"ticker": "AAPL", "validation_confidence": 20,
         "signal": {"qualified": False, "expected_move_percent": 0.1}},
        RuntimeError("No history"),
    ]):
        response = TestClient(app).get("/api/kingmaker/scan?tickers=AAPL,INVALID")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert len(response.json()["errors"]) == 1


def test_unrealized_forecasts_are_not_scored_against_current_prices():
    import auto_trainer
    with patch.object(auto_trainer, "get_actual_price") as fetch, \
         patch.object(auto_trainer, "append_to_json_log") as log, \
         patch.object(auto_trainer, "update_from_log"), \
         patch.object(auto_trainer, "publish_summary_to_api"):
        auto_trainer.update_metrics_and_fusion([{"ticker": "AAPL", "result": {"predicted_next_close": 105}}])
    fetch.assert_not_called()
    assert log.call_args.args[1][0]["num_predictions"] == 0


def test_ledger_is_idempotent_and_waits_for_target_bar_to_close():
    from kingmaker.ledger import record, recent, settle
    result = {"ticker": "AAPL", "horizon": "day", "model": "test",
              "evidence": {"last_bar_at": "2025-01-06"},
              "generated_at": "2025-01-06T22:00:00+00:00", "predicted_next_close": 103}
    first = record(result)
    assert record(dict(result, predicted_next_close=999)) == first
    frame = pd.DataFrame({"Close": [100, 102, 104]},
                         index=pd.to_datetime(["2025-01-06", "2025-01-07", "2025-01-08"], utc=True))
    with patch("backend.market_data.get_history", return_value=(frame.iloc[:2], "test")):
        assert settle()["settled"] == 0
    with patch("backend.market_data.get_history", return_value=(frame, "test")):
        assert settle()["settled"] == 1
        assert settle()["settled"] == 0
    row = recent()[0]
    assert row["actual_close"] == 102
    assert row["payload"]["predicted_next_close"] == 103
