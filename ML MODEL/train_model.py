import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


# =========================
# 1. LOAD TRAINING DATA
# =========================

df = pd.read_csv("data/raw/training_data.csv")

# Date ko datetime mein convert
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Rainfall ko numeric banao
df["Rainfall"] = pd.to_numeric(
    df["Manual Daily Rainfall (mm)"],
    errors="coerce"
)

# Date ke according sort
df = df.sort_values("Date").reset_index(drop=True)


# =========================
# 2. CREATE RAINFALL FEATURES
# =========================

# Previous day's rainfall
df["Rainfall_1d"] = df["Rainfall"].shift(1)

# Previous 3 days total rainfall
df["Rainfall_3d"] = (
    df["Rainfall"]
    .rolling(window=3)
    .sum()
    .shift(1)
)

# Previous 7 days total rainfall
df["Rainfall_7d"] = (
    df["Rainfall"]
    .rolling(window=7)
    .sum()
    .shift(1)
)


# =========================
# 3. REMOVE ROWS WITH MISSING FEATURES
# =========================

df = df.dropna().reset_index(drop=True)


# =========================
# 4. SELECT FEATURES
# =========================

features = [
    "Rainfall",
    "Rainfall_1d",
    "Rainfall_3d",
    "Rainfall_7d"
]

X = df[features]
y = df["Flood"]


# =========================
# 5. TRAIN / TEST SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# =========================
# 6. RANDOM FOREST MODEL
# =========================

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
    min_samples_leaf=2
)

model.fit(X_train, y_train)


# =========================
# 7. MODEL EVALUATION
# =========================

y_pred = model.predict(X_test)

print("\n==============================")
print("MODEL EVALUATION")
print("==============================")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    zero_division=0
))


# =========================
# 8. SAVE MODEL
# =========================

joblib.dump(model, "ML MODEL/flood_model.pkl")

print("\n==============================")
print("MODEL SAVED SUCCESSFULLY")
print("==============================")

print("File: ML MODEL/flood_model.pkl")
print("Features:", features)