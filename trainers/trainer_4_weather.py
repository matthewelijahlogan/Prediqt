import requests
from datetime import datetime

# Lat/Lon + Sector tags per ticker
TICKER_INFO = {
    "AAPL":  {"lat": 37.3349, "lon": -122.0090, "sector": "tech"},
    "TSLA":  {"lat": 30.2672, "lon": -97.7431,  "sector": "auto"},
    "GOOGL": {"lat": 37.4220, "lon": -122.0841, "sector": "tech"},
    "MSFT":  {"lat": 47.6426, "lon": -122.1350, "sector": "tech"},
    "AMZN":  {"lat": 47.6229, "lon": -122.3366, "sector": "retail"},
    "UAL":   {"lat": 41.9742, "lon": -87.9073,  "sector": "airline"},
    "AAL":   {"lat": 32.8998, "lon": -97.0403,  "sector": "airline"},
    "DE":    {"lat": 41.5055, "lon": -90.5776,  "sector": "agriculture"},
}

def get_season(month: int):
    return (
        "winter" if month in [12, 1, 2]
        else "spring" if month in [3, 4, 5]
        else "summer" if month in [6, 7, 8]
        else "fall"
    )

def predict(ticker: str, horizon: str = "day") -> dict:
    info = TICKER_INFO.get(ticker.upper())
    if not info:
        return {
            "trainer": "weather",
            "adjustment": 1.0,
            "confidence": 0.0,
            "meta": {
                "reason": "No location/sector mapping for this ticker"
            }
        }

    lat, lon, sector = info["lat"], info["lon"], info["sector"]
    season = get_season(datetime.now().month)

    try:
        response = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true",
            timeout=10
        )
        response.raise_for_status()
        weather = response.json()["current_weather"]

        temp = weather["temperature"]
        wind = weather["windspeed"]
        code = weather["weathercode"]

        # Default state
        impact = 0.0
        confidence = 0.2
        reason = "Neutral"
        sensitive = False

        if sector == "airline":
            if season == "winter" and wind > 25:
                impact = -0.05
                reason = "High wind in winter - flight risk"
                sensitive = True
            elif code in [51, 61, 71, 73]:  # rain/snow codes
                impact = -0.03
                reason = "Precipitation likely affecting flights"
                sensitive = True

        elif sector == "retail":
            if season == "winter" and 32 < temp < 60:
                impact = +0.03
                reason = "Mild weather supports shopping"
            elif temp < 20 or temp > 100:
                impact = -0.03
                reason = "Extreme temp may suppress in-store sales"

        elif sector == "agriculture":
            if temp < 32:
                impact = -0.05
                reason = "Freeze risk to crops"
                sensitive = True
            elif temp > 100:
                impact = -0.04
                reason = "Heat stress on crops"
                sensitive = True

        if sensitive:
            confidence = 0.8

        # Convert impact (-0.05 to +0.03 etc) into multiplier adjustment around 1.0
        adjustment = round(1.0 + impact, 5)

        return {
            "trainer": "weather",
            "adjustment": adjustment,
            "confidence": round(confidence, 3),
            "meta": {
                "sector": sector,
                "season": season,
                "temperature": temp,
                "windspeed": wind,
                "weather_code": code,
                "reason": reason
            }
        }

    except Exception as e:
        return {
            "trainer": "weather",
            "adjustment": 1.0,
            "confidence": 0.0,
            "meta": {
                "error": str(e),
                "reason": "Weather API call failed"
            }
        }
