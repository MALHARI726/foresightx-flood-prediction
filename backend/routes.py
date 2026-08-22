from flask import Blueprint, request, send_file

from api_service import (
    get_location_weather,
    save_weather_to_csv
)

from prediction import (
    predict_flood_risk
)


# =========================================================
# CREATE BLUEPRINT
# =========================================================

routes = Blueprint(
    "routes",
    __name__
)


# =========================================================
# FLOOD RISK API
# =========================================================

@routes.route(
    "/api/flood-risk",
    methods=["GET"]
)
def get_flood_risk():

    # -----------------------------------------------------
    # 1. GET LOCATION FROM USER
    # -----------------------------------------------------

    location = request.args.get(
        "location"
    )

    if not location:

        return (
            "Please enter a Maharashtra location.",
            400
        )

    location = location.strip()

    if not location:

        return (
            "Location cannot be empty.",
            400
        )


    # -----------------------------------------------------
    # 2. GET LIVE WEATHER
    # -----------------------------------------------------

    weather = get_location_weather(
        location
    )

    if not weather["success"]:

        return (
            weather["error"],
            400
        )


    # -----------------------------------------------------
    # 3. GET CURRENT WEATHER VALUES
    # -----------------------------------------------------

    current = weather[
        "current"
    ]


    rainfall = current[
        "precipitation"
    ]

    temperature = current[
        "temperature"
    ]

    humidity = current[
        "humidity"
    ]

    wind_speed = current[
        "wind_speed"
    ]


    # -----------------------------------------------------
    # 4. PREDICT FLOOD RISK
    # -----------------------------------------------------

    prediction = predict_flood_risk(

        rainfall=rainfall,

        temperature=temperature,

        humidity=humidity,

        wind_speed=wind_speed
    )


    # -----------------------------------------------------
    # 5. SAVE WEATHER + RISK TO CSV
    # -----------------------------------------------------

    csv_file = save_weather_to_csv(

        weather,

        prediction
    )


    # -----------------------------------------------------
    # 6. DOWNLOAD CSV
    # -----------------------------------------------------

    return send_file(

        csv_file,

        mimetype="text/csv",

        as_attachment=True,

        download_name="flood_risk_data.csv"
    )