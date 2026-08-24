from flask import Flask, render_template, jsonify
from flask_cors import CORS
import os

# --------------------------------------------------
# FRONTEND PATH
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_FOLDER = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend")
)


# --------------------------------------------------
# FLASK
# --------------------------------------------------

app = Flask(
    __name__,
    template_folder=FRONTEND_FOLDER
)

app.secret_key = "foresightx-secret-key"

CORS(app)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def home():

    return render_template("dashboard.html")


@app.route("/dashboard")
def dashboard():

    return render_template("dashboard.html")


# --------------------------------------------------
# MAP
# --------------------------------------------------

@app.route("/map")
def flood_map():

    return render_template("map.html")


# --------------------------------------------------
# STATUS
# --------------------------------------------------

@app.route("/status")
def status():

    return jsonify({
        "message": "Backend is running!",
        "status": "online"
    })


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )