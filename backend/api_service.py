import requests
import csv
import os

from config import (
    WEATHER_API_URL,
    GEOCODING_API_URL,
    API_TIMEOUT,
    TIMEZONE,
    DATA_DIR,
    LIVE_CSV_PATH
)


# =========================================================
# GET MAHARASHTRA LOCATION COORDINATES
# =========================================================

def get_coordinates(location):

    params = {
        "name": location,
        "count": 10,
        "language": "en",
        "format": "json",
        "countryCode": "IN"
    }

    try:

        response = requests.get(
            GEOCODING_API_URL,
            params=params,
            timeout=API_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:

            return {
                "success": False,
                "error": f"Location '{location}' was not found."
            }

        # Check results for Maharashtra
        for place in results:

            country = place.get(
                "country",
                ""
            )

            state = place.get(
                "admin1",
                ""
            )

            if (
                country.lower() == "india"
                and state.lower() == "maharashtra"
            ):

                return {

                    "success": True,

                    "location": place.get(
                        "name"
                    ),

                    "latitude": place.get(
                        "latitude"
                    ),

                    "longitude": place.get(
                        "longitude"
                    ),

                    "country": country,

                    "state": state
                }

        return {
            "success": False,
            "error": (
                f"'{location}' was found, "
                "but it is not in Maharashtra."
            )
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Location API timed out."
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": f"Location API error: {str(e)}"
        }


# =========================================================
# GET LIVE WEATHER DATA
# =========================================================

def get_weather_data(latitude, longitude):

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "showers,"
            "wind_speed_10m"
        ),

        "hourly": (
            "precipitation,"
            "rain,"
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m"
        ),

        "forecast_days": 3,

        "timezone": TIMEZONE,

        "temperature_unit": "celsius",

        "wind_speed_unit": "kmh",

        "precipitation_unit": "mm"
    }

    try:

        response = requests.get(
            WEATHER_API_URL,
            params=params,
            timeout=API_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        current = data.get(
            "current",
            {}
        )

        hourly = data.get(
            "hourly",
            {}
        )

        return {

            "success": True,

            "current": {

                "time": current.get(
                    "time"
                ),

                "temperature": current.get(
                    "temperature_2m"
                ),

                "humidity": current.get(
                    "relative_humidity_2m"
                ),

                "precipitation": current.get(
                    "precipitation"
                ),

                "rain": current.get(
                    "rain"
                ),

                "showers": current.get(
                    "showers"
                ),

                "wind_speed": current.get(
                    "wind_speed_10m"
                )
            },

            "hourly": {

                "time": hourly.get(
                    "time",
                    []
                ),

                "precipitation": hourly.get(
                    "precipitation",
                    []
                ),

                "rain": hourly.get(
                    "rain",
                    []
                ),

                "temperature": hourly.get(
                    "temperature_2m",
                    []
                ),

                "humidity": hourly.get(
                    "relative_humidity_2m",
                    []
                ),

                "wind_speed": hourly.get(
                    "wind_speed_10m",
                    []
                )
            }
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Weather API timed out."
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": f"Weather API error: {str(e)}"
        }


# =========================================================
# GET LOCATION + LIVE WEATHER
# =========================================================

def get_location_weather(location):

    # Find Maharashtra location
    coordinates = get_coordinates(location)

    if not coordinates["success"]:

        return coordinates

    # Get live weather
    weather = get_weather_data(
        coordinates["latitude"],
        coordinates["longitude"]
    )

    if not weather["success"]:

        return weather

    # Combine location + weather
    return {

        "success": True,

        "location": {

            "name": coordinates[
                "location"
            ],

            "state": coordinates[
                "state"
            ],

            "country": coordinates[
                "country"
            ],

            "latitude": coordinates[
                "latitude"
            ],

            "longitude": coordinates[
                "longitude"
            ]
        },

        "current": weather[
            "current"
        ],

        "hourly": weather[
            "hourly"
        ]
    }


# =========================================================
# SAVE LIVE WEATHER + FLOOD RISK TO CSV
# =========================================================

def save_weather_to_csv(
    data,
    prediction
):

    # Create data folder
    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    location = data[
        "location"
    ]

    current = data[
        "current"
    ]

    # -----------------------------------------------------
    # Create / overwrite CSV
    # -----------------------------------------------------
    # We create a fresh CSV for each request so the user
    # downloads the current location's result.
    # -----------------------------------------------------

    with open(
        LIVE_CSV_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        # Header
        writer.writerow([

            "location",
            "state",
            "country",
            "latitude",
            "longitude",
            "time",

            "temperature_c",
            "humidity_percent",

            "rainfall_mm",
            "rain_mm",
            "showers_mm",

            "wind_speed_kmh",

            "risk_score",
            "risk_level"
        ])

        # Data
        writer.writerow([

            location["name"],

            location["state"],

            location["country"],

            location["latitude"],

            location["longitude"],

            current["time"],

            current["temperature"],

            current["humidity"],

            current["precipitation"],

            current["rain"],

            current["showers"],

            current["wind_speed"],

            prediction["risk_score"],

            prediction["risk_level"]
        ])

    return LIVE_CSV_PATH


# =========================================================
# OPTIONAL: TEST API SERVICE DIRECTLY
# =========================================================

if __name__ == "__main__":

    location = input(
        "Enter Maharashtra location: "
    ).strip()

    result = get_location_weather(
        location
    )

    if result["success"]:

        print("\nLocation:")
        print(
            result["location"]["name"]
        )

        print(
            "\nTemperature:",
            result["current"]["temperature"],
            "°C"
        )

        print(
            "Humidity:",
            result["current"]["humidity"],
            "%"
        )

        print(
            "Rainfall:",
            result["current"]["precipitation"],
            "mm"
        )

        print(
            "Wind:",
            result["current"]["wind_speed"],
            "km/h"
        )

    else:

        print(
            "\nERROR:",
            result["error"]
        )