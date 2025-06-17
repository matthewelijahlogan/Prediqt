def predict(ticker):
    return {
        "insider_cluster_score": None,
        "note": "Insider cluster analysis disabled due to lack of free data sources."
    }
    
def get_signal(ticker: str):
    return {"score": 0, "error": "Trainer 10 is temporarily disabled"}


if __name__ == "__main__":
    print(predict("AAPL"))
