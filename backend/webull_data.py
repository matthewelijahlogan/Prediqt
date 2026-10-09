"""Read-only integration with Webull's official OpenAPI SDK."""
import os
import logging
from pathlib import Path

import numpy as np
import pandas as pd


def status():
    configured = bool(os.environ.get("WEBULL_APP_KEY", "").strip() and os.environ.get("WEBULL_APP_SECRET", "").strip())
    return {"configured": configured, "access_verified": False, "execution": "manual",
            "note": "Approved OpenAPI access and market-data entitlement are required. This adapter only reads historical bars; no Webull orders are submitted."}


def normalize_bars(payload, symbol):
    if not isinstance(payload, dict) or not isinstance(payload.get("result"), list):
        raise ValueError("Unexpected Webull history response")
    group = next((item for item in payload["result"] if isinstance(item, dict) and item.get("symbol") == symbol), None)
    if not group or not isinstance(group.get("result"), list) or len(group["result"]) < 30:
        raise ValueError("Insufficient Webull history")
    rows = []
    for bar in group["result"]:
        if not isinstance(bar, dict):
            raise ValueError("Malformed Webull bar")
        row = {name.title(): float(bar[name]) for name in ("open", "high", "low", "close", "volume")}
        at = pd.to_datetime(bar["time"], utc=True, errors="coerce")
        if pd.isna(at) or not all(np.isfinite(v) for v in row.values()) or min(row[k] for k in ("Open", "High", "Low", "Close")) <= 0 or row["Volume"] < 0:
            raise ValueError("Invalid Webull bar evidence")
        rows.append({"Date": at, **row})
    frame = pd.DataFrame(rows).set_index("Date").sort_index()
    if frame.index.has_duplicates:
        raise ValueError("Duplicate Webull bar timestamps")
    return frame


def get_history(symbol, horizon="day"):
    if not status()["configured"]:
        raise RuntimeError("not configured")
    try:
        from webull.core.client import ApiClient
        from webull.data.data_client import DataClient
        client = ApiClient(os.environ["WEBULL_APP_KEY"], os.environ["WEBULL_APP_SECRET"], "us",
                           connect_timeout=5, timeout=10, auto_retry=False)
        # SDK error logs include signed request headers. Disable that logger
        # before initialization or any authenticated request.
        sdk_logger = logging.getLogger("kingmaker.webull_sdk")
        sdk_logger.disabled = True
        client.set_logger(sdk_logger)
        client.set_stream_logger(log_level=logging.CRITICAL+1, logger_name="kingmaker.webull_sdk")
        client.set_token_dir(str(Path(__file__).resolve().parents[1] / ".runtime" / "webull"))
        client.add_endpoint("us", "api.webull.com")
        response = DataClient(client).market_data.get_batch_history_bar(
            [symbol], "US_ETF" if symbol in {"SPY", "QQQ", "IWM", "GLD", "XLE"} else "US_STOCK",
            "M60" if horizon == "hour" else "D", count=500,
            real_time_required=False, trading_sessions=["RTH"])
        if response.status_code != 200:
            raise RuntimeError("Webull access or market-data request rejected")
        return normalize_bars(response.json(), symbol)
    except Exception:
        # SDK/HTTP exceptions can contain authentication material.
        raise RuntimeError("Webull history unavailable; verify OpenAPI credentials and data entitlement") from None
