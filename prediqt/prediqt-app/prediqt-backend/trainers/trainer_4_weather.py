# trainer_4_weather.py

import requests
from datetime import datetime

# Basic sector mapping per ticker
TICKER_INFO = {
    "AAPL": {"lat": 37.3349, "lon": -122.0090, "sector": "tech"},
    "TSLA": {"lat": 30.2672, "lon": -97.7431, "sector": "auto"},
    "GOOGL": {"lat": 37.4220, "lon": -122.0841, "sector": "tech"},
    "MSFT": {"lat": 47.6426, "lon": -122.1350, "sector": "tech"},
    "AMZN": {"lat": 47.6229, "lon": -122.3366, "sector": "retail"},
    "UAL": {"lat": 41.9742, "lon": -87.9073, "sector": "airline"},  # United
    "AAL": {"lat": 32.8998, "lon": -97.0403, "sector": "airline"},  # American Airlines
    "DE": {"lat": 41.5055, "lon": -90.5776, "sector": "agriculture"},  # John Deere
}


def get_season(month: int):
    """Return the current season based on month (North Hemisphere)."""
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"


def predict(ticker: str):
    print(f"[trainer_4_weather] Checking weather impact for {ticker}...")

    info = TICKER_INFO.get(ticker.upper())
    if not info:
        print("[weather_model] No location/sector for this ticker. Returning neutral.")
        return {"adjustment": 1.0, "weather_sensitive": False}

    lat, lon = info["lat"], info["lon"]
    sector = info["sector"]
    month = datetime.now().month
    season = get_season(month)

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url)
        data = response.json()
        weather = data["current_weather"]

        temp = weather["temperature"]
        wind = weather["windspeed"]
        code = weather["weathercode"]

        # Default values
        adjustment = 1.0
        sensitive = False
        reasoning = "neutral"

        # Weather impact logic
        if sector == "airline":
            if season == "winter" and wind > 25:
                adjustment = 0.92
                sensitive = True
                reasoning = "High wind in winter - flight risk"
            elif code in [51, 61, 71, 73]:  # rain, snow
                adjustment = 0.94
                sensitive = True
                reasoning = "Precipitation likely affecting flights"

        elif sector == "retail":
            if season == "winter" and 32 < temp < 60:
                adjustment = 1.03
                reasoning = "Good holiday shopping weather"
            elif temp < 20 or temp > 100:
                adjustment = 0.97
                reasoning = "Poor weather affecting shoppers"
        
        elif sector == "agriculture":
            if temp < 32:
                adjustment = 0.9
                reasoning = "Freeze risk for crops"
                sensitive = True
            elif temp > 100:
                adjustment = 0.92
                reasoning = "Heat stress on crops"
                sensitive = True

        # More sectors/logic can be added here...

        result = {
            "adjustment": round(adjustment, 3),
            "weather_sensitive": sensitive,
            "sector": sector,
            "season": season,
            "temperature": temp,
            "windspeed": wind,
            "weather_code": code,
            "reasoning": reasoning,
        }

        print(f"[weather_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[weather_model] Error: {e}")
        return {"adjustment": 1.0, "weather_sensitive": False}
