

"""Synchronisation des activités Strava et enrichissement météo.

Ce script exécute le pipeline complet suivant :
1. refresh_tokens() : actualise le token OAuth Strava.
2. get_activities() : récupère la liste complète des activités.
3. Enrichissement des données avec la météo locale.
4. get_streams() : récupère les traces GPS point par point.
5. Export des fichiers CSV de résultat.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from utils.auth import refresh_tokens
from utils.meteo import get_meteo, saison_meteo
from utils.meteo import moyenne_mois, saison_meteo


# -----------------------------
# Récupération des activités Strava
# -----------------------------
def get_activities(access_token):
    """Récupère toutes les activités Strava en pagination.

    La Strava API renvoie les activités par lots de 200 éléments maximum.
    On boucle jusqu'à obtenir une page vide, ce qui marque la fin des données.
    """
    print("📥 Récupération des activités Strava…")
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}

    all_activities = []
    page = 1

    while True:
        params = {"page": page, "per_page": 200}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise RuntimeError(f"Erreur API Strava : {response.status_code} — {response.text}")

        data = response.json()
        if not data:
            break

        all_activities.extend(data)
        page += 1

    print(f"✔️ {len(all_activities)} activités récupérées")
    return all_activities


# -----------------------------
# Récupération des streams GPS Strava
# -----------------------------
def get_streams(activity_id, access_token):
    """Récupère les stream GPS associés à une activité Strava.

    Les clés demandées correspondent aux données utiles pour la piste GPS :
    lat/lon, altitude, vitesse, distance et fréquence cardiaque.
    """
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {
        "keys": "latlng,altitude,velocity_smooth,distance,heartrate",
        "key_by_type": True
    }

    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return None

    return r.json()


# -----------------------------
# Fonction robuste pour extraire lat/lon
# -----------------------------
def safe_latlng(value):
    """Retourne un couple (lat, lon) si la donnée est bien structurée.

    Certaines activités Strava peuvent avoir des coordonnées absentes ou au format
    inattendu. Cette fonction normalise le cas le plus fréquent.
    """
    if isinstance(value, list) and len(value) == 2:
        return value[0], value[1]
    return None, None


# -----------------------------
# Pipeline principal
# -----------------------------
def main():
    """Pipeline complet de synchronisation / enrichissement des activités Strava.

    Étapes détaillées :
    - authentication et refresh du token,
    - récupération des activités,
    - construction du DataFrame brut,
    - enrichissement météo et calculs de variables dérivées,
    - récupération des points GPS,
    - export des fichiers CSV finaux.
    """
    print("🔄 Rafraîchissement des tokens…")
    access_token, refresh_token = refresh_tokens()

    # 1) Récupération de la liste des activités Strava.
    activities = get_activities(access_token)

    # 2) Sauvegarde des données brutes avant transformation.
    df = pd.DataFrame(activities)
    df.to_csv("activities_raw.csv", index=False)
    print("✔️ activities_raw.csv généré")

    # 3) Ajout des données météorologiques calculées à partir des coordonnées et date.
    print("🌦️ Ajout de la météo…")

    df_h = df.copy()

    # GPS de départ/arrivée : normalisation des lat/lon dans des colonnes distinctes.
    df_h["start_lat"], df_h["start_lon"] = zip(*df_h["start_latlng"].apply(safe_latlng))
    df_h["end_lat"], df_h["end_lon"] = zip(*df_h["end_latlng"].apply(safe_latlng))

    # Dates : conversion UTC puis conversion locale pour exploiter l'heure locale.
    df_h["start_date"] = pd.to_datetime(df_h["start_date"], utc=True)
    df_h["start_date_local"] = df_h["start_date"].dt.tz_convert("Europe/Paris")
    df_h["year"] = df_h["start_date"].dt.year
    df_h["month"] = df_h["start_date"].dt.month
    df_h["hour"] = df_h["start_date_local"].dt.hour

    # -----------------------------
    # MÉTÉO BRUTE (sans fallback)
    # -----------------------------
    # Pour chaque activité, on demande la météo à l'heure de départ locale.
    # Si les coordonnées ou la météo sont absentes, on garde None pour filtrer ensuite.
    temp_list, rh_list, precip_list, cloud_list, wind_list = [], [], [], [], []

    for _, row in df_h.iterrows():
        lat = row["start_lat"]
        lon = row["start_lon"]

        if pd.isna(lat) or pd.isna(lon):
            temp_list.append(None)
            rh_list.append(None)
            precip_list.append(None)
            cloud_list.append(None)
            wind_list.append(None)
            continue

        date_str = row["start_date"].strftime("%Y-%m-%d")
        hour = int(row["hour"])

        # ⚠️ IMPORTANT : df_h=None pour éviter les fallback prématurés
        meteo = get_meteo(lat, lon, date_str, hour, None)

        if meteo is None:
            temp_list.append(None)
            rh_list.append(None)
            precip_list.append(None)
            cloud_list.append(None)
            wind_list.append(None)
        else:
            temp_list.append(meteo["temp"])
            rh_list.append(meteo["rh"])
            precip_list.append(meteo["precip"])
            cloud_list.append(meteo["cloud"])
            wind_list.append(meteo["wind"])

    # Création des colonnes météo directement à partir des résultats interpolés.
    df_h["temperature"] = temp_list
    df_h["wind_speed"] = wind_list
    df_h["temp_mean"] = df_h["temperature"]
    df_h["wind_mean"] = df_h["wind_speed"]
    df_h["rh_mean"] = rh_list
    df_h["precip_mean"] = precip_list
    df_h["cloud_mean"] = cloud_list

    # -----------------------------
    # Fallback météo (maintenant OK)
    # -----------------------------
    # Si la météo exacte manque pour une activité, on remplace par la moyenne mensuelle
    # ou par une valeur de saison. Ce mécanisme évite les NaN sur les colonnes d'entraînement.
    for col, idx in [("rh_mean", 1), ("precip_mean", 2), ("cloud_mean", 3)]:
        df_h[col] = df_h.apply(
            lambda row: row[col]
            if pd.notna(row[col])
            else (moyenne_mois(df_h, col, row["month"]) or saison_meteo(row["month"])[idx]),
            axis=1,
        )

    # Colonnes calculées : variables de contexte utiles pour l'analyse et le modèle.
    df_h["distance_km"] = df_h["distance"] / 1000
    df_h["vitesse_kmh"] = df_h["average_speed"] * 3.6
    df_h["allure_min_km"] = df_h["moving_time"] / df_h["distance_km"] / 60
    df_h["duration_min"] = df_h["moving_time"] / 60

    df_h["temp_x_dist"] = df_h["temp_mean"] * df_h["distance_km"]
    df_h["wind_x_dist"] = df_h["wind_mean"] * df_h["distance_km"]
    df_h["rh_x_dist"] = df_h["rh_mean"] * df_h["distance_km"]
    df_h["precip_x_dist"] = df_h["precip_mean"] * df_h["distance_km"]

    df_h["lat_start"] = df_h["start_lat"]
    df_h["lon_start"] = df_h["start_lon"]
    df_h["activity_id"] = df_h["id"]

    # -----------------------------
    # Catégorisation des distances (±10%)
    # -----------------------------
    # Permet de regrouper les séances par distance de référence (5 km, 10 km, etc.).
    def categorize_distance(d):
        km = d / 1000  # conversion en km

        # ±10% de marge
        if 4.5 <= km <= 5.5:
            return "5km"
        elif 9 <= km <= 11:
            return "10km"
        elif 13.5 <= km <= 16.5:
            return "15km"
        elif 18 <= km <= 20.5:
            return "20km"
        elif 20.5 <= km <= 22.5:  # semi-marathon ≈ 21.1 km
            return "Semi-marathon"
        else:
            return "Entrainement"

    df_h["categories_distances"] = (
    df_h["distance"]
    .apply(categorize_distance)
)


    # -----------------------------
    # Récupération GPS Strava → gps_points.csv
    # -----------------------------
    # Chaque activité a une trace GPS constituée de points successifs.
    # On les extrait et on les enregistre sous forme de tableau linéaire pour analyse.
    print("📡 Récupération des traces GPS…")

    gps_rows = []

    for _, row in df_h.iterrows():
        activity_id = row["id"]
        streams = get_streams(activity_id, access_token)

        if streams is None or "latlng" not in streams:
            continue

        latlng = streams["latlng"]["data"]
        altitude = streams.get("altitude", {}).get("data", [])
        velocity = streams.get("velocity_smooth", {}).get("data", [])
        distance = streams.get("distance", {}).get("data", [])
        heartrate = streams.get("heartrate", {}).get("data", [])

        for i in range(len(latlng)):
            gps_rows.append({
                "activity_id": activity_id,
                "lat": latlng[i][0],
                "lon": latlng[i][1],
                "altitude": altitude[i] if i < len(altitude) else None,
                "velocity": velocity[i] if i < len(velocity) else None,
                "distance": distance[i] if i < len(distance) else None,
                "heartrate": heartrate[i] if i < len(heartrate) else None
            })

    # 4) Export des données dans un dossier créé aussi sur les déploiements neufs.
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    gps_df = pd.DataFrame(gps_rows)
    gps_df.to_csv(data_dir / "gps_points.csv", index=False)
    print("✔️ data/gps_points.csv généré")

    # 5) Export final de l'ensemble des activités enrichies et prêtes pour l'analyse.
    df_h.to_csv(data_dir / "activities_with_weather_harmonized.csv", index=False)
    print("✔️ data/activities_with_weather_harmonized.csv généré")
    
    return df_h


if __name__ == "__main__":
    main()

