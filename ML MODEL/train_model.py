import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model(data_path, model_path):
    df = pd.read_csv(data_path)
    X = df[['rainfall', 'temperature', 'humidity', 'wind_speed']]
    y = df['flood_risk']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    joblib.dump(model, model_path)
    print("✅ Model trained and saved successfully!")

if __name__ == "__main__":
    train_model("data/processed/flood_training_data.csv", "ml/flood_model.pkl")
