from sklearn.linear_model import LogisticRegression
import joblib
import numpy as np
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Mock training data
X = np.array([
    [10, 70, 20, 15],
    [50, 90, 60, 30],
    [5, 65, 5, 10],
    [60, 85, 55, 25]
])
y = [0, 1, 0, 1]  # 0=LOW, 1=HIGH

model = LogisticRegression()
model.fit(X, y)

joblib.dump(model, os.path.join(MODEL_DIR, "flood_model.pkl"))
print("✅ Mock flood model saved successfully.")
