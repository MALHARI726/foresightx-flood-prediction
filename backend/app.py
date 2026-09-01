import csv
import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import DISTRICT_COORDINATES


# Initialize Flask app
app = Flask(
    __name__,
    template_folder='../frontend',
    static_folder='../frontend/static'
)
app.config['SECRET_KEY'] = 'maha-flood-ai-secret-2026'
from functools import lru_cache

import pandas as pd
import requests
from flask import Flask, jsonify, render_template, request

from config import DISTRICT_COORDINATES, GEOCODING_API_URL, WEATHER_API_URL, API_TIMEOUT, TIMEZONE
from prediction import predict_flood_risk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
FLOOD_HISTORY_FILE = os.path.join(RAW_DIR, "flood_history.csv")
WEATHER_FILE = os.path.join(RAW_DIR, "weather.csv")
LIVE_FILE = os.path.join(DATA_DIR, "live_weather_data.csv")
DB_FILE = os.path.join(os.path.dirname(__file__), "database.db")

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "frontend"), static_folder=os.path.join(BASE_DIR, "static"))
app.config["SECRET_KEY"] = "maha-flood-ai-2026"



def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()
HISTORICAL_FLOOD_EVENTS=[
    {
        "year": "2005",
        "event_name": "Maharashtra & Mumbai Cloudburst Deluge",
        "affected_districts": "Mumbai, Thane, Raigad, Ratnagiri",
        "rainfall_mm": 944.0,
        "severity": "CRITICAL CATASTROPHIC",
        "summary": "Historic cloudburst dropped 944mm in 24 hours over Santacruz. Mithi River overflowed, paralyzing suburban transport and causing widespread urban inundation."
    },
    {
        "year": "2019",
        "event_name": "Krishna Basin Major Inundation",
        "affected_districts": "Kolhapur, Sangli, Satara, Pune",
        "rainfall_mm": 380.0,
        "severity": "CRITICAL RED ALERT",
        "summary": "Unprecedented continuous monsoon spells over Mahabaleshwar and Western Ghats caused Panchganga and Krishna rivers to surge 12+ meters above danger mark."
    },
    {
        "year": "2021",
        "event_name": "Konkan Chiplun-Mahad Flash Floods",
        "affected_districts": "Ratnagiri, Raigad, Sindhudurg, Satara",
        "rainfall_mm": 485.0,
        "severity": "CRITICAL EMERGENCY",
        "summary": "Vashishti and Savitri rivers overflowed within hours due to intense torrential downpour and high tide, submerging Chiplun town center and Mahad lowlands."
    },
    {
        "year": "2023",
        "event_name": "Vidarbha River Basin Surges",
        "affected_districts": "Nagpur, Chandrapur, Gadchiroli, Bhandara",
        "rainfall_mm": 210.0,
        "severity": "HIGH SEVERITY",
        "summary": "Heavy rainfall in catchment areas of Wainganga, Wardha, and Godavari tributaries triggered floodgate releases at Gosikhurd dam, submerging agricultural belts."
    },
    {
        "year": "2024",
        "event_name": "Pune & Thane Monsoon Waterlogging",
        "affected_districts": "Pune, Thane, Raigad, Palghar",
        "rainfall_mm": 240.0,
        "severity": "HIGH SEVERITY",
        "summary": "Intense spells caused Khadakwasla dam discharge leading to Mutha river overflow in Pune, alongside severe urban low-lying waterlogging in Thane and Ulhasnagar."
    }
]
def load_flood_history():
    """Historical events come ONLY from data/raw/flood_history.csv."""
    if not os.path.exists(FLOOD_HISTORY_FILE):
        return pd.DataFrame()
    df = pd.read_csv(FLOOD_HISTORY_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    df["Start Date Parsed"] = pd.to_datetime(df["Start Date"], dayfirst=True, errors="coerce")
    df["End Date Parsed"] = pd.to_datetime(df["End Date"], dayfirst=True, errors="coerce")
    df["Year"] = df["Start Date Parsed"].dt.year
    return df


HISTORY_DF = load_flood_history()


def historical_years():
    if HISTORY_DF.empty:
        return []
    return sorted(int(y) for y in HISTORY_DF["Year"].dropna().unique())


def district_names():
    names = set(DISTRICT_COORDINATES.keys())
    if not HISTORY_DF.empty and "Districts" in HISTORY_DF:
        for raw in HISTORY_DF["Districts"].dropna():
            for item in str(raw).split(","):
                item = item.strip()
                if item and item.lower() not in {"parts of maharashtra", "gadchiroli yavotmal"}:
                    names.add(item)
    # Keep names that the project data can identify; aliases remain searchable.
    return sorted(names)


@lru_cache(maxsize=128)
def geocode_maharashtra(location):
    """Resolve missing district coordinates through Open-Meteo only when needed for live/map rendering."""
    if location in DISTRICT_COORDINATES:
        c = DISTRICT_COORDINATES[location]
        return {"success": True, "latitude": c["lat"], "longitude": c["lon"], "name": location}
    aliases = {"Raigarh": "Raigad", "Aurangabad": "Chhatrapati Sambhajinagar", "Mumbai Suburban": "Mumbai"}
    lookup = aliases.get(location, location)
    if lookup in DISTRICT_COORDINATES:
        c = DISTRICT_COORDINATES[lookup]
        return {"success": True, "latitude": c["lat"], "longitude": c["lon"], "name": location}
    try:
        r = requests.get(
            GEOCODING_API_URL,
            params={"name": lookup, "count": 10, "language": "en", "format": "json", "countryCode": "IN"},
            timeout=API_TIMEOUT,
        )
        r.raise_for_status()
        for p in r.json().get("results", []):
            if str(p.get("country", "")).lower() == "india" and str(p.get("admin1", "")).lower() == "maharashtra":
                return {"success": True, "latitude": p["latitude"], "longitude": p["longitude"], "name": location}
    except requests.RequestException:
        pass
    return {"success": False, "name": location}


def weather_code_label(code):
    code = int(code or 0)
    if code in (0,): return "Clear"
    if code in (1, 2, 3): return "Cloudy"
    if code in (45, 48): return "Fog"
    if code in (51, 53, 55, 56, 57): return "Drizzle"
    if code in (61, 63, 65, 66, 67, 80, 81, 82): return "Rain"
    if code in (71, 73, 75, 77, 85, 86): return "Snow"
    if code in (95, 96, 99): return "Thunderstorm"
    return "Cloudy"


def fetch_open_meteo(location, history_days=7):
    geo = geocode_maharashtra(location)
    if not geo.get("success"):
        return {"success": False, "error": f"Could not locate '{location}' in Maharashtra."}

    params = {
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,showers,wind_speed_10m,weather_code",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m",
        "past_days": history_days,
        "forecast_days": 1,
        "timezone": TIMEZONE,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    try:
        r = requests.get(WEATHER_API_URL, params=params, timeout=API_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        current = payload.get("current", {})
        return {"success": True, "location": geo, "current": current, "hourly": payload.get("hourly", {}), "source": "Open-Meteo live"}
    except requests.RequestException as exc:
        return {"success": False, "error": f"Live weather service unavailable: {exc}"}


def live_weather(location):
    result = fetch_open_meteo(location, 7)
    if not result["success"]:
        # Fallback is only the project's own bundled live_weather_data.csv; no fabricated values.
        if os.path.exists(LIVE_FILE):
            try:
                df = pd.read_csv(LIVE_FILE)
                rows = df[df["location"].astype(str).str.lower() == location.lower()]
                if not rows.empty:
                    row = rows.iloc[-1]
                    return {
                        "success": True, "location": location, "temperature": float(row["temperature_c"]),
                        "rainfall": float(row["rainfall_mm"]), "humidity": float(row["humidity_percent"]),
                        "wind_speed": float(row["wind_speed_kmh"]), "condition": "Live data file",
                        "condition_type": "cloudy", "time": str(row["time"]), "latitude": float(row["latitude"]),
                        "longitude": float(row["longitude"]), "source": "data/live_weather_data.csv (fallback)",
                    }
            except Exception:
                pass
        return result

    c = result["current"]
    condition = weather_code_label(c.get("weather_code"))
    return {
        "success": True,
        "location": location,
        "temperature": round(float(c.get("temperature_2m", 0)), 1),
        "rainfall": round(float(c.get("precipitation", 0)), 2),
        "rain": round(float(c.get("rain", 0)), 2),
        "showers": round(float(c.get("showers", 0)), 2),
        "humidity": round(float(c.get("relative_humidity_2m", 0)), 1),
        "wind_speed": round(float(c.get("wind_speed_10m", 0)), 1),
        "condition": condition,
        "condition_type": condition.lower(),
        "time": c.get("time"),
        "latitude": result["location"]["latitude"],
        "longitude": result["location"]["longitude"],
        "source": result["source"],
    }


def last_7_days(location):
    result = fetch_open_meteo(location, 7)
    if not result["success"]:
        # Project's bundled weather.csv is used only as a data fallback.
        if os.path.exists(WEATHER_FILE):
            df = pd.read_csv(WEATHER_FILE)
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df[df["location"].astype(str).str.lower() == location.lower()].dropna(subset=["date"]).sort_values("date").tail(7)
            if not df.empty:
                return {"success": True, "dates": df["date"].dt.strftime("%d %b").tolist(), "temperature": df["temperature_c"].astype(float).round(1).tolist(), "rainfall": [0.0] * len(df), "source": "data/raw/weather.csv (rainfall unavailable)"}
        return result

    hourly = result["hourly"]
    times = pd.to_datetime(hourly.get("time", []))
    frame = pd.DataFrame({
        "time": times,
        "temperature": hourly.get("temperature_2m", []),
        "rainfall": hourly.get("precipitation", []),
    }).dropna(subset=["time"])
    frame["date"] = frame["time"].dt.date
    daily = frame.groupby("date", as_index=False).agg(temperature=("temperature", "mean"), rainfall=("rainfall", "sum")).tail(7)
    return {"success": True, "dates": [d.strftime("%d %b") for d in daily["date"]], "temperature": daily["temperature"].round(1).tolist(), "rainfall": daily["rainfall"].round(2).tolist(), "source": result["source"]}


def last_24_hours(location):
    result = fetch_open_meteo(location, 1)
    if not result.get("success"):
        return result
    hourly = result.get("hourly", {})
    times = pd.to_datetime(hourly.get("time", []))
    frame = pd.DataFrame({
        "time": times,
        "rainfall": hourly.get("precipitation", []),
    }).dropna(subset=["time"])
    if frame.empty:
        return {"success": False, "error": "Hourly live weather data unavailable"}
    frame = frame.tail(24).copy()
    current = result.get("current", {})
    temperature = float(current.get("temperature", 25) or 25)
    humidity = float(current.get("humidity", 70) or 70)
    wind = float(current.get("wind_speed", 10) or 10)
    risks = []
    for rain in frame["rainfall"].fillna(0).astype(float).tolist():
        try:
            risks.append(float(predict_flood_risk(rain, temperature, humidity, wind).get("risk_score", 0)))
        except Exception:
            risks.append(0.0)
    return {
        "success": True,
        "hours": frame["time"].dt.strftime("%H:%M").tolist(),
        "rainfall": frame["rainfall"].fillna(0).astype(float).round(2).tolist(),
        "flood_risk": [round(v, 2) for v in risks],
        "source": result.get("source", "Open-Meteo")
    }


def risk_for_weather(w):
    p = predict_flood_risk(w["rainfall"], w["temperature"], w["humidity"], w["wind_speed"])
    p.update({
        "location": w["location"],
        "risk_percentage": p["risk_score"],
        "alert_class": p["risk_level"].lower(),
        "warning_message": f"{p['risk_level']} flood risk based on current rainfall, humidity, temperature and wind.",
        "action_guideline": warning_text(p["risk_level"]),
    })
    return p


def warning_text(level):
    return {
        "HIGH": "Prepare for possible inundation. Avoid riverbanks and low-lying roads and follow official local advisories.",
        "MEDIUM": "Monitor rainfall and drainage closely. Avoid unnecessary travel through low-lying or waterlogged areas.",
        "LOW": "No elevated flood signal from the current weather inputs. Continue normal monsoon precautions.",
    }.get(level, "Continue monitoring current weather and official advisories.")


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS weather_records (id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, temperature REAL, rainfall REAL, humidity REAL, wind_speed REAL, weather_condition TEXT, timestamp TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS flood_predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, risk_percentage REAL, risk_level TEXT, timestamp TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, alert_level TEXT, alert_message TEXT, timestamp TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS system_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    if cur.execute("SELECT COUNT(*) FROM system_settings").fetchone()[0] == 0:
        cur.executemany("INSERT INTO system_settings(key,value) VALUES(?,?)", [("default_location", "Mumbai"), ("temp_unit", "celsius"), ("warning_notifications", "true"), ("refresh_interval", "60")])
    conn.commit(); conn.close()


init_db()


def get_setting(key, default=""):
    conn = get_db(); row = conn.execute("SELECT value FROM system_settings WHERE key=?", (key,)).fetchone(); conn.close()
    return row["value"] if row else default


def save_live(w, p):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO weather_records(location,temperature,rainfall,humidity,wind_speed,weather_condition,timestamp) VALUES(?,?,?,?,?,?,?)", (w["location"], w["temperature"], w["rainfall"], w["humidity"], w["wind_speed"], w["condition"], now))
    cur.execute("INSERT INTO flood_predictions(location,risk_percentage,risk_level,timestamp) VALUES(?,?,?,?)", (w["location"], p["risk_percentage"], p["risk_level"], now))
    if p["risk_percentage"] >= 40:
        cur.execute("INSERT INTO alerts(location,alert_level,alert_message,timestamp) VALUES(?,?,?,?)", (w["location"], p["risk_level"], p["warning_message"], now))
    conn.commit(); conn.close()


def history_records(year=None):
    if HISTORY_DF.empty: return []
    df = HISTORY_DF.copy()
    if year not in (None, "", "all"):
        try: df = df[df["Year"] == int(year)]
        except ValueError: pass
    out=[]
    for idx, r in df.iterrows():
        out.append({
            "id": int(idx), "year": int(r["Year"]) if pd.notna(r["Year"]) else None,
            "start_date": clean_text(r["Start Date"]), "end_date": clean_text(r["End Date"]),
            "duration_days": clean_text(r["Duration(Days) "]) if "Duration(Days) " in r else clean_text(r.get("Duration(Days)", "")),
            "main_cause": clean_text(r.get("Main Cause", "")), "districts": clean_text(r.get("Districts", "")),
            "state": clean_text(r.get("State", "")), "fatalities": clean_text(r.get("Human fatality", "")),
            "human_fatality": clean_text(r.get("Human fatality", "")),
            "injured": clean_text(r.get("Human injured", "")), "displaced": clean_text(r.get("Human Displaced", "")),
            "description": clean_text(r.get("Description of Casualties/injured", "")), "damage_extent": clean_text(r.get("Extent of damage ", r.get("Extent of damage", ""))),
        })
    return out


@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        initial_location="Ratnagiri"
    )

@app.route("/weather")
def weather_view():
    loc=request.args.get("location", get_setting("default_location", "Mumbai"))
    return render_template("weather.html", active_page="weather", initial_location=loc, districts=district_names())

@app.route("/gis")
def gis_view():
    return render_template("gis.html", active_page="gis", districts=district_names(), years=historical_years())

@app.route("/simulator")
def simulator_view():
    loc=request.args.get("location", get_setting("default_location", "Mumbai"))
    return render_template("simulator.html", active_page="simulator", initial_location=loc, districts=district_names())

@app.route("/warnings")
def warnings_view():
    loc=request.args.get("location", get_setting("default_location", "Mumbai"))
    return render_template("warnings.html", active_page="warnings", initial_location=loc, districts=district_names())

@app.route("/history")
@app.route("/previous_floods")
def history_view():
    return render_template("previous_floods.html", active_page="history", districts=district_names(), years=historical_years())

@app.route("/settings")
def settings_view():
    settings={k:get_setting(k) for k in ["default_location","temp_unit","warning_notifications","refresh_interval"]}
    return render_template("settings.html", active_page="settings", settings=settings, districts=district_names())


@app.route("/api/dashboard-data")
def api_dashboard_data():
    loc=request.args.get("location", "Mumbai").strip()
    w=live_weather(loc)
    if not w.get("success"): return jsonify({"status":"error","error":w.get("error","Weather unavailable")}), 503
    p=risk_for_weather(w); save_live(w,p)
    series=last_24_hours(loc)
    return jsonify({"status":"success","weather":w,"prediction":p,"series":series})

@app.route("/api/weather/live")
def api_live_weather():
    loc=request.args.get("location", "Mumbai").strip()
    w=live_weather(loc)
    if not w.get("success"): return jsonify({"status":"error","error":w.get("error","Weather unavailable")}),503
    p=risk_for_weather(w)
    return jsonify({"status":"success","data":w,"prediction":p,"location":w["location"],**w})

@app.route("/api/weather/series")
def api_weather_series():
    loc=request.args.get("location", "Mumbai").strip()
    s=last_7_days(loc)
    if not s.get("success"): return jsonify({"status":"error","error":s.get("error")}),503
    return jsonify({"status":"success","location":loc,**s})

@app.route("/api/predict")
def api_predict():
    loc=request.args.get("location", "Mumbai").strip(); w=live_weather(loc)
    if not w.get("success"): return jsonify({"status":"error","error":w.get("error")}),503
    return jsonify({"status":"success","prediction":risk_for_weather(w),"weather":w})

@app.route("/api/simulate", methods=["POST","GET"])
def api_simulate():
    data=request.get_json(silent=True) or request.args
    loc=str(data.get("location","Mumbai"))
    live=live_weather(loc)
    if not live.get("success"): return jsonify({"status":"error","error":live.get("error")}),503
    # Start simulator controls at the CURRENT live values; user can then change them.
    rainfall=float(data.get("rainfall", live["rainfall"])); temperature=float(data.get("temperature", live["temperature"]))
    humidity=float(data.get("humidity", live["humidity"])); wind=float(data.get("wind_speed", live["wind_speed"]))
    p=predict_flood_risk(rainfall,temperature,humidity,wind)
    result={"location":loc,"rainfall":rainfall,"temperature":temperature,"humidity":humidity,"wind_speed":wind,"risk_percentage":p["risk_score"],"risk_level":p["risk_level"],"alert_class":p["risk_level"].lower(),"action_guideline":warning_text(p["risk_level"])}
    higher_rain=rainfall*1.4
    hp=predict_flood_risk(higher_rain,temperature,humidity,wind)
    return jsonify({"status":"success","live":live,"simulation":result,"higher_scenario":{"risk_percentage":hp["risk_score"],"risk_level":hp["risk_level"]},"sensitivity_insight":f"A 40% rainfall increase from {rainfall:.1f} to {higher_rain:.1f} mm changes the model score from {p['risk_score']}% to {hp['risk_score']}%."})

@app.route("/api/gis/data")
def api_gis_data():
    # Current live layer: only districts that can be resolved from the project configuration/data.
    rows=[]
    # Live map uses the coordinates already present in the supplied project configuration.
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(live_weather,d):d for d in DISTRICT_COORDINATES.keys()}
        for future in as_completed(futures):
            d=futures[future]
            try:
                w=future.result()
                if w.get("success"):
                    p=risk_for_weather(w); rows.append({"district":d,"lat":w["latitude"],"lon":w["longitude"],"temperature":w["temperature"],"rainfall":w["rainfall"],"humidity":w["humidity"],"wind_speed":w["wind_speed"],"risk_percentage":p["risk_percentage"],"risk_level":p["risk_level"]})
            except Exception:
                continue
    rows.sort(key=lambda x:x["district"])
    return jsonify({"status":"success","districts":rows})

@app.route("/api/gis/historical-floods")
def api_historical_floods():
    year=request.args.get("year","all")
    records=history_records(year)
    floods=[]
    jobs=[]
    for r in records:
        for district in [x.strip() for x in r["districts"].split(",") if x.strip()]:
            if district.lower() in {"parts of maharashtra","gadchiroli yavotmal"}: continue
            jobs.append((r,district))
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(geocode_maharashtra,district):(r,district) for r,district in jobs}
        for future in as_completed(futures):
            r,district=futures[future]
            try: geo=future.result()
            except Exception: continue
            if not geo.get("success"): continue
            floods.append({"id":f"{r['id']}-{district}","year":r["year"],"district":district,"lat":geo["latitude"],"lon":geo["longitude"],"start_date":r["start_date"],"end_date":r["end_date"],"main_cause":r["main_cause"],"fatalities":r["fatalities"] or "0","description":r["description"] or r["damage_extent"],"damage":r["damage_extent"]})
    floods.sort(key=lambda x:(x["year"] or 0,x["district"]))
    return jsonify({"status":"success","has_data":bool(floods),"flood_incidents":floods,"count":len(floods),"year":year,"available_years":historical_years()})

@app.route("/api/gis/safe-routes")
def api_safe_routes():
    """District-level safe evacuation corridors using only project coordinates + live risk.
    No external road network is used because the supplied project contains no road-network dataset.
    """
    origin = request.args.get("location", "Mumbai").strip()
    match = next((d for d in DISTRICT_COORDINATES if d.lower() == origin.lower()), None)
    origin = match or origin
    if origin not in DISTRICT_COORDINATES:
        return jsonify({"status":"error","error":"District is not available in the supplied project coordinates."}), 400
    origin_w = live_weather(origin)
    if not origin_w.get("success"):
        return jsonify({"status":"error","error":origin_w.get("error","Live weather unavailable")}), 503
    import math
    candidates=[]
    lat1, lon1 = DISTRICT_COORDINATES[origin]["lat"], DISTRICT_COORDINATES[origin]["lon"]
    for district, coords in DISTRICT_COORDINATES.items():
        if district == origin: continue
        w=live_weather(district)
        if not w.get("success"): continue
        p=risk_for_weather(w)
        lat2, lon2 = coords["lat"], coords["lon"]
        km=math.sqrt(((lat2-lat1)*111.0)**2 + ((lon2-lon1)*104.0*math.cos(math.radians((lat1+lat2)/2)))**2)
        score=(p["risk_percentage"]*0.72) + min(km,300)*0.08
        candidates.append({"district":district,"lat":lat2,"lon":lon2,"distance_km":round(km,1),"risk_percentage":p["risk_percentage"],"risk_level":p["risk_level"],"score":round(score,2),"weather":w["condition"]})
    candidates.sort(key=lambda x:x["score"])
    routes=[]
    for i,c in enumerate(candidates[:3],1):
        routes.append({"id":i,"from":origin,"to":c["district"],"points":[[origin_w["latitude"],origin_w["longitude"]],[c["lat"],c["lon"]]],"distance_km":c["distance_km"],"destination_risk":c["risk_percentage"],"destination_risk_level":c["risk_level"],"destination_weather":c["weather"],"advisory":"District-level evacuation corridor. Confirm local road and authority conditions before travel."})
    return jsonify({"status":"success","origin":origin,"origin_risk":risk_for_weather(origin_w),"routes":routes,"note":"Corridors use only project district coordinates plus live weather/risk; they are not turn-by-turn road directions."})

@app.route("/api/warnings/active")
def api_active_warnings():
    loc=request.args.get("location","Mumbai")
    w=live_weather(loc)
    if not w.get("success"): return jsonify({"status":"error","error":w.get("error")}),503
    p=risk_for_weather(w)
    warnings=[]
    if p["risk_percentage"] >= 40:
        warnings.append({"location":loc,"risk_level":p["risk_level"],"risk_percentage":p["risk_percentage"],"alert_class":p["alert_class"],"rainfall_mm":w["rainfall"],"temperature":w["temperature"],"humidity":w["humidity"],"wind_speed":w["wind_speed"],"action_guideline":p["action_guideline"],"river_name":"Weather-driven catchment signal"})
    # Always provide a useful early-warning status for the selected district.
    warnings.append({"location":loc,"risk_level":p["risk_level"],"risk_percentage":p["risk_percentage"],"alert_class":p["alert_class"],"rainfall_mm":w["rainfall"],"temperature":w["temperature"],"humidity":w["humidity"],"wind_speed":w["wind_speed"],"action_guideline":warning_text(p["risk_level"]),"river_name":"Live meteorological indicator"})
    return jsonify({"status":"success","warnings":warnings,"updated_at":w.get("time"),"source":w.get("source")})

@app.route("/api/history/records")
def api_history_records():
    year=request.args.get("year")
    return jsonify({"status":"success","records":history_records(year),"available_years":historical_years()})

@app.route("/api/settings", methods=["GET","POST"])
def api_settings_handler():
    conn=get_db(); cur=conn.cursor()
    if request.method=="POST":
        data=request.get_json(silent=True) or {}
        for key in ["default_location","temp_unit","warning_notifications","refresh_interval"]:
            if key in data: cur.execute("INSERT OR REPLACE INTO system_settings(key,value) VALUES(?,?)",(key,str(data[key])))
        conn.commit(); conn.close(); return jsonify({"status":"success"})
    rows=cur.execute("SELECT key,value FROM system_settings").fetchall(); conn.close()
    return jsonify({"status":"success","settings":{r["key"]:r["value"] for r in rows}})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",3000)), debug=False)
