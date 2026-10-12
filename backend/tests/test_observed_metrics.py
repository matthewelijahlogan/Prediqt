import json
from unittest.mock import patch

from kingmaker import ledger, opportunities


def test_daily_rankings_separate_signs_and_do_not_pad():
    def candidate(symbol, *_):
        move = int(symbol[1:]) - 12
        return {"ticker": symbol, "change_percent": move, "movement_score": 50,
                "qualified_driver": False, "estimated_net_move_percent": 0,
                "forecast": {"validation_confidence": 10}}
    with patch.object(opportunities, "candidate", side_effect=candidate):
        board = opportunities.build_board([f"S{i}" for i in range(25)])
        assert len(board["daily_gainers"]) == len(board["daily_losers"]) == 10
        assert board["daily_gainers"][0]["change_percent"] == 12
        assert board["daily_losers"][0]["change_percent"] == -12
        assert all(x["change_percent"] > 0 for x in board["daily_gainers"])
        assert all(x["change_percent"] < 0 for x in board["daily_losers"])
        assert opportunities.build_board(["S12"])["daily_gainers"] == []
        assert opportunities.build_board(["S0"], "hour")["daily_losers"] == []


def test_metrics_only_score_settled_first_seen_forecasts(tmp_path, monkeypatch):
    monkeypatch.setenv("KINGMAKER_LEDGER_PATH", str(tmp_path / 'ledger.sqlite3'))
    with ledger.connect() as db:
        for i, actual in enumerate([104, None]):
            db.execute("INSERT INTO forecasts (ticker,horizon,model,origin,created_at,payload,actual_close) VALUES (?,?,?,?,?,?,?)",
                       ("AAPL", "day", "test", str(i), "2026-10-12", json.dumps({"current_price": 100, "predicted_next_close": 103}), actual))
    db.close()
    result = ledger.metrics()["horizons"]["day"]
    assert result["recorded"] == 2 and result["pending"] == result["settled"] == 1
    assert result["mae_dollars"] == result["rmse_dollars"] == 1
    assert result["baseline_rmse_dollars"] == 4
    assert result["direction_accuracy"] == 1


def test_empty_metrics_do_not_fabricate_performance(tmp_path, monkeypatch):
    monkeypatch.setenv("KINGMAKER_LEDGER_PATH", str(tmp_path / 'empty.sqlite3'))
    assert ledger.metrics()["horizons"] == {}
