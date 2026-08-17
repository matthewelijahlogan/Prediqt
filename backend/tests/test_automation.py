import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.automation import proposal_store
from main import app


class AutomationApiTests(unittest.TestCase):
    def setUp(self):
        with proposal_store._lock:
            proposal_store._items.clear()
        self.client = TestClient(app)

    def test_qualified_order_is_only_proposed_until_approval(self):
        response = self.client.post(
            "/api/automation/proposals",
            json={
                "symbol": "AAPL",
                "side": "buy",
                "notional": 25,
                "rationale": "2/4 BUY horizons",
            },
        )

        self.assertEqual(response.status_code, 200)
        proposal = response.json()
        self.assertEqual(proposal["status"], "PENDING_APPROVAL")
        self.assertIsNone(proposal["broker_order_id"])

    def test_approval_submits_one_paper_order(self):
        proposal = self.client.post(
            "/api/automation/proposals",
            json={"symbol": "AAPL", "side": "buy", "notional": 25},
        ).json()
        broker_order = {"id": "paper-order-1", "status": "accepted"}

        with patch("backend.routers.automation.submit_market_order", return_value=broker_order) as submit:
            response = self.client.post(
                f"/api/automation/proposals/{proposal['proposal_id']}/approve"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "SUBMITTED")
        self.assertEqual(response.json()["broker_order_id"], "paper-order-1")
        submit.assert_called_once_with(
            "AAPL", "buy", 25.0, proposal["client_order_id"]
        )

    def test_failed_broker_connection_keeps_proposal_approvable(self):
        proposal = self.client.post(
            "/api/automation/proposals",
            json={"symbol": "AAPL", "side": "buy", "notional": 25},
        ).json()

        with patch(
            "backend.routers.automation.submit_market_order",
            side_effect=RuntimeError("paper broker not configured"),
        ):
            response = self.client.post(
                f"/api/automation/proposals/{proposal['proposal_id']}/approve"
            )

        self.assertEqual(response.status_code, 503)
        stored = self.client.get("/api/automation/proposals").json()["items"][0]
        self.assertEqual(stored["status"], "PENDING_APPROVAL")
        self.assertIn("not configured", stored["error"])

    def test_notional_cannot_exceed_policy_limit(self):
        response = self.client.post(
            "/api/automation/proposals",
            json={"symbol": "AAPL", "side": "buy", "notional": 1000},
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
