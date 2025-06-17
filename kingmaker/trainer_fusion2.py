import os
import json
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

# === LOGGING SETUP ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "predictive_logs")
os.makedirs(LOG_DIR, exist_ok=True)
PREDICTIONS_LOG2_FILE = os.path.join(LOG_DIR, "predictions_log2.json")


def append_prediction_to_log2(entry):
    try:
        if not os.path.exists(PREDICTIONS_LOG2_FILE):
            log = []
        else:
            with open(PREDICTIONS_LOG2_FILE, "r") as f:
                log = json.load(f)
    except json.JSONDecodeError:
        log = []

    log.append(entry)

    with open(PREDICTIONS_LOG2_FILE, "w") as f:
        json.dump(log, f, indent=2)


# === SIGNAL EXTRACTORS ===
def get_signal_trainer_1(ticker):
    res = trainer_1_transformer_embeddings.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("score")
    if score is None:
        return {"error": "No score returned"}
    return {"score": float(score), "details": res}


def get_signal_trainer_2(ticker):
    res = trainer_2_lstm_price_trend.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("trend_signal") or res.get("score")
    if score is None:
        return {"error": "No score returned"}
    return {"score": float(score), "details": res}


def get_signal_trainer_3(ticker):
    res = trainer_3_news_ner_sentiment.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("score") or res.get("sentiment_score")
    if score is None:
        return {"error": "No score returned"}
    return {"score": float(score), "details": res}


def get_signal_trainer_4(ticker):
    res = trainer_4_local_llm_sentiment.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("score") or res.get("sentiment")
    if score is None:
        return {"error": "No score returned"}
    return {"score": float(score), "details": res}


def get_signal_trainer_5(ticker):
    res = trainer_5_options_pressure.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("options_pressure_score") or res.get("score")
    if score is None:
        return {"error": "No score returned"}
    return {"score": float(score), "details": res}


def get_signal_trainer_6(ticker):
    res = trainer_6_dark_pool_volume.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("dark_pool_score") or res.get("score")
    if score is None:
        return {"error": "No score returned"}
    return {"score": float(score), "details": res}


def get_signal_trainer_7(ticker):
    res = trainer_7_ai_sentiment_synthesis.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("synthetic_sentiment_score")
    if score is None:
        return {"error": "No score returned"}
    return {"score": float(score), "details": res}


def get_signal_trainer_8(ticker):
    res = trainer_8_fund_flow_inference.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("fund_flow_score") or res.get("score")
    if score is None:
        return {"error": "No score returned"}
    return {"score": float(score), "details": res}


def get_signal_trainer_9(ticker):
    res = trainer_9_intraday_price_action.train_and_predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    try:
        predicted = res.get("predicted_next_close")
        import yfinance as yf
        data = yf.Ticker(ticker).history(period="5d", interval="1d", progress=False)
        last_close = data['Close'].iloc[-1] if not data.empty else None
        if last_close is None or predicted is None:
            return {"error": "Insufficient data for normalization"}
        change = (predicted - last_close) / last_close
        score = max(min(change, 1), -1)
        return {"score": score, "details": res}
    except Exception as e:
        return {"error": str(e)}


#def get_signal_trainer_10(ticker):
    #res = trainer_10_insider_algo_clusters.predict(ticker)
    #if "error" in res:
    #    return {"error": res["error"]}
    #score = res.get("insider_cluster_score")
    #if score is None:
    #    return {"error": "No score returned"}
    #score_mapped = (score - 0.5) * 2
    #return {"score": float(score_mapped), "details": res}


def get_signal_trainer_11(ticker):
    res = trainer_11_rsi.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("rsi_signal")
    if score is None:
        return {"error": "No RSI signal"}
    return {"score": float(score), "details": res}


def get_signal_trainer_12(ticker):
    res = trainer_12_macd.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("macd_signal")
    if score is None:
        return {"error": "No MACD signal"}
    return {"score": float(score), "details": res}


def get_signal_trainer_13(ticker):
    res = trainer_13_bollinger_bands.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("bb_signal")
    if score is None:
        return {"error": "No Bollinger Bands signal"}
    return {"score": float(score), "details": res}


def get_signal_trainer_14(ticker):
    res = trainer_14_sma_crossover.predict(ticker)
    if "error" in res:
        return {"error": res["error"]}
    score = res.get("sma_crossover_signal")
    if score is None:
        return {"error": "No SMA crossover signal"}
    return {"score": float(score), "details": res}


def fuse_all_trainer_signals(ticker: str):
    adapters = [
        get_signal_trainer_1,
        get_signal_trainer_2,
        get_signal_trainer_3,
        get_signal_trainer_4,
        get_signal_trainer_5,
        get_signal_trainer_6,
        get_signal_trainer_7,
        get_signal_trainer_8,
        get_signal_trainer_9,
        get_signal_trainer_10,
        get_signal_trainer_11,
        get_signal_trainer_12,
        get_signal_trainer_13,
        get_signal_trainer_14,
    ]

    signals = {}
    total_score = 0.0
    count = 0
    errors = {}

    for idx, get_signal in enumerate(adapters, 1):
        try:
            result = get_signal(ticker)
            if "error" in result:
                errors[f"trainer_{idx}"] = result["error"]
                continue
            score = result.get("score")
            if score is None:
                errors[f"trainer_{idx}"] = "No score returned"
                continue
            signals[f"trainer_{idx}"] = score
            total_score += score
            count += 1
        except Exception as e:
            errors[f"trainer_{idx}"] = str(e)

    if count == 0:
        return {"error": "No valid signals from any trainer", "details": errors}

    fused_score = total_score / count

    return {
        "fused_score": round(fused_score, 4),
        "individual_scores": signals,
        "errors": errors,
    }


if __name__ == "__main__":
    ticker = "AAPL"
    fusion_result = fuse_all_trainer_signals(ticker)
    print(f"Fused signals for {ticker}:\n{json.dumps(fusion_result, indent=2)}")

    if "fused_score" in fusion_result:
        append_prediction_to_log2({
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "fused_score": fusion_result["fused_score"],
            "individual_scores": fusion_result["individual_scores"],
            "errors": fusion_result["errors"],
            "model": "trainer_fusion2"
        })
