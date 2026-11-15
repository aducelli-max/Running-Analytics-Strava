

import requests
import pandas as pd

def saison_meteo(month):
    """Retourne des valeurs météo de secours adaptées au mois."""
    # Valeurs dans l'ordre : température, humidité, précipitations et nuages.
    if month in [3,4,5]: return 12, 65, 1.5, 55
    if month in [6,7,8]: return 22, 55, 1.0, 40
    if month in [9,10,11]: return 13, 75, 2.0, 65
    return 5, 80, 2.5, 70

def moyenne_mois(df, col, month, n=10):
    """Moyenne les n dernières valeurs valides de la colonne pour ce mois.

    Renvoie None lorsque moins de trois observations sont disponibles.
    """
    # Filtre les observations par mois et écarte les données manquantes.
    subset = df[df["month"] == month][col].dropna()
    if len(subset) >= 3:
        return subset.tail(n).mean()
    return None

def get_meteo(lat, lon, date, hour, df_h=None):
    """Récupère la météo horaire et complète les données manquantes.

    lat/lon indiquent le lieu, date est au format AAAA-MM-JJ, hour est
    l'heure locale et df_h est un historique facultatif.
    Le résultat contient temp, rh, precip, cloud et wind.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    # Demande les variables horaires pour la journée, dans le fuseau de Paris.
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relativehumidity_2m,precipitation,cloudcover,windspeed_10m",
        "start_date": date,
        "end_date": date,
        "timezone": "Europe/Paris"
    }

    # Limite l'attente à cinq secondes ; en cas d'erreur, renvoie des
    # valeurs météo fixes pour permettre au programme de continuer.
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        meteo = r.json()
    except Exception as e:
        print("⚠️ API météo non disponible, fallback utilisé :", e)
        return {
            "temp": 12,
            "rh": 60,
            "precip": 0,
            "cloud": 20,
            "wind": 5
        }

    # Cherche l'index de l'heure demandée. Si elle n'existe pas dans la
    # réponse, utilise la première observation disponible.
    try:
        idx = meteo["hourly"]["time"].index(f"{date}T{hour:02d}:00")
    except ValueError:
        idx = 0

    # Extrait chaque variable météo à l'index horaire sélectionné.
    temp = meteo["hourly"]["temperature_2m"][idx]
    rh = meteo["hourly"]["relativehumidity_2m"][idx]
    precip = meteo["hourly"]["precipitation"][idx]
    cloud = meteo["hourly"]["cloudcover"][idx]
    wind = meteo["hourly"]["windspeed_10m"][idx]

    # Le mois sert à sélectionner des valeurs de remplacement saisonnières.
    month = int(date.split("-")[1])

    # En l'absence de mesure, privilégie la moyenne historique du mois ;
    # si elle n'est pas disponible, utilise la valeur saisonnière.
    if pd.isna(rh):
        rh = moyenne_mois(df_h, "rh_mean", month) if df_h is not None else saison_meteo(month)[1]
    if pd.isna(precip):
        precip = moyenne_mois(df_h, "precip_mean", month) if df_h is not None else saison_meteo(month)[2]
    if pd.isna(cloud):
        cloud = moyenne_mois(df_h, "cloud_mean", month) if df_h is not None else saison_meteo(month)[3]

    return {
        "temp": temp,
        "rh": rh,
        "precip": precip,
        "cloud": cloud,
        "wind": wind
    }

