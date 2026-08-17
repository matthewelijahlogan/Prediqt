import os

import requests


PAPER_API_BASE = "https://paper-api.alpaca.markets"


def _credentials() -> tuple[str, str]:
    key = os.environ.get("ALPACA_PAPER_API_KEY", "").strip()
    secret = os.environ.get("ALPACA_PAPER_SECRET_KEY", "").strip()
    if not key or not secret:
        raise RuntimeError(
            "Alpaca paper trading is not connected. Configure "
            "ALPACA_PAPER_API_KEY and ALPACA_PAPER_SECRET_KEY in Render."
        )
    return key, secret


def _headers() -> dict[str, str]:
    key, secret = _credentials()
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
        "Content-Type": "application/json",
    }


def submit_market_order(
    symbol: str,
    side: str,
    notional: float,
    client_order_id: str,
) -> dict:
    headers = _headers()

    # Check the deterministic client ID first so approval retries cannot create
    # a second order after a network timeout on a successful submission.
    lookup = requests.get(
        f"{PAPER_API_BASE}/v2/orders:by_client_order_id",
        params={"client_order_id": client_order_id},
        headers=headers,
        timeout=15,
    )
    if lookup.status_code == 200:
        return lookup.json()
    if lookup.status_code != 404:
        raise RuntimeError(f"Alpaca order lookup failed ({lookup.status_code}): {lookup.text[:200]}")

    response = requests.post(
        f"{PAPER_API_BASE}/v2/orders",
        headers=headers,
        json={
            "symbol": symbol,
            "notional": f"{notional:.2f}",
            "side": side,
            "type": "market",
            "time_in_force": "day",
            "client_order_id": client_order_id,
        },
        timeout=15,
    )
    if response.status_code not in {200, 201}:
        raise RuntimeError(f"Alpaca paper order failed ({response.status_code}): {response.text[:300]}")
    return response.json()
