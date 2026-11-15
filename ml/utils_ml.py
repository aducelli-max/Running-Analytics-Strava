import pickle
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.ensemble import GradientBoostingRegressor

from utils.meteo import moyenne_mois, saison_meteo


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "activities_with_weather_harmonized.csv"
MODEL_PATH = ROOT_DIR / "ml" / "model.pkl"
FEATURES = [
    "temp_mean",
    "rh_mean",
    "precip_mean",
    "cloud_mean",
    "wind_mean",
    "temp_x_dist",
    "wind_x_dist",
    "rh_x_dist",
    "precip_x_dist",
    "total_elevation_gain",
    "distance_km",
    "month",
    "hour",
]


@st.cache_data
def _load_data():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(
            "Données Strava absentes. Utilisez le bouton « Mise à jour » "
            "pour synchroniser vos activités."
        )
    return pd.read_csv(DATA_PATH)


@st.cache_resource
def _load_model():
    if MODEL_PATH.is_file():
        with MODEL_PATH.open("rb") as model_file:
            return pickle.load(model_file), False

    data = _load_data()
    training_data = data[FEATURES + ["vitesse_kmh"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()
    if len(training_data) < 2:
        raise ValueError(
            "Il faut au moins deux activités avec une vitesse valide "
            "pour entraîner le modèle."
        )

    model = GradientBoostingRegressor(random_state=42)
    model.fit(training_data[FEATURES], training_data["vitesse_kmh"])
    return model, True


def is_model_trained_from_data():
    return _load_model()[1]


def predict_time(
    distance_km, temp, rh, precip, cloud, wind, month, hour, total_elevation_gain
):
    data = _load_data()
    model, _ = _load_model()

    if pd.isna(rh):
        rh = moyenne_mois(data, "rh_mean", month) or saison_meteo(month)[1]
    if pd.isna(precip):
        precip = moyenne_mois(data, "precip_mean", month) or saison_meteo(month)[2]
    if pd.isna(cloud):
        cloud = moyenne_mois(data, "cloud_mean", month) or saison_meteo(month)[3]

    x = pd.DataFrame([{
        "temp_mean": temp,
        "rh_mean": rh,
        "precip_mean": precip,
        "cloud_mean": cloud,
        "wind_mean": wind,
        "temp_x_dist": temp * distance_km,
        "wind_x_dist": wind * distance_km,
        "rh_x_dist": rh * distance_km,
        "precip_x_dist": precip * distance_km,
        "total_elevation_gain": total_elevation_gain,
        "distance_km": distance_km,
        "month": month,
        "hour": hour,
    }]).fillna(0)

    speed = model.predict(x)[0]
    time_min = (distance_km / speed) * 60
    return speed, time_min
