import os

# ==========================================
# SERVER
# ==========================================

HOST = "0.0.0.0"
PORT = 5001
DEBUG = True


# ==========================================
# OPEN-METEO
# ==========================================

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"

API_TIMEOUT = 10

TIMEZONE = "Asia/Kolkata"


# ==========================================
# DATA FOLDER
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

LIVE_CSV_PATH = os.path.join(
    DATA_DIR,
    "live_weather_data.csv"
)