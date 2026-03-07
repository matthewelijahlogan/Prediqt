# PredIQT

PredIQT is now structured as:
- `main.py` + `backend/` + `trainers/`: FastAPI backend and prediction pipeline.
- `mobile/`: React Native (Expo, vanilla JavaScript) standalone app.

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
3. Set secret env vars in Render dashboard:
   - `NEWS_API_KEY`
   - `FRED_API_KEY`

Start command is:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 3) React Native app (mobile/)

Prereqs:
- Node.js 20+
- Expo CLI via `npx`

Setup:
```bash
cd mobile
npm install
```

Configure backend URL:
```bash
cp .env.example .env
```
Set:
- `EXPO_PUBLIC_API_BASE_URL=https://<your-render-service>.onrender.com`

Run:
```bash
npm run start
```

## Notes

- Legacy Cordova artifacts remain in the repository, but active frontend is `mobile/`.
- Prediction quality depends on external APIs and available market/news data.
