# =========================================================
# FLOOD RISK PREDICTION
# WITHOUT ML MODEL
# =========================================================


def predict_flood_risk(
    rainfall,
    temperature,
    humidity,
    wind_speed
):

    # -----------------------------------------------------
    # Start risk score
    # -----------------------------------------------------

    risk_score = 0


    # -----------------------------------------------------
    # RAINFALL
    # -----------------------------------------------------

    if rainfall >= 50:

        risk_score += 50

    elif rainfall >= 20:

        risk_score += 35

    elif rainfall >= 10:

        risk_score += 20

    elif rainfall >= 5:

        risk_score += 10


    # -----------------------------------------------------
    # HUMIDITY
    # -----------------------------------------------------

    if humidity >= 90:

        risk_score += 20

    elif humidity >= 80:

        risk_score += 15

    elif humidity >= 70:

        risk_score += 10


    # -----------------------------------------------------
    # WIND SPEED
    # -----------------------------------------------------

    if wind_speed >= 40:

        risk_score += 15

    elif wind_speed >= 25:

        risk_score += 10

    elif wind_speed >= 15:

        risk_score += 5


    # -----------------------------------------------------
    # TEMPERATURE
    # -----------------------------------------------------

    # Temperature has a smaller effect
    # compared with rainfall.

    if temperature >= 35:

        risk_score += 5


    # -----------------------------------------------------
    # LIMIT SCORE TO 100
    # -----------------------------------------------------

    risk_score = min(
        risk_score,
        100
    )


    # -----------------------------------------------------
    # DETERMINE FLOOD RISK
    # -----------------------------------------------------

    if risk_score >= 70:

        risk_level = "HIGH"

    elif risk_score >= 40:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"


    # -----------------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------------

    return {

        "risk_score": risk_score,

        "risk_level": risk_level

    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    result = predict_flood_risk(

        rainfall=50,

        temperature=25,

        humidity=90,

        wind_speed=30
    )


    print(
        "Risk Score:",
        result["risk_score"]
    )

    print(
        "Risk Level:",
        result["risk_level"]
    )