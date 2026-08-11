# PredIQT

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

Prediction responses include the prospective target price plus a transparent
`signal` object: `BUY`, `HOLD`, or `SELL`, expected move, confidence,
horizon-specific move threshold, qualification state, and plain-language
rationale. A directional forecast cannot produce BUY or SELL unless model
error also clears the evidence gate. The web terminal combines the four
horizons into a composite signal; at least two horizons must agree for a
composite BUY or SELL.

Optional env vars:
- `NEWS_API_KEY`
- `FRED_API_KEY`
- `ENV=prod` on hosted environments

## 2) Render deployment

This repo includes `render.yaml` for a single free Render web service.

Steps:
1. In Render, create a new Blueprint and select this GitHub repo.
2. Render detects the root `render.yaml` and creates `prediqt-api`.
3. Set secret env vars when prompted:
   - `NEWS_API_KEY`
   - `FRED_API_KEY`
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
