# train_predictor.py

from trainers import trainer_1_yfinance as base_model
from trainers import trainer_2_sentiment as sentiment_model
from trainers import trainer_3_pelosi as pelosi_model
from trainers import trainer_4_weather as weather_model
from trainers import trainer_5_macro as macro_model
from trainers import trainer_6_earnings as earnings_model
from trainers import trainer_7_social as social_model
from trainers import trainer_8_sector as sector_model
from trainers import trainer_9_insider_trading as insider_model
from trainers import trainer_10_options_flow as options_model
from trainers import trainer_11_technical_indicators as technical_model
from trainers import trainer_12_etf_sector_model as etf_sector_model
from trainers import trainer_13_volume as volume_model
from trainers import trainer_14_patterns as patterns_model
from trainers import trainer_15_volatility as volatility_model
from trainers import trainer_16_predictivelog as predictivelog_model
from trainers import trainer_17_news as news_model
from trainers import trainer_fusion as fusion_model

from datetime import datetime
import yfinance as yf
from fastapi import HTTPException

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting prediction")


def train_and_predict(ticker: str, horizon: str = "hour"):
    print(f"[orchestrator] Training for {ticker} with horizon '{horizon}'\n")
    results = {}

    # --- 1) Delisted check ---
    try:
        info = yf.Ticker(ticker).info
        if not info or info.get("regularMarketPrice") is None:
            # no price => assume delisted or invalid
            raise HTTPException(status_code=404, detail="Ticker not found or delisted")
    except HTTPException:
        # bubble up our 404
        raise
    except Exception as e:
        # other yfinance error
        raise HTTPException(status_code=503, detail="Error fetching ticker info")

    # Base model always runs with ticker and horizon
    try:
        base_res = base_model.predict(ticker, horizon)
        if "error" in base_res:
            print(f"[base_model] Error in prediction: {base_res['error']}")
            results['base'] = None
        else:
            results['base'] = base_res
        print(f"[base_model] Output: {results['base']}")
    except Exception as e:
        print(f"[base_model] Exception: {e}")
        results['base'] = None

    # Horizon-specific active models
    horizon_model_map = {
        "hour": ["sentiment", "technical", "volume", "patterns", "volatility"],
        "day": ["sentiment", "technical", "volume", "patterns", "volatility", "macro", "predictivelog", "news"],
        "week": [
            "pelosi", "weather", "macro", "earnings", "social", "sector",
            "insider", "options", "technical", "etf_sector", "volume",
            "patterns", "volatility", "predictivelog", "news"
        ],
        "month": [
            "pelosi", "weather", "macro", "earnings", "social", "sector",
            "insider", "options", "technical", "etf_sector", "volume",
            "patterns", "volatility", "predictivelog", "news"
        ]
    }

    active_models = set(horizon_model_map.get(horizon, []))

    model_list = {
        "sentiment": sentiment_model,
        "pelosi": pelosi_model,
        "weather": weather_model,
        "macro": macro_model,
        "earnings": earnings_model,
        "social": social_model,
        "sector": sector_model,
        "insider": insider_model,
        "options": options_model,
        "technical": technical_model,
        "etf_sector": etf_sector_model,
        "volume": volume_model,
        "patterns": patterns_model,
        "volatility": volatility_model,
        "predictivelog": predictivelog_model,
        "news": news_model
    }

    for name, model in model_list.items():
        if name not in active_models:
            print(f"[{name}_model] Skipped for horizon '{horizon}'")
            results[name] = None
            continue

        try:
            # Some models don't support 'horizon' as an argument
            try:
                res = model.predict(ticker, horizon)
            except TypeError:
                res = model.predict(ticker)

            if res and "error" in res:
                print(f"[{name}_model] Error in prediction: {res['error']}")
                results[name] = None
            else:
                results[name] = res
            print(f"[{name}_model] Output: {results[name]}")
        except Exception as e:
            print(f"[{name}_model] Exception: {e}")
            results[name] = None

    print(f"[fusion_model] Inputs: {results}")

    try:
        # Fusion expects dict of results (trainer_results), plus horizon param for scaling
        fused = fusion_model.predict(results, mode="heuristic", horizon=horizon)
        print(f"[fusion_model] Output: {fused}")
        return fused
    except Exception as e:
        print(f"[fusion_model] Error: {e}")
        return {"error": f"fusion model failed: {str(e)}"}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python train_predictor.py <TICKER> [horizon]")
        sys.exit(1)

    ticker = sys.argv[1]
    horizon = sys.argv[2] if len(sys.argv) > 2 else "hour"

    try:
        result = train_and_predict(ticker, horizon)
        print(f"\nPrediction Result for {ticker.upper()} ({horizon}):")
        print(result)
    except HTTPException as http_e:
        print(f"HTTP {http_e.status_code}: {http_e.detail}")
    except Exception as e:
        print(f"Error: {e}")
