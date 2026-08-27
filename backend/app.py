import os
import sqlite3
import time
from datetime import datetime, timedelta
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for


# Initialize Flask app
app = Flask(__name__, template_folder='frontend', static_folder='static')
app.config['SECRET_KEY'] = 'maha-flood-ai-secret-2026'

DB_FILE = os.path.join(os.path.dirname(__file__), 'database.db')

HISTORICAL_FLOOD_EVENTS = [
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

def get_districts_full_status():
    districts_data = []
    weather_list = get_all_districts_weather()
    for w in weather_list:
        district = w["location"]
        geo = DISTRICT_COORDINATES.get(district, {"lat": w["coordinates"]["lat"], "lon": w["coordinates"]["lon"], "elevation_m": 50})
        pred = flood_model.predict(
            rainfall_mm=w["rainfall"],
            river_level_m=w["river_water_level"],
            soil_moisture_pct=w["soil_moisture"],
            temperature_c=w["temperature"],
            humidity_pct=w["humidity"],
            location=district
        )
        districts_data.append({
            "district": district,
            "lat": geo["lat"],
            "lon": geo["lon"],
            "elevation": geo.get("elevation_m", 50),
            "weather_condition": w["weather_condition"],
            "weather_condition_desc": w.get("weather_condition_desc", "Live Telemetry"),
            "temperature": w["temperature"],
            "rainfall": w["rainfall"],
            "humidity": w["humidity"],
            "wind_speed": w["wind_speed"],
            "soil_moisture": w["soil_moisture"],
            "river_level": w["river_water_level"],
            "danger_level": pred["danger_river_level_m"],
            "risk_percentage": pred["risk_percentage"],
            "risk_level": pred["risk_level"],
            "alert_class": pred["alert_class"],
            "warning_message": pred["warning_message"],
            "action_guideline": pred.get("action_guideline", "Monitor river levels and heed local authority advisories."),
            "major_rivers": pred["major_rivers"],
            "affected_zones": pred["affected_zones"]
        })
    return districts_data

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database tables and seeds baseline historical data."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. weather_records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            temperature REAL,
            rainfall REAL,
            humidity REAL,
            wind_speed REAL,
            weather_condition TEXT,
            timestamp TEXT NOT NULL
        )
    ''')

    # 2. flood_predictions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flood_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            risk_percentage REAL,
            risk_level TEXT,
            timestamp TEXT NOT NULL
        )
    ''')

    # 3. alerts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            alert_level TEXT,
            alert_message TEXT,
            timestamp TEXT NOT NULL
        )
    ''')

    # 4. system_settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Seed default settings if empty
    cursor.execute('SELECT COUNT(*) FROM system_settings')
    if cursor.fetchone()[0] == 0:
        defaults = [
            ('default_location', 'Mumbai'),
            ('temp_unit', 'celsius'),
            ('warning_notifications', 'true'),
            ('refresh_interval', '60')
        ]
        cursor.executemany('INSERT INTO system_settings (key, value) VALUES (?, ?)', defaults)

    # Seed historical weather & flood records if empty
    cursor.execute('SELECT COUNT(*) FROM weather_records')
    if cursor.fetchone()[0] == 0:
        seed_locations = [
            ("Mumbai", 29.4, 185.0, 92.0, 32.0, "Rain", "HIGH RISK", 78.5),
            ("Kolhapur", 26.2, 210.0, 95.0, 24.0, "Rain", "CRITICAL FLOOD WARNING", 89.2),
            ("Sangli", 27.5, 140.0, 88.0, 18.0, "Rain", "HIGH RISK", 74.0),
            ("Ratnagiri", 28.0, 240.0, 94.0, 38.0, "Storm", "CRITICAL FLOOD WARNING", 92.8),
            ("Raigad", 27.8, 195.0, 91.0, 30.0, "Rain", "HIGH RISK", 81.0),
            ("Pune", 25.4, 65.0, 78.0, 16.0, "Rain", "MEDIUM RISK", 48.0),
            ("Nashik", 28.1, 45.0, 72.0, 14.0, "Cloudy", "MEDIUM RISK", 38.5),
            ("Nagpur", 32.5, 12.0, 60.0, 10.0, "Clear", "LOW RISK", 18.0),
            ("Thane", 29.0, 160.0, 89.0, 28.0, "Rain", "HIGH RISK", 76.0),
            ("Chhatrapati Sambhajinagar", 31.0, 8.0, 58.0, 12.0, "Cloudy", "LOW RISK", 22.0),
            ("Gadchiroli", 28.9, 115.0, 86.0, 15.0, "Rain", "MEDIUM RISK", 58.0),
            ("Sindhudurg", 28.2, 175.0, 90.0, 25.0, "Rain", "HIGH RISK", 72.5)
        ]
        
        now = datetime.now()
        for idx, item in enumerate(seed_locations):
            loc, temp, rain, hum, wind, cond, r_lvl, r_pct = item
            record_time = (now - timedelta(hours=(idx * 4 + 2))).strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO weather_records (location, temperature, rainfall, humidity, wind_speed, weather_condition, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (loc, temp, rain, hum, wind, cond, record_time))

            cursor.execute('''
                INSERT INTO flood_predictions (location, risk_percentage, risk_level, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (loc, r_pct, r_lvl, record_time))

            if r_pct >= 60.0:
                alert_msg = f"Heavy surge recorded in {loc} river basin. Caution advised in flood prone zones."
                cursor.execute('''
                    INSERT INTO alerts (location, alert_level, alert_message, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (loc, r_lvl, alert_msg, record_time))

    conn.commit()
    conn.close()

# Initialize Database immediately
init_db()

# --- Helper functions ---

def get_setting(key: str, default_val: str = "") -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM system_settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else default_val

def save_telemetry_and_prediction(weather_data: dict, prediction_data: dict):
    """Saves live weather and AI prediction to SQLite database."""
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO weather_records (location, temperature, rainfall, humidity, wind_speed, weather_condition, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        weather_data["location"],
        weather_data["temperature"],
        weather_data["rainfall"],
        weather_data["humidity"],
        weather_data["wind_speed"],
        weather_data["weather_condition"],
        now_str
    ))

    cursor.execute('''
        INSERT INTO flood_predictions (location, risk_percentage, risk_level, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (
        prediction_data["location"],
        prediction_data["risk_percentage"],
        prediction_data["risk_level"],
        now_str
    ))

    # Add to alerts table if risk is elevated
    if prediction_data["risk_percentage"] >= 30.0:
        cursor.execute('''
            INSERT INTO alerts (location, alert_level, alert_message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            prediction_data["location"],
            prediction_data["risk_level"],
            prediction_data["warning_message"],
            now_str
        ))

    conn.commit()
    conn.close()

# --- Page Routes ---

@app.route('/')
def dashboard_view():
    default_loc = get_setting('default_location', 'Mumbai')
    loc = request.args.get('location', default_loc).strip()
    return render_template('dashboard.html', active_page='dashboard', initial_location=loc, districts=list(DISTRICT_COORDINATES.keys()))

@app.route('/weather')
def weather_view():
    default_loc = get_setting('default_location', 'Mumbai')
    loc = request.args.get('location', default_loc).strip()
    weather_data = get_live_weather(loc)
    forecast_data = get_7day_forecast(loc)
    return render_template(
        'weather.html',
        active_page='weather',
        weather=weather_data,
        forecast=forecast_data,
        initial_location=loc,
        districts=list(DISTRICT_COORDINATES.keys())
    )

@app.route('/gis')
def gis_view():
    districts_data = get_districts_full_status()
    return render_template(
        'gis.html',
        active_page='gis',
        districts_data=districts_data,
        districts=list(DISTRICT_COORDINATES.keys())
    )

@app.route('/simulator')
def simulator_view():
    default_loc = get_setting('default_location', 'Mumbai')
    loc = request.args.get('location', default_loc).strip()
    return render_template('simulator.html', active_page='simulator', initial_location=loc, districts=list(DISTRICT_COORDINATES.keys()))

@app.route('/warnings')
def warnings_view():
    districts_data = get_districts_full_status()
    return render_template(
        'warnings.html',
        active_page='warnings',
        districts_data=districts_data,
        districts=list(DISTRICT_COORDINATES.keys())
    )

@app.route('/history')
def history_view():
    return render_template(
        'previous_floods.html',
        active_page='history',
        history=HISTORICAL_FLOOD_EVENTS,
        districts=list(DISTRICT_COORDINATES.keys())
    )

@app.route('/settings')
def settings_view():
    settings = {
        'default_location': get_setting('default_location', 'Mumbai'),
        'temp_unit': get_setting('temp_unit', 'celsius'),
        'warning_notifications': get_setting('warning_notifications', 'true'),
        'refresh_interval': get_setting('refresh_interval', '60')
    }
    return render_template('settings.html', active_page='settings', settings=settings, districts=list(DISTRICT_COORDINATES.keys()))

# --- API Endpoints ---

@app.route('/api/dashboard-data')
def api_dashboard_data():
    loc = request.args.get('location', 'Mumbai').strip()
    weather = get_live_weather(loc)
    prediction = flood_model.predict(
        rainfall_mm=weather["rainfall"],
        river_level_m=weather["river_water_level"],
        soil_moisture_pct=weather["soil_moisture"],
        temperature_c=weather["temperature"],
        humidity_pct=weather["humidity"],
        location=weather["location"]
    )
    
    # Save to SQLite
    save_telemetry_and_prediction(weather, prediction)

    return jsonify({
        "status": "success",
        "weather": weather,
        "prediction": prediction,
        "bg_image": f"/static/images/weather/{weather['weather_condition'].lower()}.jpg"
    })

@app.route('/api/weather/live')
def api_live_weather():
    loc = request.args.get('location', 'Mumbai').strip()
    weather = get_live_weather(loc)
    return jsonify({
        "status": "success",
        "data": weather
    })

@app.route('/api/predict')
def api_predict():
    loc = request.args.get('location', 'Mumbai').strip()
    rainfall = float(request.args.get('rainfall', 0))
    river_level = float(request.args.get('river_level', 2.0))
    soil_moisture = float(request.args.get('soil_moisture', 50))
    
    prediction = flood_model.predict(
        rainfall_mm=rainfall,
        river_level_m=river_level,
        soil_moisture_pct=soil_moisture,
        location=loc
    )
    return jsonify({
        "status": "success",
        "data": prediction
    })

@app.route('/api/simulate', methods=['POST', 'GET'])
def api_simulate():
    if request.method == 'POST':
        data = request.get_json() or {}
        loc = data.get('location', 'Mumbai')
        rainfall = float(data.get('rainfall', 50.0))
        river_level = float(data.get('river_level', 3.5))
        soil_moisture = float(data.get('soil_moisture', 60.0))
    else:
        loc = request.args.get('location', 'Mumbai')
        rainfall = float(request.args.get('rainfall', 50.0))
        river_level = float(request.args.get('river_level', 3.5))
        soil_moisture = float(request.args.get('soil_moisture', 60.0))

    prediction = flood_model.predict(
        rainfall_mm=rainfall,
        river_level_m=river_level,
        soil_moisture_pct=soil_moisture,
        location=loc
    )
    
    # Calculate what-if dynamic sensitivity summary
    plus_40_rain = rainfall * 1.4 + 15
    pred_plus = flood_model.predict(
        rainfall_mm=plus_40_rain,
        river_level_m=river_level * 1.25,
        soil_moisture_pct=min(100.0, soil_moisture * 1.2),
        location=loc
    )

    insight = (
        f"If rainfall increases by 40% (to {plus_40_rain:.1f} mm), "
        f"flood probability increases from {prediction['risk_percentage']}% to {pred_plus['risk_percentage']}%."
    )

    return jsonify({
        "status": "success",
        "simulation": prediction,
        "sensitivity_insight": insight,
        "higher_scenario": pred_plus
    })

@app.route('/api/gis/data')
def api_gis_data():
    """Returns GIS district status dataset for interactive Maharashtra map"""
    districts_data = get_districts_full_status()
    return jsonify({
        "status": "success",
        "districts": districts_data
    })


@app.route('/api/warnings/active')
def api_active_warnings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, location, alert_level, alert_message, timestamp 
        FROM alerts 
        ORDER BY id DESC LIMIT 25
    ''')
    rows = cursor.fetchall()
    conn.close()

    alerts_list = [dict(row) for row in rows]
    return jsonify({
        "status": "success",
        "alerts": alerts_list
    })

@app.route('/api/history/records')
def api_history_records():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT w.id, w.location, w.temperature, w.rainfall, w.humidity, w.wind_speed, 
               w.weather_condition, w.timestamp, p.risk_percentage, p.risk_level
        FROM weather_records w
        LEFT JOIN flood_predictions p ON w.location = p.location AND w.timestamp = p.timestamp
        ORDER BY w.id DESC LIMIT 40
    ''')
    rows = cursor.fetchall()
    conn.close()

    records = [dict(row) for row in rows]
    return jsonify({
        "status": "success",
        "records": records
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings_handler():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.get_json() or {}
        for key in ['default_location', 'temp_unit', 'warning_notifications', 'refresh_interval']:
            if key in data:
                cursor.execute('INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)', (key, str(data[key])))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Settings updated successfully"})
    else:
        cursor.execute('SELECT key, value FROM system_settings')
        rows = cursor.fetchall()
        conn.close()
        settings = {row['key']: row['value'] for row in rows}
        return jsonify({"status": "success", "settings": settings})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"==================================================")
    print(f" Maha Flood AI - Server running on http://0.0.0.0:{port}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=False)
