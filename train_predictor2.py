# train_predictor2.py

import yfinance as yf
import pandas as pd
from datetime import datetime

from kingmaker import (
    trainer_1_transformer_embeddings,
    trainer_2_lstm_price_trend,
    trainer_3_news_ner_sentiment,
    trainer_4_local_llm_sentiment,
    trainer_5_options_pressure,
    trainer_6_dark_pool_volume,
    trainer_7_ai_sentiment_synthesis,
    trainer_8_fund_flow_inference,
    trainer_9_intraday_price_action,
    #trainer_10_insider_algo_clusters,
    trainer_11_rsi,
    trainer_12_macd,
    trainer_13_bollinger_bands,
    trainer_14_sma_crossover,
)

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting prediction")


def train_and_predict2(ticker: str, period: str = "day"):
    print(f"[orchestrator] Training for {ticker} with period '{period}'\n")
    results = {}
    errors = {}

    try:
        # --- Step 1: Basic Heuristic Model ---
        data = yf.Ticker(ticker).history(period="30d", interval="1d")
        if data.empty or len(data) < 10:
            error_msg = "Not enough data for prediction"
            print(f"[heuristic_model] Error: {error_msg}")
            return {"error": error_msg}

        close = data["Close"]
        returns = close.pct_change().dropna()

        recent_return = returns[-3:].mean()
        volatility = returns.std()
        ma_5 = close.rolling(window=5).mean().iloc[-1]
        ma_10 = close.rolling(window=10).mean().iloc[-1]
        ma_ratio = (ma_5 / ma_10) if ma_10 != 0 else 1
        last_close = close.iloc[-1]

        predicted_return = (
            0.6 * recent_return -
            0.4 * volatility +
            0.3 * (ma_ratio - 1)
        )
        predicted_next_close = round(last_close * (1 + predicted_return), 2)
        heuristic_signal = max(min(predicted_return * 10, 1), -1)

        results['heuristic'] = {
            "predicted_next_close": predicted_next_close,
            "predicted_return": predicted_return,
            "heuristic_signal": heuristic_signal,
        }
        print(f"[heuristic_model] Output: {results['heuristic']}")

        # --- Step 2: Technical Indicators via External Trainers (11–14) ---
        technical_indicators = {
            "rsi": trainer_11_rsi,
            "macd": trainer_12_macd,
            "bollinger": trainer_13_bollinger_bands,
            "sma": trainer_14_sma_crossover,
        }

        indicator_scores = []
        indicator_values = {}

        for name, module in technical_indicators.items():
            try:
                res = module.get_signal(ticker)
                score = res.get("score", 0)
                indicator_scores.append(score)
                indicator_values[name] = res
                print(f"[{name}_model] Output: {res}")
            except Exception as e:
                error_msg = str(e)
                errors[f"{name}_model"] = error_msg
                print(f"[{name}_model] Error: {error_msg}")
                indicator_scores.append(0)
                indicator_values[name] = {}

        indicator_avg = sum(indicator_scores) / len(indicator_scores) if indicator_scores else 0
        results['indicator_scores'] = {k: v.get("score", 0) for k, v in indicator_values.items()}
        results['indicator_values'] = {
            "bb_lower": indicator_values.get("bollinger", {}).get("lower"),
            "bb_upper": indicator_values.get("bollinger", {}).get("upper"),
            "sma_short": indicator_values.get("sma", {}).get("sma_short"),
            "sma_long": indicator_values.get("sma", {}).get("sma_long"),
        }
        results['indicator_avg'] = indicator_avg

        # --- Step 3: Advanced Trainers (1–10) ---
        trainer_modules = [
            trainer_1_transformer_embeddings,
            trainer_2_lstm_price_trend,
            trainer_3_news_ner_sentiment,
            trainer_4_local_llm_sentiment,
            trainer_5_options_pressure,
            trainer_6_dark_pool_volume,
            trainer_7_ai_sentiment_synthesis,
            trainer_8_fund_flow_inference,
            trainer_9_intraday_price_action,
            #trainer_10_insider_algo_clusters,
        ]

        trainer_scores = {}
        for idx, mod in enumerate(trainer_modules, 1):
            try:
                result = mod.get_signal(ticker)
                if "error" in result:
                    errors[f"trainer_{idx}"] = result["error"]
                    print(f"[trainer_{idx}_model] Error: {result['error']}")
                    continue
                score = result.get("score")
                if score is None:
                    errors[f"trainer_{idx}"] = "No score returned"
                    print(f"[trainer_{idx}_model] Error: No score returned")
                    continue
                trainer_scores[f"trainer_{idx}"] = score
                print(f"[trainer_{idx}_model] Output: {result}")
            except Exception as e:
                error_msg = str(e)
                errors[f"trainer_{idx}"] = error_msg
                print(f"[trainer_{idx}_model] Error: {error_msg}")

        other_avg = sum(trainer_scores.values()) / len(trainer_scores) if trainer_scores else 0
        results['trainer_scores'] = trainer_scores
        results['other_trainers_avg'] = other_avg

        # --- Step 4: Fuse All Signals ---
        fused_score = (
            0.4 * heuristic_signal +
            0.3 * indicator_avg +
            0.3 * other_avg
        )
        fused_score = max(min(fused_score, 1), -1)
        results['fused_score'] = round(fused_score, 4)

        results['errors'] = errors

        print(f"[fused_model] Output: {results['fused_score']}")

        return results

    except Exception as e:
        error_msg = str(e)
        print(f"[orchestrator] Error: {error_msg}")
        return {"error": error_msg}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python train_predictor2.py <TICKER> [period]")
        sys.exit(1)

    ticker = sys.argv[1]
    period = sys.argv[2] if len(sys.argv) > 2 else "day"

    try:
        result = train_and_predict2(ticker, period)
        print(f"\nPrediction Result for {ticker.upper()} ({period}):")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
