from altair import Color
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
from pathlib import Path
import time
import plotly.graph_objects as go
import numpy as np

from ml.utils_ml import is_model_trained_from_data, predict_time
from utils.couleur_allure import couleur_allure
from utils.meteo_heart_rate import meteo_heart_rate
from utils.color_pct import color_pct
from utils.folium_color import folium_color
from utils.meteo import get_meteo
from utils.strava_sync import main
from utils.convert_minutes_to_hhmm import format_duration, format_pace

DATA_DIR = Path(__file__).resolve().parent / "data"
ACTIVITIES_FILE = DATA_DIR / "activities_with_weather_harmonized.csv"
GPS_FILE = DATA_DIR / "gps_points.csv"

# -------------------------------------------------------------------
# IMPORTS ET CONFIGURATION GLOBALE
# -------------------------------------------------------------------
# Les bibliothèques ci-dessous sont utilisées pour :
# - l'interface Streamlit,
# - la manipulation des données (pandas, numpy),
# - l'affichage des cartes (folium, streamlit_folium),
# - la génération de graphiques (plotly),
# - les fonctions métier du projet (météo, prédiction, Strava).


# ---------------------
# INITIALISATION SESSION
# ---------------------
# Ces variables permettent de mémoriser l'état de navigation et
# la course sélectionnée entre les différentes pages de l'application.
if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_activity" not in st.session_state:
    st.session_state.selected_activity = None
    


