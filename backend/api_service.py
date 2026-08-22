import requests


# Open-Meteo LIVE Weather API
API_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather_data(latitude, longitude):
    """
    Get live weather and rainfall data
    using latitude and longitude.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,

        # Current live weather
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "showers,"
            "wind_speed_10m"
        ),

        # Hourly forecast data
        "hourly": (
            "precipitation,"
            "rain,"
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m"
        ),

        # Forecast for next 3 days
        "forecast_days": 3,

        # Indian time
        "timezone": "Asia/Kolkata",

        # Units
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm"
    }

    try:

        # Send request to Open-Meteo
        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        # Check if request was successful
        response.raise_for_status()

        # Convert response into JSON
        data = response.json()

        # Extract current weather
        current = data.get("current", {})

        # Extract hourly weather
        hourly = data.get("hourly", {})

        # Return clean data
        return {
            "success": True,

            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "current": {
                "time": current.get("time"),
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "rain": current.get("rain"),
                "showers": current.get("showers"),
                "wind_speed": current.get("wind_speed_10m")
            },

            "hourly": {
                "time": hourly.get("time", []),
                "precipitation": hourly.get("precipitation", []),
                "rain": hourly.get("rain", []),
                "temperature": hourly.get("temperature_2m", []),
                "humidity": hourly.get("relative_humidity_2m", []),
                "wind_speed": hourly.get("wind_speed_10m", [])
            }
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Weather API request timed out."
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": f"Weather API request failed: {str(e)}"
        }

    except Exception as e:

        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


# -------------------------------------------------------
# TEST THE API
# -------------------------------------------------------

if __name__ == "__main__":

    # Mumbai coordinates
    latitude = 19.0760
    longitude = 72.8777

    print("\nConnecting to Open-Meteo LIVE API...")

    weather = get_weather_data(
        latitude,
        longitude
    )

    if weather["success"]:

        print("\n========== LIVE WEATHER DATA ==========")

        print(
            "Latitude:",
            weather["location"]["latitude"]
        )

        print(
            "Longitude:",
            weather["location"]["longitude"]
        )

        print(
            "Time:",
            weather["current"]["time"]
        )

        print(
            "Temperature:",
            weather["current"]["temperature"],
            "°C"
        )

        print(
            "Humidity:",
            weather["current"]["humidity"],
            "%"
        )

        print(
            "Precipitation:",
            weather["current"]["precipitation"],
            "mm"
        )

        print(
            "Rain:",
            weather["current"]["rain"],
            "mm"
        )

        print(
            "Showers:",
            weather["current"]["showers"],
            "mm"
        )

        print(
            "Wind Speed:",
            weather["current"]["wind_speed"],
            "km/h"
        )

        print("\n========== NEXT HOURLY RAINFALL ==========")

        rainfall = weather["hourly"]["precipitation"]

        for i, value in enumerate(rainfall[:10]):

            print(
                f"Hour {i + 1}: {value} mm"
            )

    else:

        print("\nERROR:")
        print(weather["error"])