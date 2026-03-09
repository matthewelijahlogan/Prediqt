# PredIQT

PredIQT is now structured as:
- `main.py` + `backend/` + `trainers/`: FastAPI backend and prediction pipeline.
- `mobile-native-app/`: Bare React Native CLI app (vanilla JavaScript, no Expo).
- `auto_trainer.py`: background trainer loop for ongoing model signal updates.

## 1) Backend (local)

Prereqs:
- Python 3.11+

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

Optional env vars:
- `NEWS_API_KEY`
- `FRED_API_KEY`
- `ENV=prod` on hosted environments

## 2) Render deployment

This repo includes `render.yaml`.

Steps:
1. Create a Render Web Service from this GitHub repo.
2. Ensure Render detects `render.yaml`.
3. `render.yaml` defines two services:
   - `prediqt-api` (web API)
   - `prediqt-trainer` (background trainer worker)
4. Set secret env vars in Render dashboard:
   - `NEWS_API_KEY`
   - `FRED_API_KEY`

Start command is:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Trainer worker command is:
```bash
python auto_trainer.py
```

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
