from sklearn.metrics import accuracy_score
import pandas as pd
import joblib

def evaluate_model(model_path, test_data_path):
    model = joblib.load(model_path)
    df = pd.read_csv(test_data_path)

    X_test = df[['rainfall', 'temperature', 'humidity', 'wind_speed']]
    y_test = df['flood_risk']
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ Model accuracy: {accuracy:.2f}")

if __name__ == "__main__":
    evaluate_model("ml/flood_model.pkl", "data/processed/flood_training_data.csv")
