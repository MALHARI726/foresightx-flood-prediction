from flask import Blueprint, request, jsonify, send_file

from api_service import (
    get_location_weather,
    save_weather_to_csv
)

from prediction import predict_flood_risk

routes = Blueprint("routes", __name__)


@routes.route("/api/flood-risk", methods=["GET"])
def get_flood_risk():

    location = request.args.get("location")

    if not location:
        return jsonify({
            "success": False,
            "error": "Please enter a Maharashtra location."
        }), 400

    weather = get_location_weather(location)

    if not weather["success"]:
        return jsonify({
            "success": False,
            "error": weather["error"]
        }), 400

    current = weather["current"]

    prediction = predict_flood_risk(
        rainfall=current["precipitation"],
        temperature=current["temperature"],
        humidity=current["humidity"],
        wind_speed=current["wind_speed"]
    )

    save_weather_to_csv(weather, prediction)

    return jsonify({
        "success": True,
        "location": location,
        "weather": {
            "rainfall": current["precipitation"],
            "temperature": current["temperature"],
            "humidity": current["humidity"],
            "wind_speed": current["wind_speed"]
        },
        "prediction": prediction
    })


@routes.route("/download/flood-risk", methods=["GET"])
def download_flood_risk():

    location = request.args.get("location")

    if not location:
        return jsonify({
            "success": False,
            "error": "Please provide a location."
        }), 400

    weather = get_location_weather(location)

    if not weather["success"]:
        return jsonify({
            "success": False,
            "error": weather["error"]
        }), 400

    current = weather["current"]

    prediction = predict_flood_risk(
        rainfall=current["precipitation"],
        temperature=current["temperature"],
        humidity=current["humidity"],
        wind_speed=current["wind_speed"]
    )

    csv_file = save_weather_to_csv(
        weather,
        prediction
    )

    return send_file(
        csv_file,
        mimetype="text/csv",
        as_attachment=True,
        download_name="flood_risk_data.csv"
    )