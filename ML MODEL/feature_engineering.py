import pandas as pd

def preprocess_data(raw_rainfall, raw_weather, raw_history, output_path):
    rainfall = pd.read_csv(raw_rainfall)
    weather = pd.read_csv(raw_weather)
    history = pd.read_csv(raw_history)

    merged = rainfall.merge(weather, on=["date", "location"], how="inner")
    merged['year'] = pd.to_datetime(merged['date']).dt.year
    merged = merged.merge(history, on=["year", "location"], how="left")

    merged['flood_risk'] = merged['flood_occurred'].fillna(0)
    merged.drop(columns=['flood_occurred'], inplace=True)

    merged.to_csv(output_path, index=False)
    print("✅ Data processed and saved to:", output_path)

if __name__ == "__main__":
    preprocess_data("data/raw/rainfall.csv", "data/raw/weather.csv", "data/raw/flood_history.csv", "data/processed/flood_training_data.csv")
