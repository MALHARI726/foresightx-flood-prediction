import pandas as pd
import joblib

def predict_flood(input_data_path, model_path):
    model = joblib.load(model_path)
    data = pd.read_csv(input_data_path)

    X = data[['rainfall', 'temperature', 'humidity', 'wind_speed']]
    predictions = model.predict(X)
    data['predicted_flood_risk'] = predictions

    print("✅ Predictions complete!")
    return data

if __name__ == "__main__":
    result = predict_flood("data/processed/flood_training_data.csv", "ml/flood_model.pkl")
    print(result.head())
