import os

DISTRICT_COORDINATES = {
    "Mumbai": {
        "lat": 19.0760,
        "lon": 72.8777,
        "elevation_m": 14
    },
    "Pune": {
        "lat": 18.5204,
        "lon": 73.8567,
        "elevation_m": 560
    },
    "Nagpur": {
        "lat": 21.1458,
        "lon": 79.0882,
        "elevation_m": 310
    },
    "Nashik": {
        "lat": 19.9975,
        "lon": 73.7898,
        "elevation_m": 560
    },
    "Kolhapur": {
        "lat": 16.7050,
        "lon": 74.2433,
        "elevation_m": 569
    },
    "Sangli": {
        "lat": 16.8524,
        "lon": 74.5815,
        "elevation_m": 549
    },
    "Satara": {
        "lat": 17.6805,
        "lon": 73.9933,
        "elevation_m": 742
    },
    "Thane": {
        "lat": 19.2183,
        "lon": 72.9781,
        "elevation_m": 7
    },
    "Raigad": {
        "lat": 18.2376,
        "lon": 73.4445,
        "elevation_m": 25
    },
    "Ratnagiri": {
        "lat": 16.9902,
        "lon": 73.3120,
        "elevation_m": 11
    },
    "Sindhudurg": {
        "lat": 16.3492,
        "lon": 73.5594,
        "elevation_m": 10
    },
    "Palghar": {
        "lat": 19.6967,
        "lon": 72.7699,
        "elevation_m": 15
    },
    "Aurangabad": {
        "lat": 19.8762,
        "lon": 75.3433,
        "elevation_m": 568
    },
    "Chhatrapati Sambhajinagar": {
        "lat": 19.8762,
        "lon": 75.3433,
        "elevation_m": 568
    },
    "Gadchiroli": {
        "lat": 20.1849,
        "lon": 80.0000,
        "elevation_m": 217
    },
    "Chandrapur": {
        "lat": 19.9615,
        "lon": 79.2961,
        "elevation_m": 189
    },
    "Bhandara": {
        "lat": 21.1702,
        "lon": 79.6480,
        "elevation_m": 244
    }
}
# ==========================================
# SERVER
# ==========================================

HOST = "0.0.0.0"
PORT = 3000
DEBUG = True

APP_NAME = "ForesightX Flood Prediction"

# ==========================================
# PATHS
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BACKEND_DIR = os.path.join(BASE_DIR, "backend")

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

DATA_DIR = os.path.join(BASE_DIR, "data")

# Database
DATABASE_FILE = os.path.join(DATA_DIR, "foresightx.db")

# CSV
LIVE_CSV_PATH = os.path.join(DATA_DIR, "live_weather_data.csv")

# Model
MODEL_FILE = os.path.join(DATA_DIR, "model.pkl")

TRAINING_DATA_FILE = os.path.join(DATA_DIR, "flood_data.csv")

# ==========================================
# APIs
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
# ==========================================
# DISTRICT COORDINATES
# ==========================================

DISTRICT_COORDINATES = {
    "Sindhudurg": {
        "latitude": 16.3492,
        "longitude": 73.5178
    }
}
TIMEZONE = "Asia/Kolkata"
