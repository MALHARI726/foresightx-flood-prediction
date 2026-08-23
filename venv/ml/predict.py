import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "flood_model.pkl")

def predict_flood_risk(features):
    model = joblib.load(MODEL_PATH)
    risk_class = model.predict([features])[0]
    risk_level = "HIGH" if risk_class == 1 else "LOW"
    return {"risk_score": int(risk_class)*70, "risk_level": risk_level}