# -------------------------------------------------------------------
# PAGE 1 — ACCUEIL
# -------------------------------------------------------------------
# Cette section affiche la landing page de l'application, la bannière,
# les boutons d'action et permet de mettre à jour les données ou
# d'importer un fichier GPX.
if st.session_state.page == "home":

    # Liste des images dans le dossier static
    headers_image = [
        "static/Printemps_running.jpeg",
        "static/Automne_running.jpg",
        "static/Hiver_running.jpg",
        "static/Ete_running.jpg"
    ]
    
    # Index qui change à chaque rafraîchissement
    index = int(time.time() // 5 % len(headers_image))
    
    
    # --- HEADER IMAGE ---
    st.image(headers_image[index], use_container_width=True)
    st.markdown("<h1 style='text-align:center;'>🏃‍♂️ Météo & Performance — Running Analytics with Strava</h1>", unsafe_allow_html=True)
    st.caption(
        ":material/info: Mets tes activités Strava à jour, puis sélectionne "
        "une course pour consulter ses statistiques et son estimation."
    )



    # --- Boutons d'action ---
# Cette section permet de lancer la mise à jour des activités Strava et
# d'importer un fichier GPX pour traiter un parcours externe.
    col1, col2 = st.columns(2)

    with col1:
        # Bouton de synchronisation des données Strava.
        if st.button(
            "🔄 Mise à jour",
            help="Synchronise tes activités Strava et actualise les statistiques.",
        ):
            with st.spinner("⏳ Mise à jour des activités…"):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress.progress(i + 1)
                df_updated = main()
            if df_updated is None:
                st.error("❌ Impossible de mettre à jour les activités : données vides ou erreur Strava.")
                
            else:
                # Vider le cache Streamlit
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✔️ Mise à jour terminée !")
                st.write(f"📊 Total activités : {len(df_updated)}"
                )
                time.sleep(1)
                
                st.rerun()

    with col2:
        uploaded_gpx = st.file_uploader(
            "📥 Sélectionner un fichier GPX",
            type=["gpx"],
            help=(
                "Choisis un fichier .gpx. Pour le moment, l'application "
                "confirme sa réception sans l'ajouter aux statistiques."
            ),
        )
        if uploaded_gpx is not None:
            st.write("GPX reçu, traitement en cours...")


# ---------------------
# CHARGEMENT DES DONNÉES
# ---------------------
# Charge les données d'activités et les points GPS depuis les fichiers CSV.
# La fonction est mise en cache pour éviter de relire les fichiers à chaque rafraîchissement.
@st.cache_data
def load_data():
    if not ACTIVITIES_FILE.is_file() or not GPS_FILE.is_file():
        return None, None

    # Lecture du dataset principal contenant les infos de performance et météo.
    df = pd.read_csv(ACTIVITIES_FILE)

    # On conserve uniquement les sorties en course à pied.
    df = df[df["sport_type"] == "Run"].copy()

    # Conversion explicite des dates en datetime timezone-aware.
    df["start_date"] = pd.to_datetime(
        df["start_date"],
        utc=True
    )

    df["start_date_local"] = pd.to_datetime(
        df["start_date_local"],
        utc=True
    )

    # Normalisation de l'allure pour éliminer les valeurs invalides ou infinies.
    df["allure_min_km"] = (
        pd.to_numeric(
            df["allure_min_km"],
            errors="coerce"
        )
        .replace([np.inf, -np.inf], np.nan)
    )

    # Lecture des points GPS associés à chaque activité.
    gps = pd.read_csv(GPS_FILE)

    return df, gps


# Appel unique de chargement des données au démarrage de l'application.
df, gps = load_data()
if df is None or gps is None:
    st.warning("Aucune donnée Strava n’est encore disponible sur ce déploiement.")
    st.info("Clique sur « Mise à jour » pour synchroniser tes activités Strava.")
    st.stop()

if df.empty:
    st.error("Le dataframe df est vide")
    st.stop()

if gps.empty:
    st.error("Le dataframe gps est vide")
    st.stop()
    
    
# ---------------------
# BARRE LATERAL : MÉTÉO DU JOUR & STATISTIQUES PERSO
# ---------------------
# Sélectionne la dernière activité connue pour extraire la météo du lieu de départ.
latest_activities = df.dropna(subset=["start_date_local"])
if latest_activities.empty:
        st.error("Aucune activité de course avec une date valide n’est disponible.")
        st.stop()

best_row_today = latest_activities.loc[
        latest_activities["start_date_local"].idxmax()
    ]
lat = best_row_today["lat_start"]
lon = best_row_today["lon_start"]
date_str = datetime.now().strftime("%Y-%m-%d")
hour_now = datetime.now().hour

# Récupération de la météo actuelle à partir des coordonnées de la dernière activité.
meteo_today = get_meteo(lat, lon, date_str, hour_now, df)

# Affichage de la météo dans la sidebar.
st.sidebar.title(
    "La météo du jour",
    icon=":material/cloud:",
    help="Conditions estimées près du départ de ta dernière course.",
)
st.sidebar.write(f"**🌡️ Température :** {meteo_today['temp']} °C")
st.sidebar.write(f"**💨 Vent :** {meteo_today['wind']} km/h")
st.sidebar.write(f"**💧 Humidité :** {meteo_today['rh']} %")
st.sidebar.write(f"**🌧️ Précipitations :** {meteo_today['precip']} mm")
st.sidebar.write(f"**☁️ Nuages :** {meteo_today['cloud']} %")

# Affichage de statistiques globales pour aider à contextualiser les performances.
st.sidebar.title(
    "Statistiques globales",
    icon=":material/monitoring:",
    help="Moyennes calculées à partir de toutes tes courses synchronisées.",
)
    
st.sidebar.write(f"**📏 Distance moy. :** {df["distance_km"].mean():.2f} km")
st.sidebar.write(f"**⌛ Durée moy. :** {format_duration(df['duration_min'].mean())}")
st.sidebar.write(f"⏱️ **Allure moy. :** {format_pace(df['allure_min_km'].mean())}")
st.sidebar.write(f"**🏃Vitesse moy. :** {df['vitesse_kmh'].mean():.1f} km/h")
st.sidebar.write(f"**💪Score d'effort moy. :** {df['suffer_score'].mean():.1f}")
st.sidebar.write(f"**⚡Dénivelé moy. :** {df['total_elevation_gain'].mean():.1f} M")
    
st.sidebar.write(f"**💓 Cardio moy. :** {df["average_heartrate"].mean():.2f} Bpm")
    
st.sidebar.write(f"**🏁 Activités :** {df['activity_id'].count()} sorties") 
        
    

# ---------------------
# FILTRES ANNÉE / MOIS / CATÉGORIES
# ---------------------
# Construction des filtres interactifs pour sélectionner un sous-ensemble d'activités.
st.caption(
    ":material/info: Choisis une période et des distances pour filtrer "
    "la carte et la liste des courses."
)
df_cat = df.copy()
last_activity = df_cat.sort_values(by="start_date_local", ascending=False).iloc[0]
default_year = int(last_activity["year"])
default_month = int(last_activity["month"])

annees_disponibles = sorted(df_cat["year"].unique())
annee = st.selectbox("Choisir l'année :", annees_disponibles,
                         index=annees_disponibles.index(default_year),
                         help="Affiche les courses réalisées pendant cette année.")

mois_noms = {
        1:"Janvier",2:"Février",3:"Mars",4:"Avril",5:"Mai",6:"Juin",
        7:"Juillet",8:"Août",9:"Septembre",10:"Octobre",11:"Novembre",12:"Décembre"
    }

mois_dispo_num = sorted(df_cat[df_cat["year"] == annee]["month"].unique())
mois_nom = st.selectbox("Choisir le mois :", [mois_noms[m] for m in mois_dispo_num],
                            index=mois_dispo_num.index(default_month),
                            help="Affiche les courses réalisées pendant ce mois.")
mois_num = [k for k,v in mois_noms.items() if v == mois_nom][0]

df_filtre = df_cat[(df_cat["year"] == annee) & (df_cat["month"] == mois_num)]
categories_dispo = sorted(df_filtre["categories_distances"].unique())
categories_selection = st.multiselect("Choisir les catégories :", categories_dispo,
                                          default=categories_dispo,
                                          help="Choisis les distances à afficher. Plusieurs choix sont possibles.")

df_filtre = df_filtre[df_filtre["categories_distances"].isin(categories_selection)]

# Titre de la section qui affiche les parcours du mois en sélection.
st.subheader(
    "Parcours du mois sélectionné",
    icon=":material/map:",
    help="La carte montre les parcours de la période choisie. Clique sur un marqueur pour voir les statistiques d'une course.",
)

# ---------------------
# SÉCURITÉ : AUCUNE ACTIVITÉ
# ---------------------
# Vérifie qu'il y a bien au moins une activité dans le filtrage courant.
if df_filtre.empty:
        st.warning("⚠️ Aucune activité pour ce mois")
        st.stop()
        
# ---------------------
# SÉCURITÉ : COORDONNÉES INVALIDES
# ---------------------
# S'assure que la première activité du filtre possède des coordonnées GPS valides.
lat0 = df_filtre.iloc[0]["lat_start"]
lon0 = df_filtre.iloc[0]["lon_start"]

if pd.isna(lat0) or pd.isna(lon0):
        st.warning("⚠️ Aucun élément pour cette catégorie")
        st.stop()
       

# ---------------------
# CARTE CENTRÉE SUR LA PREMIÈRE ACTIVITÉ
# ---------------------
# Initialise la carte Folium sur la première activité disponible du mois.
carte = folium.Map(
        location=[df_filtre.iloc[0]["lat_start"], df_filtre.iloc[0]["lon_start"]],
        zoom_start=13
    )

# -----------------------------
# AFFICHAGE DE TOUS LES PARCOURS
# -----------------------------
# Cette boucle trace chaque sortie du mois sur la carte et colorie chaque
# segment selon son allure pour visualiser immédiatement les variations de rythme.
popup_activity_ids = {}
popup_label_counts = {}

for activity_id in df_filtre["activity_id"].unique():

        gps_run = (
            gps[gps["activity_id"] == activity_id]
            .dropna(subset=["lat", "lon"])
            .copy()
        )

        if len(gps_run) < 2:
            continue

        # Réduit le nombre de points pour alléger le rendu sur la carte.
        gps_run = gps_run.iloc[::3].copy()

    # Pour les parcours très courts
        if len(gps_run) < 2:
            continue

        # Calcule un rythme approximatif en min/km à partir de la vitesse.
        gps_run["pace"] = (1000 / gps_run["velocity"]) / 60
        coords = gps_run[["lat", "lon"]].values.tolist()
        activity = df_filtre[df_filtre["activity_id"] == activity_id].iloc[0]
        distance_km = activity["distance_km"]
        start_date = activity["start_date_local"].strftime("%Y-%m-%d %H:%M:%S")
        popup_label_base = (
            f"{distance_km:.1f} km · {start_date} · "
            f"{format_duration(activity['duration_min'])}"
        )
        popup_label_counts[popup_label_base] = (
            popup_label_counts.get(popup_label_base, 0) + 1
        )
        popup_label = popup_label_base
        if popup_label_counts[popup_label_base] > 1:
            popup_label = (
                f"{popup_label_base} · Sortie "
                f"{popup_label_counts[popup_label_base]}"
            )
        popup_activity_ids[popup_label] = activity_id
        heartrate = activity["average_heartrate"]
        heartrate_text = f"{heartrate:.0f} BPM" if pd.notna(heartrate) else "—"
        elevation = activity["total_elevation_gain"]
        elevation_text = f"{elevation:.0f} m" if pd.notna(elevation) else "—"
        popup_html = (
            f"<strong>{popup_label}</strong><br>"
            f"Allure : {format_pace(activity['allure_min_km'])}<br>"
            f"Vitesse : {activity['vitesse_kmh']:.2f} km/h<br>"
            f"Fréquence cardiaque : {heartrate_text}<br>"
            f"Dénivelé : {elevation_text}"
        )

    # Trace grise de fond
        folium.PolyLine(
            coords,
            color="grey",
            weight=3,
            opacity=0.3
        ).add_to(carte)

        # Trace colorée selon allure
        for i in range(len(coords) - 1):
            folium.PolyLine(
                [coords[i], coords[i+1]],
                color=couleur_allure(float(gps_run.iloc[i].pace)),
                weight=5,
                opacity=0.9
            ).add_to(carte)

        # Markers départ / arrivée
        folium.Marker(
            coords[0],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Départ · {distance_km:.1f} km",
            icon=folium.Icon(icon="play")
        ).add_to(carte)

        folium.Marker(
            coords[-1],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Arrivée · {distance_km:.1f} km",
            icon=folium.Icon(color='black', icon="flag-checkered", prefix="fa")
        ).add_to(carte)

# -----------------------------
# ZOOM AUTOMATIQUE SUR TOUTES LES COURSES
# -----------------------------
# Ajuste le zoom de la carte pour inclure l'ensemble des parcours filtrés.
gps_all = gps[gps["activity_id"].isin(df_filtre["activity_id"])
    ].dropna(subset=["lat", "lon"])

map_data = None
if not gps_all.empty:
        min_lat = gps_all["lat"].min()
        max_lat = gps_all["lat"].max()
        min_lon = gps_all["lon"].min()
        max_lon = gps_all["lon"].max()

        carte.fit_bounds(
            [[min_lat, min_lon], 
             [max_lat, max_lon]])

    # --- Affichage Folium ---
    # Intègre la carte interactive dans l'interface Streamlit.
        map_data = st_folium(
            carte, 
            height=600, 
            width=900,
            returned_objects=["last_object_clicked_popup"],
        )

if map_data and map_data.get("last_object_clicked_popup"):
        popup_label = map_data["last_object_clicked_popup"].splitlines()[0].strip()
        activity_clicked = popup_activity_ids.get(popup_label)
        if activity_clicked is not None:
            st.session_state["selected_map_activity_id"] = activity_clicked
            st.session_state["selected_activity"] = (
                df_filtre[df_filtre["activity_id"] == activity_clicked].iloc[0]
            )

selected_map_activity_id = st.session_state.get("selected_map_activity_id")
selected_map_activity = None
if selected_map_activity_id is not None:
        selected_rows = df_filtre[
            df_filtre["activity_id"] == selected_map_activity_id
        ]
        if selected_rows.empty:
            st.session_state.pop("selected_map_activity_id", None)
        else:
            selected_map_activity = selected_rows.iloc[0]

if selected_map_activity is not None:
        with st.container(border=True):
            st.subheader(
                "Course sélectionnée",
                icon=":material/directions_run:",
                help="Résumé des statistiques de la course choisie sur la carte.",
            )
            st.caption(
                selected_map_activity["start_date_local"].strftime(
                    "%d/%m/%Y à %H:%M"
                )
                + f" · {selected_map_activity['categories_distances']}"
            )

            first_stats_row = st.columns(3)
            first_stats_row[0].metric(
                "Distance (km)", f"{selected_map_activity['distance_km']:.1f}"
            )
            first_stats_row[1].metric(
                "Durée", format_duration(selected_map_activity["duration_min"])
            )
            first_stats_row[2].metric(
                "Allure", format_pace(selected_map_activity["allure_min_km"])
            )

            second_stats_row = st.columns(3)
            second_stats_row[0].metric(
                "Vitesse (km/h)", f"{selected_map_activity['vitesse_kmh']:.1f}"
            )
            heartrate = selected_map_activity["average_heartrate"]
            second_stats_row[1].metric(
                "Cardio (BPM)", f"{heartrate:.0f}" if pd.notna(heartrate) else "—"
            )
            elevation = selected_map_activity["total_elevation_gain"]
            second_stats_row[2].metric(
                "Dénivelé (m)", f"{elevation:.0f}" if pd.notna(elevation) else "—"
            )

            if st.button(
                "🔮 Prédire cette course",
                key="analyze_map_activity",
                icon=":material/insights:",
                width="stretch",
                help="Ouvre l'analyse météo et l'estimation pour cette course.",
            ):
                st.session_state["selected_activity"] = selected_map_activity
                st.session_state.page = "prediction"
                st.rerun()

# -----------------------------
# COURSES DU MOIS
# -----------------------------
# Cette section détaille ensuite chaque course du mois sous forme de cartes,
# graphiques et boutons d'action pour naviguer vers l'analyse prédictive.
st.subheader(
    "Courses du mois",
    icon=":material/calendar_month:",
    help="Chaque carte résume une course. Le bouton permet d'ouvrir son analyse météo.",
)

# Styles CSS pour la mise en forme des badges de catégorie.
st.markdown("""
        <style>
        .badge {
            display: inline-block;
            background-color: #4FC3F7;
            color: white;
            padding: 10px 18px;
            border-radius: 12px;
            font-size: 26px;        /* ← Taille du texte augmentée */
            font-weight: bold;
            margin: 8px 0;
            box-shadow: 0 4px 10px rgba(0,0,0,0.25);
        }
        </style>
        """, unsafe_allow_html=True)
    
for cat in categories_selection:

        # Badge visuel pour chaque catégorie de distance.
        st.markdown(
            f"<div class='badge'>🏷️ {cat}</div>", 
            unsafe_allow_html=True
        )

        df_cat_sorted = (
            df_filtre[
                df_filtre["categories_distances"] == cat
                ]
                .sort_values(by="duration_min")
        )

        for i, (_, row) in enumerate(df_cat_sorted.iterrows()):
            
            unique_key = f"{row['activity_id']}_{cat}_{i}"

            # Ajoute un indicateur de meilleure performance dans cette catégorie.
            trophy = (
                " 🏆" 
                if row["activity_id"] == df_cat_sorted.iloc[0]["activity_id"]
                else ""
            )
            bpm = row["average_heartrate"]
            bpm_txt = f"{bpm:.0f} BPM" if pd.notna(bpm) else "—"

            # --- Carte info ---
            # Affiche les principales métriques de la course dans une carte HTML.
            st.markdown(f"""
            <div class="card">
                <strong>{row['start_date_local'].strftime('%Y-%m-%d')}</strong>{trophy}
                Distance : {row['distance_km']:.1f} km
                Allure : {format_pace(row['allure_min_km'])}
                Vitesse : {row['vitesse_kmh']:.2f} km/h
                Cardio : {bpm_txt}
                Temps : {format_duration(row['duration_min'])}
            </div>
            """, unsafe_allow_html=True)

            # --- Graphique ---
            # Représentation visuelle des quatre dimensions principales de performance.
            stats_labels = ["Allure","Vitesse","Cardio","Temps"]
            stats_values = [
                row["allure_min_km"],
                row["vitesse_kmh"],
                bpm if pd.notna(bpm) else 0,
                row["duration_min"]
            ]
            stats_display_values = [
                format_pace(row["allure_min_km"]),
                f"{row['vitesse_kmh']:.2f} km/h",
                bpm_txt,
                format_duration(row["duration_min"]),
            ]

            fig = go.Figure(go.Bar(
                x=stats_values,
                y=stats_labels,
                customdata=stats_display_values,
                hovertemplate="%{y}: %{customdata}<extra></extra>",
                orientation='h',
                marker=dict(color=["#4FC3F7","#81C784","#E57373","#FFD54F"])
            ))

            fig.update_layout(
                height=150,
                margin=dict(l=0,r=0,t=0,b=0),
                template="plotly_dark",
                xaxis=dict(showgrid=False, visible=False),
                yaxis=dict(showgrid=False),
            )

            st.plotly_chart(fig, use_container_width=True,key=f"chart_{unique_key}")


            # --- Bouton prédire ---
            # Envoie l'activité courante vers la page de prédiction météo-performance.
            if st.button(
                "🔮 Prédire",
                key=f"btn_{unique_key}",
                help="Ouvre l'analyse météo et l'estimation pour cette course.",
            ):
                st.session_state["selected_activity"] = row
                st.session_state.page = "prediction"
                st.rerun()

            st.markdown("<hr class='separator'>", unsafe_allow_html=True)


#---------------------
# PAGE PREDICTION
#---------------------
# Écran dédié à l'analyse météo + performance et à la recommandation
# des meilleurs créneaux d'entraînement selon la météo, la distance et
# les conditions de la course sélectionnée.
# Ici, on compare les performances réelles avec un modèle prédictif pour
# estimer l'impact de la météo, puis proposer les meilleures heures pour courir.


import plotly.graph_objects as go

st.title(
    "Coach running",
    icon=":material/directions_run:",
    help="Analyse une course sélectionnée et estime ses performances selon la météo.",
)
    
    # --- Charger GPS ici aussi ---
df, gps = load_data()


    # --- Récupération de l'activité sélectionnée ---
selected_activity = st.session_state.get("selected_activity", None)
if selected_activity is None:
        st.error("Aucune activité sélectionnée depuis la page principale.")
        st.stop()

    # --- Bouton Reset ML ---
    # Permet de réinitialiser les paramètres de prédiction et repartir
    # sur une analyse neuve sans conserver l'ancien état calculé.
if st.button(
    "🔄 Recommencer l'analyse",
    key="btn_reset_ml",
    help="Efface la course sélectionnée pour en choisir une autre.",
):
        st.session_state["selected_activity"] = None
        st.session_state["temp_slider"] = 0
        st.session_state["wind_slider"] = 0
        st.session_state["rh_slider"] = 0
        st.session_state["precip_slider"] = 0
        st.session_state["cloud_slider"] = 0
        st.session_state["ml_reset"] = True
        st.rerun()

if st.session_state.get("ml_reset", False):
        st.info("🔄 ML réinitialisé.")
        st.session_state["ml_reset"] = False
        st.stop()

    # --- Calcul ML ---
    # On utilise le modèle pour prédire la performance sous les conditions
    # météorologiques de l'activité sélectionnée.
st.success(f"Course sélectionnée : {selected_activity['start_date_local']}")

speed_ml, time_ml = predict_time(
        selected_activity["distance_km"],
        selected_activity["temp_mean"],
        selected_activity["rh_mean"],
        selected_activity["precip_mean"],
        selected_activity["cloud_mean"],
        selected_activity["wind_mean"],
        selected_activity["month"],
        selected_activity["hour"],
        selected_activity["total_elevation_gain"]
    )

if is_model_trained_from_data():
    st.info("Modèle entraîné en mémoire à partir de tes activités synchronisées.")

allure_ml = 60 / speed_ml

predicted_time = time_ml
predicted_speed = speed_ml
predicted_allure = 60 / predicted_speed

    # --- Réel ---
real_allure = selected_activity["allure_min_km"]
real_speed = selected_activity["vitesse_kmh"]
real_hr = selected_activity["average_heartrate"]
real_time = selected_activity["duration_min"]

    # --- % variations ---
allure_pct = ((predicted_allure - real_allure) / real_allure) * 100
speed_pct = ((predicted_speed - real_speed) / real_speed) * 100
time_pct = ((predicted_time - real_time) / real_time) * 100

    # -----------------------------
    # AFFICHAGE DES STATS
    # -----------------------------
    # Ici on compare les mesures réelles et les prédictions météo-performance
    # pour quantifier l'impact des conditions sur la sortie.
    # -----------------------------
    # # 📊 DUMBBELL CHART
    # -----------------------------
st.subheader(
    "Comparaison des performances",
    icon=":material/compare_arrows:",
    help="Compare le résultat réel de la course sélectionnée à l'estimation du modèle. L'écart n'isole pas l'effet de la météo.",
)
st.info(
    "Le modèle apprend à partir de courses passées. Ici, il estime uniquement "
    "la course sélectionnée à partir de sa distance, de son dénivelé, du mois, "
    "de l'heure et de la météo enregistrée pendant cette sortie. Ce n'est ni "
    "une moyenne de tes courses, ni une prévision météo pour les prochaines heures. "
    "La durée est calculée à partir de la vitesse estimée.\n\n"
    "**Lire l'écart :** `+` signifie que l'estimation est plus élevée que le "
    "résultat réel. Pour le temps et l'allure, cela signifie plus lent ; pour "
    "la vitesse, plus rapide. Le cardio est mesuré pendant la course, mais "
    "n'est pas prédit par le modèle.",
    title="Comment lire ce tableau",
    icon=":material/info:",
)

compare_df = pd.DataFrame({
        "Indicateur": [
            "Durée totale",
            "Cardio moyen",
            "Vitesse moyenne",
            "Allure moyenne"
        ],

        "Course réelle": [
            format_duration(real_time),
            f"{real_hr:.0f} BPM" if pd.notna(real_hr) else "N/A",
            f"{real_speed:.2f} km/h",
            format_pace(real_allure)
        
        ],

        "Estimation du modèle": [
            format_duration(predicted_time),
            "Non estimé",
            f"{predicted_speed:.2f} km/h",
            format_pace(predicted_allure)
        ],

        "Écart modèle/réel": [
            f"{time_pct:+.1f}%",
            "—",
            f"{speed_pct:+.1f}%",
            f"{allure_pct:+.1f}%"
        ]
})

st.dataframe(
    compare_df,
    width="stretch",
    hide_index=True,
    alt="Comparaison des mesures réelles de la course et des estimations du modèle",
)

    # -----------------------------
    # ÉCART GLOBAL ENTRE LE MODÈLE ET LA COURSE RÉELLE
    # -----------------------------
    
delta_allure = -allure_pct
delta_speed = speed_pct
delta_time = -time_pct

performance_trend = (
        delta_allure * 0.4 +
        delta_speed * 0.3 +
        delta_time * 0.1
    )

color = folium_color(performance_trend)



    # -----------------------------
    # CARTE DE LA COURSE
    # -----------------------------

st.subheader(
    "Parcours de la course",
    icon=":material/map:",
    help="La couleur résume l'écart entre l'estimation du modèle et la course réelle : vert si l'estimation est globalement plus rapide, orange si l'écart est faible, rouge si elle est plus lente. Ce n'est pas une mesure isolée de l'effet météo.",
)
gps_run = gps[gps["activity_id"] == selected_activity["activity_id"]].dropna()
gps_run = gps_run.iloc[::3]
coords = gps_run[["lat", "lon"]].dropna().values.tolist()

if len(coords) < 2:
        st.warning("⚠️ Impossible d'afficher la carte : pas assez de points GPS.")
else:
    
        carte_ml = folium.Map(
            location=[coords[0][0], coords[0][1]],
            zoom_start=13
        )

        for i in range(len(coords) - 1):
            folium.PolyLine(
                [coords[i], coords[i+1]],
                color=color,
                weight=6,
                opacity=0.9
            ).add_to(carte_ml)

        html_ml = carte_ml._repr_html_()
        st.components.v1.html(html_ml, height=600)
 
    # -----------------------------
    # 🏆 MEILLEURE HEURE DU JOUR
    # -----------------------------

# Section dédiée au choix du meilleur créneau pour s'entraîner selon les
# prévisions météo du jour, du lendemain et du surlendemain.
st.subheader(
    "Quand s'entraîner ?",
    icon=":material/schedule:",
    help="Les créneaux sont classés selon la météo prévue. Choisis un jour pour afficher l'estimation correspondante.",
)

lat = selected_activity["lat_start"]
lon = selected_activity["lon_start"]

analysis_now = pd.Timestamp.now(tz="Europe/Paris")
today_str = analysis_now.strftime("%Y-%m-%d")

hours_results = []

# Calcul du score météo pour les heures restantes aujourd'hui.
for hour in range(max(6, analysis_now.hour + 1), 22):

        try:

            meteo_hour = get_meteo(
                lat,
                lon,
                today_str,
                hour,
                df
            )

            speed_pred, time_pred = predict_time(
                selected_activity["distance_km"],
                meteo_hour["temp"],
                meteo_hour["rh"],
                meteo_hour["precip"],
                meteo_hour["cloud"],
                meteo_hour["wind"],
                analysis_now.month,
                hour,
                selected_activity["total_elevation_gain"]
            )

            allure_pred = 60 / speed_pred

            score = 100

            score -= abs(meteo_hour["temp"] - 12) * 2
            score -= meteo_hour["wind"] * 1.5
            score -= meteo_hour["rh"] * 0.3
            score -= meteo_hour["precip"] * 5

            score = max(0, min(100, score))

            hours_results.append({
                "hour": hour,
                "temp": meteo_hour["temp"],
                "wind": meteo_hour["wind"],
                "rh": meteo_hour["rh"],
                "precip": meteo_hour["precip"],
                "cloud": meteo_hour["cloud"],
                "speed": speed_pred,
                "allure": allure_pred,
                "time": time_pred,
                "month": analysis_now.month,
                "score": score
            })

        except Exception as e:
            st.error(f"Heure {hour} : {e}")

    # -----------------------------
    # DATAFRAME
    # -----------------------------

df_hours = pd.DataFrame(hours_results)
best_hour = (
    df_hours.loc[df_hours["score"].idxmax()]
    if not df_hours.empty
    else None
)
        
    # -----------------------------
    # 🗓️ DEMAIN
    # -----------------------------

# Prévisions météo pour le lendemain afin de comparer la qualité des
# conditions à celle du jour actuel.
tomorrow = analysis_now + pd.Timedelta(days=1)
tomorrow_str = tomorrow.strftime("%Y-%m-%d")

hours_tomorrow = []

# Calcul du score météo pour chaque heure du lendemain.
for hour in range(6, 22):

    try:

        meteo_hour = get_meteo(
            lat,
            lon,
            tomorrow_str,
            hour,
            df
        )

        speed_pred, time_pred = predict_time(
            selected_activity["distance_km"],
            meteo_hour["temp"],
            meteo_hour["rh"],
            meteo_hour["precip"],
            meteo_hour["cloud"],
            meteo_hour["wind"],
            tomorrow.month,
            hour,
            selected_activity["total_elevation_gain"]
        )

        score = 100

        score -= abs(meteo_hour["temp"] - 12) * 2
        score -= meteo_hour["wind"] * 1.5
        score -= meteo_hour["rh"] * 0.3
        score -= meteo_hour["precip"] * 5

        score = max(0, min(100, score))
        allure_pred = 60 / speed_pred

        hours_tomorrow.append({
            "hour": hour,
            "temp": meteo_hour["temp"],
            "wind": meteo_hour["wind"],
            "rh": meteo_hour["rh"],
            "precip": meteo_hour["precip"],
            "cloud": meteo_hour["cloud"],
            "speed": speed_pred,
            "allure": allure_pred,
            "time": time_pred,
            "month": tomorrow.month,
            "score": score
        })

    except:
        pass    
        
        
    # -----------------------------
    # DATAFRAME
    # -----------------------------
    
df_tomorrow = pd.DataFrame(hours_tomorrow)
#st.write(df_tomorrow.head()) #Vérifier les valeurs 

best_tomorrow = (
    df_tomorrow.loc[df_tomorrow["score"].idxmax()]
    if not df_tomorrow.empty
    else None
)
        
    # -----------------------------
    # 🗓️ SURLENDEMAIN
    # -----------------------------

# Prévisions météo pour le surlendemain afin d'obtenir une vue sur trois jours.
day_after  = analysis_now + pd.Timedelta(days=2)
day_after_str = day_after.strftime("%Y-%m-%d")

hours_day_after = []

# Calcul du score météo pour chaque heure du surlendemain.
for hour in range(6, 22):

    try:

        meteo_hour = get_meteo(
            lat,
            lon,
            day_after_str,
            hour,
            df
        )

        speed_pred, time_pred = predict_time(
            selected_activity["distance_km"],
            meteo_hour["temp"],
            meteo_hour["rh"],
            meteo_hour["precip"],
            meteo_hour["cloud"],
            meteo_hour["wind"],
            day_after.month,
            hour,
            selected_activity["total_elevation_gain"]
        )

        score = 100

        score -= abs(meteo_hour["temp"] - 12) * 2
        score -= meteo_hour["wind"] * 1.5
        score -= meteo_hour["rh"] * 0.3
        score -= meteo_hour["precip"] * 5

        score = max(0, min(100, score))
        allure_pred = 60 / speed_pred

        hours_day_after.append({
            "hour": hour,
            "temp": meteo_hour["temp"],
            "wind": meteo_hour["wind"],
            "rh": meteo_hour["rh"],
            "precip": meteo_hour["precip"],
            "cloud": meteo_hour["cloud"],
            "speed": speed_pred,
            "allure": allure_pred,
            "time": time_pred,
            "month": day_after.month,
            "score": score
        })

    except:
        continue    
        
        
    # -----------------------------
    # DATAFRAME
    # -----------------------------
    
df_day_after = pd.DataFrame(hours_day_after)
#st.write(df_day_after.head()) #Vérifier les valeurs 

best_day_after = (
    df_day_after.loc[df_day_after["score"].idxmax()]
    if not df_day_after.empty
    else None
)
    # -----------------------------
    # CARTE MEILLEUR JOUR / MEILLEURE HEURE
    # -----------------------------

day_recommendations = [
    ("Aujourd'hui", df_hours, best_hour, "#636EFA"),
    ("Demain", df_tomorrow, best_tomorrow, "#EF553B"),
    ("Après-demain", df_day_after, best_day_after, "#00CC96"),
]

for column, (day_name, _, best_slot, _) in zip(
    st.columns(3), day_recommendations
):
    with column:
        with st.container(border=True):
            st.markdown(f"### {day_name}")
            if best_slot is None:
                st.info("Aucun créneau disponible.")
                continue

            st.markdown(f"**🏆 {int(best_slot['hour']):02d}h00**")
            st.metric("Note météo", f"{best_slot['score']:.1f}/100")
            st.caption(
                f"🌡️ {best_slot['temp']:.1f} °C · "
                f"💨 {best_slot['wind']:.1f} km/h"
            )
            st.caption(f"⚡ {best_slot['speed']:.2f} km/h")

    # La carte et le graphique utilisent le même meilleur point par journée.
available_recommendations = [
    (day_name, best_slot)
    for day_name, _, best_slot, _ in day_recommendations
    if best_slot is not None
]

if available_recommendations:
    winner_day, winner = max(
        available_recommendations,
        key=lambda recommendation: recommendation[1]["score"],
    )
    st.success(
        f"🏆 Meilleure opportunité : {winner_day} "
        f"{int(winner['hour']):02d}h00 · "
        f"Note météo : {winner['score']:.1f}/100"
    )
else:
    st.warning("Aucun créneau météo n'a pu être calculé pour les trois jours.")

# Le graphique affiche les mêmes meilleurs points que les cartes.

fig_compare_days = go.Figure()

for day_name, day_data, best_slot, color in day_recommendations:
    if day_data.empty:
        continue

    fig_compare_days.add_trace(
        go.Scatter(
            x=day_data["hour"],
            y=day_data["score"],
            mode="lines+markers",
            name=day_name,
            line={"color": color},
            marker={"color": color},
            hovertemplate=(
                "%{x}:00<br>Note météo : %{y:.1f}/100"
                "<extra>%{fullData.name}</extra>"
            ),
        )
    )

    if best_slot is not None:
        best_hour_value = int(best_slot["hour"])
        best_score_value = best_slot["score"]
        fig_compare_days.add_trace(
            go.Scatter(
                x=[best_hour_value],
                y=[best_score_value],
                mode="markers+text",
                text=[f"{best_hour_value:02d}h · {best_score_value:.1f}/100"],
                textposition="top center",
                marker={
                    "symbol": "star",
                    "size": 16,
                    "color": color,
                    "line": {"color": "white", "width": 1},
                },
                showlegend=False,
                hovertemplate=(
                    f"{day_name} {best_hour_value:02d}:00"
                    f"<br>Meilleure note : {best_score_value:.1f}/100"
                    "<extra></extra>"
                ),
            )
        )

if best_hour is not None:
    fig_compare_days.add_vline(
        x=analysis_now.hour,
        line_dash="dash",
        line_color="gray",
        annotation_text="Heure d'analyse",
        annotation_position="top",
    )

fig_compare_days.update_layout(
    title="📈 Note météo par heure — étoiles = meilleur créneau",
    template="plotly_dark",
    height=450,
    xaxis_title="Heure",
    yaxis_title="Note météo (/100)",
)

if any(not day_data.empty for _, day_data, _, _ in day_recommendations):
    st.plotly_chart(
        fig_compare_days,
        width="stretch",
    )
else:
    st.info("Aucune donnée météo n'est disponible pour afficher le graphique.")

if available_recommendations:
    recommendation_days = [
        day_name for day_name, _ in available_recommendations
    ]
    if st.session_state.get("selected_training_day") not in recommendation_days:
        st.session_state["selected_training_day"] = winner_day

    selected_training_day = st.segmented_control(
        "Choisir l'entraînement à estimer",
        options=recommendation_days,
        key="selected_training_day",
        help="Choisis aujourd'hui, demain ou après-demain pour voir la projection de course.",
    )

    if selected_training_day is not None:
        selected_slot = next(
            slot
            for day_name, slot in available_recommendations
            if day_name == selected_training_day
        )
        estimated_speed = selected_slot["speed"]
        estimated_time = selected_slot["time"]
        estimated_pace = selected_slot["allure"]

        reference_heartrate = selected_activity["average_heartrate"]
        if pd.notna(reference_heartrate):
            reference_weather_effect = meteo_heart_rate(
                selected_activity["temp_mean"],
                selected_activity["rh_mean"],
                selected_activity["wind_mean"],
            )
            selected_weather_effect = meteo_heart_rate(
                selected_slot["temp"],
                selected_slot["rh"],
                selected_slot["wind"],
            )
            estimated_heartrate = (
                reference_heartrate
                + selected_weather_effect
                - reference_weather_effect
            )
            heartrate_display = f"{estimated_heartrate:.0f}"
        else:
            heartrate_display = "—"

        st.subheader(
            f"Estimation de l'entraînement — {selected_training_day} "
            f"à {int(selected_slot['hour']):02d}h00",
            icon=":material/insights:",
            help="Projection de durée, allure, vitesse et cardio pour la distance de la course sélectionnée.",
        )
        st.caption(
            "Projection indicative du modèle ML pour ta distance habituelle : "
            "la météo est déjà intégrée à la prédiction. La note sert à "
            f"comparer les créneaux ({selected_slot['score']:.1f}/100)."
        )
        st.caption(
            f"Météo : {selected_slot['temp']:.1f} °C · "
            f"humidité {selected_slot['rh']:.0f}% · "
            f"vent {selected_slot['wind']:.1f} km/h · "
            f"pluie {selected_slot['precip']:.1f} mm"
        )

        first_estimate_row = st.columns(3)
        first_estimate_row[0].metric(
            "Distance (km)", f"{selected_activity['distance_km']:.1f}"
        )
        first_estimate_row[1].metric(
            "Durée estimée", format_duration(estimated_time)
        )
        first_estimate_row[2].metric(
            "Allure estimée", format_pace(estimated_pace)
        )

        second_estimate_row = st.columns(3)
        second_estimate_row[0].metric(
            "Vitesse estimée (km/h)", f"{estimated_speed:.1f}"
        )
        second_estimate_row[1].metric(
            "Cardio estimé (BPM)", heartrate_display
        )
        elevation = selected_activity["total_elevation_gain"]
        second_estimate_row[2].metric(
            "Dénivelé (m)", f"{elevation:.0f}" if pd.notna(elevation) else "—"
        )

