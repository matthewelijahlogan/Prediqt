from unittest.mock import patch, MagicMock
import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app
from kingmaker import opportunities as desk
from backend import webull_data


def test_rankings_have_correct_limits_and_do_not_promote_speculation():
    def fake(symbol, *_args):
        rank = int(symbol[1:])
        return {"ticker": symbol, "movement_score": rank, "qualified_driver": rank == 1,
                "estimated_net_move_percent": rank / 10, "forecast_move_percent": rank / 10,
                "forecast": {"validation_confidence": rank}}
    with patch.object(desk, "candidate", side_effect=fake):
        result = desk.build_board([f"S{i}" for i in range(15)])
    assert len(result["big_movers"]) == 5
    assert result["big_movers"][0]["ticker"] == "S14"
    assert len(result["daily_drivers"]) == 10
    assert result["daily_drivers"][0]["ticker"] == "S1"
    assert not result["big_movers"][0]["qualified_driver"]


def test_candidate_graph_and_costs_use_real_aligned_evidence():
    frame = pd.DataFrame({"Close": np.linspace(90, 100, 40), "Volume": [100]*39 + [200]},
                         index=pd.date_range(end=pd.Timestamp.now(tz="UTC"), periods=40, freq="D"))
    forecast = {"data_quality": {"usable": True}, "evidence": {"last_bar_at": frame.index[-1].isoformat()},
                "current_price": 100, "predicted_next_close": 103, "model_mse": 4,
                "signal": {"expected_move_percent": 3, "action": "BUY", "qualified": True}}
    with patch.object(desk, "predict", return_value=forecast), patch.object(desk, "get_history", return_value=(frame, "test")):
        item = desk.candidate("AAPL", "day", 40)
        assert item["relative_volume"] == 2
        assert item["estimated_net_move_percent"] == 2.6
        assert item["error_band"]["low"] == 101
        assert item["error_band"]["high"] == 105
        assert len(item["history"]) == 30
        assert item["history"][-1]["close"] == 100
        assert not desk.candidate("AAPL", "day", 400)["qualified_driver"]


def test_failed_candidates_are_not_padded_and_errors_do_not_leak_secrets():
    with patch.object(desk, "candidate", side_effect=RuntimeError("secret=do-not-expose")):
        result = desk.build_board(["AAPL"])
    assert result["big_movers"] == result["daily_drivers"] == []
    assert "do-not-expose" not in str(result)


def test_nonfinite_price_or_changed_origin_is_rejected():
    for value in [float("nan"), float("inf")]:
        with pytest.raises(ValueError):
            desk.finite(value)


def test_background_api_validates_and_returns_progress(monkeypatch):
    from backend.routers import opportunities as routes
    with routes._lock:
        routes._jobs.clear()
    client = TestClient(app)
    assert client.post("/api/kingmaker/opportunities", json={"tickers": "BAD!"}).status_code == 422
    assert client.post("/api/kingmaker/opportunities", json={"cost_bps": -1}).status_code == 422
    def fake(symbols, horizon, costs, progress):
        progress(len(symbols), len(symbols))
        return {"universe": symbols, "big_movers": [], "daily_drivers": []}
    monkeypatch.setattr(routes, "build_board", fake)
    started = client.post("/api/kingmaker/opportunities", json={"tickers": "aapl,AAPL,MSFT"}).json()
    for _ in range(100):
        job = client.get(f"/api/kingmaker/opportunities/{started['job_id']}").json()
        if job["status"] == "complete":
            break
        time.sleep(0.01)
    assert job["completed"] == job["total"] == 2
    assert job["result"]["universe"] == ["AAPL", "MSFT"]
    assert client.get("/api/kingmaker/opportunities/missing").status_code == 404


def webull_payload():
    return {"result": [{"symbol": "AAPL", "instrument_id": "123", "result": [
        {"time": at.isoformat(), "open": "100", "close": "101", "high": "102", "low": "99", "volume": "200"}
        for at in pd.date_range("2026-01-01", periods=40, tz="UTC")]}]}


def test_webull_documented_schema_and_invalid_data():
    frame = webull_data.normalize_bars(webull_payload(), "AAPL")
    assert len(frame) == 40 and frame["Close"].iloc[-1] == 101
    payload = webull_payload(); payload["result"][0]["result"][0]["close"] = "nan"
    with pytest.raises(ValueError):
        webull_data.normalize_bars(payload, "AAPL")


def test_official_webull_sdk_is_read_only_and_redacts_errors(monkeypatch):
    monkeypatch.setenv("WEBULL_APP_KEY", "test-key")
    monkeypatch.setenv("WEBULL_APP_SECRET", "private-test-secret")
    response = MagicMock(status_code=200)
    response.json.return_value = webull_payload()
    with patch("webull.core.client.ApiClient") as api, patch("webull.data.data_client.DataClient") as data:
        data.return_value.market_data.get_batch_history_bar.return_value = response
        assert len(webull_data.get_history("AAPL")) == 40
        api.return_value.set_logger.assert_called_once()
        api.return_value.add_endpoint.assert_called_once_with("us", "api.webull.com")
        args = data.return_value.market_data.get_batch_history_bar.call_args
        assert args.args == (["AAPL"], "US_STOCK", "D")
        assert args.kwargs["real_time_required"] is False
        data.return_value.market_data.get_batch_history_bar.side_effect = RuntimeError("private-test-secret")
        with pytest.raises(RuntimeError) as error:
            webull_data.get_history("AAPL")
        assert "private-test-secret" not in str(error.value)


def test_hourly_model_rejects_yesterdays_bar(monkeypatch):
    from kingmaker import model
    origin = (pd.Timestamp.now(tz="UTC")-pd.Timedelta(hours=20)).isoformat()
    base = {"meta": {"market_data_provider": "test", "last_bar_at": origin, "current_price": 100},
            "validation_confidence": 90, "predicted_next_close": 104, "model_mse": 1}
    monkeypatch.setattr(model, "base_predict", lambda *_args: base)
    result = model.predict("AAPL", "hour")
    assert not result["data_quality"]["usable"]
    assert result["signal"]["action"] == "HOLD"
