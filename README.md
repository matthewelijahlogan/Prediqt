# PredIQT

Kingmaker v1 now powers `/predict/{ticker}` and the web terminal. It builds on
the existing price-feature Ridge model, with three expanding validation folds,
purged horizon-overlapping labels, and a final refit on available labeled data.
This is a new implementation; the older Kingmaker described in `GPT_Recap.txt`
was not present in this checkout. Legacy heuristic trainers remain available
through `legacy_train_and_predict` but do not affect Kingmaker forecasts.

Open `http://127.0.0.1:8000` after starting the backend to use the watchlist scanner.
`GET /api/kingmaker/scan?tickers=AAPL,MSFT,NVDA&horizon=day` compares up to 20
symbols and includes per-symbol failures. `GET /api/kingmaker/status` describes
the model. Forecasts expose validation errors, a no-change baseline, fold sizes,
data provider, and the last bar timestamp. Confidence is a validation quality
score, not a calibrated probability of profit. Stale fallback history and bars
older than four calendar days cannot qualify for a directional signal.

Profitability is unproven: these are forecast-error checks, not a portfolio
backtest with costs or a live trading record. The scheduler no longer scores new
forecasts against the current price. First-seen forecasts for each symbol,
horizon, model version, and origin bar are recorded in `data/kingmaker.sqlite3`.
`GET /api/kingmaker/forecasts` lists them; `POST /api/kingmaker/settle` records
observed outcomes only when a subsequent bar proves the target bar has ended.
The enabled scheduler also settles earlier forecasts before each batch. Set
`KINGMAKER_LEDGER_PATH` to persistent storage on hosted deployments; Render's
ephemeral filesystem does not retain this ledger across redeploys.
No weekly income target is guaranteed. Broker
execution remains paper-only and requires configured credentials and approval.

Verify backend changes with `python -m pytest backend/tests -q` (install `pytest`
and `httpx` in your development environment if needed).

PredIQT is now structured as:
- `main.py` + `backend/` + `trainers/`: FastAPI backend and prediction pipeline.
- `mobile-native-app/`: Bare React Native CLI app (vanilla JavaScript, no Expo).
- `auto_trainer.py`: background trainer loop for ongoing model signal updates.

## 1) Backend (local)

Prereqs:
- Python 3.11

Run:
```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health check:
- `GET /health`

Key endpoints used by mobile:
- `GET /predict/{ticker}?horizon=hour|day|week|month`
- `GET /api/quote?ticker=...`
- `GET /api/ticker-tape`
- `GET /api/news`
- `GET /api/market-data/status`
- `GET /api/automation/status`
- `POST /api/automation/proposals`
- `POST /api/automation/proposals/{id}/approve|reject`

Prediction responses include the prospective target price plus a transparent
`signal` object: `BUY`, `HOLD`, or `SELL`, expected move, confidence,
horizon-specific move threshold, qualification state, and plain-language
rationale. A directional forecast cannot produce BUY or SELL unless model
error also clears the evidence gate. The web terminal combines the four
horizons into a composite signal; at least two horizons must agree for a
composite BUY or SELL.

The Automation Machine converts a qualified composite BUY into a proposed
dollar-notional order. Every proposal remains `PENDING_APPROVAL` until approved
from the dashboard. Execution is intentionally limited to Alpaca paper trading;
configure `ALPACA_PAPER_API_KEY` and `ALPACA_PAPER_SECRET_KEY` on Render to
enable submission. Live brokerage execution is not enabled.

Core price history uses a provider chain rather than depending on one scraper:
Alpaca Market Data, then Alpha Vantage, then Yahoo, followed by a last-known-good
cache that can remain available for up to 24 hours. Configure
`ALPHA_VANTAGE_API_KEY` to enable that independent fallback. Provider health is
visible at `/api/market-data/status`.

Optional env vars:
- `NEWS_API_KEY`
- `FRED_API_KEY`
- `ENV=prod` on hosted environments
- `ALPACA_PAPER_API_KEY`
- `ALPACA_PAPER_SECRET_KEY`
- `AUTOMATION_MAX_NOTIONAL=100`
- `ALPHA_VANTAGE_API_KEY`

## 2) Render deployment

This repo includes `render.yaml` for a single free Render web service.

Steps:
1. In Render, create a new Blueprint and select this GitHub repo.
2. Render detects the root `render.yaml` and creates `prediqt-api`.
3. Set secret env vars when prompted:
   - `NEWS_API_KEY`
   - `FRED_API_KEY`
   - `ALPACA_PAPER_API_KEY`
   - `ALPACA_PAPER_SECRET_KEY`
   - `ALPHA_VANTAGE_API_KEY`
4. Deploy and verify `GET /health` returns `{"status":"ok"}`.

Start command is:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Render does not offer free background workers. The Blueprint therefore keeps
the optional trainer scheduler disabled. To run `auto_trainer.py` continuously,
add a paid background worker and configure `INTERNAL_SYNC_TOKEN` and
`PREDIQT_API_URL` on that worker.

## 3) React Native app (mobile-native-app, no Expo)

Prereqs:
- Node.js 20+
- Android Studio + Android SDK
- A connected Android device with USB debugging enabled, or an emulator

Setup:
```bash
cd mobile-native-app
npm install
```

Run Metro:
```bash
npm run start
```

Install on Android:
```bash
npm run android
```

## Notes

- Legacy Cordova and Expo artifacts remain in the repository, but active mobile frontend is `mobile-native-app/`.
- Prediction quality depends on external APIs and available market/news data.
