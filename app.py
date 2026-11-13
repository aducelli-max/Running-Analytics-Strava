from altair import Color
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time
import plotly.graph_objects as go
import numpy as np

from ml.utils_ml import predict_time
from utils.couleur_allure import couleur_allure
from utils.meteo_penalty import meteo_penalty
from utils.meteo_heart_rate import meteo_heart_rate
from utils.color_pct import color_pct
from utils.folium_color import folium_color
from utils.meteo import get_meteo
from utils.strava_sync import main


# ---------------------
# INITIALISATION SESSION
# ---------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_activity" not in st.session_state:
    st.session_state.selected_activity = None

# ---------------------
# PAGE 1 — ACCUEIL
# ---------------------
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



    # --- Boutons d'action ---
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Mise à jour"):
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
                st.success("✔️ Mise à jour terminée !")
                st.write(f"📊 Total activités : {len(df_updated)}"
                )
                time.sleep(1)
                
                st.rerun()

    with col2:
        uploaded_gpx = st.file_uploader("📥 Import GPX", type=["gpx"])
        if uploaded_gpx is not None:
            st.write("GPX reçu, traitement en cours...")


# ---------------------
# CHARGEMENT DES DONNÉES
# ---------------------

@st.cache_data
def load_data():

    df = pd.read_csv(
        "data/activities_with_weather_harmonized.csv"
    
    )

    df = df[df["sport_type"] == "Run"].copy()

    df["start_date"] = pd.to_datetime(
        df["start_date"],
        utc=True
    )

    df["start_date_local"] = pd.to_datetime(
        df["start_date_local"],
        utc=True
    )

    df["allure_min_km"] = (
        pd.to_numeric(
            df["allure_min_km"],
            errors="coerce"
        )
        .replace([np.inf, -np.inf], np.nan)
    )

    gps = pd.read_csv(
        "data/gps_points.csv"
    )

    return df, gps


# APPEL DE LA FONCTION
df, gps = load_data()
if df.empty:
    st.error("Le dataframe df est vide")
    st.stop()

if gps.empty:
    st.error("Le dataframe gps est vide")
    st.stop()
    
    
# ---------------------
# BARRE LATERAL : MÉTÉO DU JOUR & STATISTIQUES PERSO
# ---------------------
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

meteo_today = get_meteo(lat, lon, date_str, hour_now, df)

st.sidebar.title("🌦️ La météo du jour")
st.sidebar.write(f"**🌡️ Température :** {meteo_today['temp']} °C")
st.sidebar.write(f"**💨 Vent :** {meteo_today['wind']} km/h")
st.sidebar.write(f"**💧 Humidité :** {meteo_today['rh']} %")
st.sidebar.write(f"**🌧️ Précipitations :** {meteo_today['precip']} mm")
st.sidebar.write(f"**☁️ Nuages :** {meteo_today['cloud']} %")

st.sidebar.title("📈📉  Stats' globales : ")
    
st.sidebar.write(f"**📏 Distance moy. :** {df["distance_km"].mean():.2f} km")
st.sidebar.write(f"**⌛ Durée moy. :** {df["duration_min"].mean():.1f} Min")
st.sidebar.write(f"⏱️ **Allure moy. :** {df['allure_min_km'].mean():.2f} min/km")   
st.sidebar.write(f"**🏃Vitesse moy. :** {df['vitesse_kmh'].mean():.1f} km/h")
st.sidebar.write(f"**💪Score d'effort moy. :** {df['suffer_score'].mean():.1f}")
st.sidebar.write(f"**⚡Dénivelé moy. :** {df['total_elevation_gain'].mean():.1f} M")
    
st.sidebar.write(f"**💓 Cardio moy. :** {df["average_heartrate"].mean():.2f} Bpm")
    
st.sidebar.write(f"**🏁 Activités :** {df['activity_id'].count()} sorties") 
        
    

    # ---------------------
    # FILTRES ANNÉE / MOIS / CATÉGORIES
    # ---------------------
df_cat = df.copy()
last_activity = df_cat.sort_values(by="start_date_local", ascending=False).iloc[0]
default_year = int(last_activity["year"])
default_month = int(last_activity["month"])

annees_disponibles = sorted(df_cat["year"].unique())
annee = st.selectbox("Choisir l'année :", annees_disponibles,
                         index=annees_disponibles.index(default_year))

mois_noms = {
        1:"Janvier",2:"Février",3:"Mars",4:"Avril",5:"Mai",6:"Juin",
        7:"Juillet",8:"Août",9:"Septembre",10:"Octobre",11:"Novembre",12:"Décembre"
    }

mois_dispo_num = sorted(df_cat[df_cat["year"] == annee]["month"].unique())
mois_nom = st.selectbox("Choisir le mois :", [mois_noms[m] for m in mois_dispo_num],
                            index=mois_dispo_num.index(default_month))
mois_num = [k for k,v in mois_noms.items() if v == mois_nom][0]

df_filtre = df_cat[(df_cat["year"] == annee) & (df_cat["month"] == mois_num)]
categories_dispo = sorted(df_filtre["categories_distances"].unique())
categories_selection = st.multiselect("Choisir les catégories :", categories_dispo,
                                          default=categories_dispo)

df_filtre = df_filtre[df_filtre["categories_distances"].isin(categories_selection)]

st.subheader("🗺️ Parcours du mois sélectionné")
    
    # ---------------------
    # SÉCURITÉ : AUCUNE ACTIVITÉ
    # ---------------------
    
if df_filtre.empty:
        st.warning("⚠️ Aucune activité pour ce mois")
        st.stop()
        
    # ---------------------
    # SÉCURITÉ : COORDONNÉES INVALIDES
    # ---------------------
    
lat0 = df_filtre.iloc[0]["lat_start"]
lon0 = df_filtre.iloc[0]["lon_start"]

if pd.isna(lat0) or pd.isna(lon0):
        st.warning("⚠️ Aucun élément pour cette catégorie")
        st.stop()
       

    # ---------------------
    # CARTE CENTRÉE SUR LA PREMIÈRE ACTIVITÉ
    # ---------------------
carte = folium.Map(
        location=[df_filtre.iloc[0]["lat_start"], df_filtre.iloc[0]["lon_start"]],
        zoom_start=13
    )

    # -----------------------------
    # AFFICHAGE DE TOUS LES PARCOURS
    # -----------------------------
for activity_id in df_filtre["activity_id"].unique():

        gps_run = (
            gps[gps["activity_id"] == activity_id]
            .dropna(subset=["lat", "lon"])
            .copy()
        )

        if len(gps_run) < 2:
            continue

        gps_run = gps_run.iloc[::3].copy()

    # Pour les parcours très courts
        if len(gps_run) < 2:
            continue

        gps_run["pace"] = (1000 / gps_run["velocity"]) / 60
        coords = gps_run[["lat", "lon"]].values.tolist()

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
            popup=str(activity_id),
            icon=folium.Icon(icon="play")
        ).add_to(carte)

        folium.Marker(
            coords[-1],
            popup=str(activity_id),
            icon=folium.Icon(color='black', icon="flag-checkered", prefix="fa")
        ).add_to(carte)

    # -----------------------------
    # ZOOM AUTOMATIQUE SUR TOUTES LES COURSES
    # -----------------------------
gps_all = gps[gps["activity_id"].isin(df_filtre["activity_id"])
    ].dropna(subset=["lat", "lon"])

if not gps_all.empty:
        min_lat = gps_all["lat"].min()
        max_lat = gps_all["lat"].max()
        min_lon = gps_all["lon"].min()
        max_lon = gps_all["lon"].max()

        carte.fit_bounds(
            [[min_lat, min_lon], 
             [max_lat, max_lon]])

    # --- Affichage Folium ---
        map_data = st_folium(
            carte, 
            height=600, 
            width=900
        )

    # --- Clic sur un marker → sélection pour prédiction ---
if map_data and "last_object_clicked" in map_data:
            
        clicked = map_data["last_object_clicked"]
            
        if clicked and "popup" in clicked:
            
            activity_clicked = int(clicked["popup"])
            
            st.session_state["selected_activity"] = df_filtre[df_filtre["activity_id"] == activity_clicked].iloc[0]
            st.session_state.page = "prediction"
            st.rerun()

    # -----------------------------
    # COURSES DU MOIS
    # -----------------------------
st.subheader("📅 Courses du mois")

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

            trophy = (
                " 🏆" 
                if row["activity_id"] == df_cat_sorted.iloc[0]["activity_id"]
                else ""
            )
            bpm = row["average_heartrate"]
            bpm_txt = f"{bpm:.0f} BPM" if pd.notna(bpm) else "—"

            # --- Carte info ---
            st.markdown(f"""
            <div class="card">
                <strong>{row['start_date_local'].strftime('%Y-%m-%d')}</strong>{trophy}
                Distance : {row['distance_km']:.1f} km
                Allure : {row['allure_min_km']:.2f} min/km
                Vitesse : {row['vitesse_kmh']:.2f} km/h
                Cardio : {bpm_txt}
                Temps : {row['duration_min']:.1f} min
            </div>
            """, unsafe_allow_html=True)

            # --- Graphique ---
            stats_labels = ["Allure","Vitesse","Cardio","Temps"]
            stats_values = [
                row["allure_min_km"],
                row["vitesse_kmh"],
                bpm if pd.notna(bpm) else 0,
                row["duration_min"]
            ]

            fig = go.Figure(go.Bar(
                x=stats_values,
                y=stats_labels,
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
            if st.button("🔮 Prédire", key=f"btn_{unique_key}"):
                st.session_state["selected_activity"] = row
                st.session_state.page = "prediction"
                st.rerun()

            st.markdown("<hr class='separator'>", unsafe_allow_html=True)


    #---------------------
    # PAGE PREDICTION
    #---------------------


if st.session_state.page == "prediction":
    
        def get_coach_phrase(score_meteo):
            if score_meteo >= 80:
                return """
            Conditions idéales pour performer.
            La météo te porte, ton corps va répondre, et le terrain est avec toi.
            C’est le moment de dérouler une foulée propre, régulière, ambitieuse.
            Reste fluide, respire, et laisse la mécanique faire le travail.
            Aujourd’hui, tu peux viser un chrono solide sans te mettre en danger.
            """, "#00FFAA", "🟢 Conditions parfaites"
        
            elif score_meteo >= 60:
                return """
            Conditions correctes, rien d’alarmant.
            Tu peux faire une bonne course, mais la clé sera la gestion.
            Ne pars pas trop vite, installe ton rythme, reste concentré.
            La météo ne t’aide pas, mais elle ne te pénalise pas non plus.
            Ton mental fera la différence : reste propre, reste lucide.
            """, "#4FC3F7", "🔵 Conditions correctes"
        
            elif score_meteo >= 40:
                return """
            Météo exigeante, il va falloir courir avec la tête.
            Adapte ton allure, protège ton cardio, surveille ton souffle.
            Les conditions vont te tester : vise la régularité plutôt que la vitesse.
            C’est une course de maîtrise, pas de bravoure.
            Reste solide, reste stable, et tu traverseras cette zone sans te cramer.
            """, "#FFD54F", "🟡 Conditions difficiles"
        
            else:
                return """
            Météo hostile : adapte tout, allure, respiration, ambition.
            Aujourd’hui, l’objectif n’est pas le chrono, mais la résistance.
            Chaque kilomètre est un combat, avance avec humilité.
            Protège ton corps, garde la tête froide, et reste maître de ton effort.
            C’est une course de survivant : tu t’adaptes, tu encaisses, tu progresses.
        """, "#FF0080", "🔴 Conditions extrêmes"


import plotly.graph_objects as go

st.title("🤖 Coach Running IAnalyse :")
    
    # --- Charger GPS ici aussi ---
df, gps = load_data()


    # --- Récupération de l'activité sélectionnée ---
selected_activity = st.session_state.get("selected_activity", None)
if selected_activity is None:
        st.error("Aucune activité sélectionnée depuis la page principale.")
        st.stop()

    # --- Bouton Reset ML ---
if st.button("🔄 Reset ML", key="btn_reset_ml"):
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

allure_ml = 60 / speed_ml
bpm_increase = meteo_heart_rate(
        selected_activity["temp_mean"],
        selected_activity["rh_mean"],
        selected_activity["wind_mean"]
    )

heartrate_ml = selected_activity["average_heartrate"] - bpm_increase
corrected_hr = heartrate_ml + bpm_increase

penalty = meteo_penalty(
        selected_activity["temp_mean"],
        selected_activity["rh_mean"],
        selected_activity["wind_mean"],
        selected_activity["precip_mean"]
    )

corrected_time = time_ml * (1 + penalty / 100)
corrected_speed = speed_ml * (1 - penalty / 100)
corrected_allure = 60 / corrected_speed

    # --- Réel ---
real_allure = selected_activity["allure_min_km"]
real_speed = selected_activity["vitesse_kmh"]
real_hr = selected_activity["average_heartrate"]
real_time = selected_activity["duration_min"]

    # --- % variations ---
allure_pct = ((corrected_allure - real_allure) / real_allure) * 100
speed_pct = ((corrected_speed - real_speed) / real_speed) * 100
hr_pct = ((corrected_hr - real_hr) / real_hr) * 100 if pd.notna(real_hr) else 0
time_pct = ((corrected_time - real_time) / real_time) * 100

    # -----------------------------
    # AFFICHAGE DES STATS
    # -----------------------------
    # -----------------------------
    # # 📊 DUMBBELL CHART
    # -----------------------------
st.subheader("📊 Comparaison des performances")
    
def format_duration(mins):
        total_seconds = int(mins * 60)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
        else:
            return f"{minutes:02d}m {seconds:02d}s"

compare_df = pd.DataFrame({
        "Métriques": [
            "⏱️ Temps",
            "❤️ Cardio",
            "🏃 Vitesse",
            "⚡ Allure"
        ],

        "Réel": [
            format_duration(real_time),
            f"{real_hr:.0f} BPM" if pd.notna(real_hr) else "N/A",
            f"{real_speed:.2f} km/h",
            f"{real_allure:.2f} min/km"
        
        ],

        "Prévision": [
            format_duration(corrected_time),
            f"{corrected_hr:.0f} BPM" if pd.notna(corrected_hr) else "N/A",
            f"{corrected_speed:.2f} km/h",
            f"{corrected_allure:.2f} min/km"
        ],

        "Impact météo": [
            f"{time_pct:+.1f}%",
            f"{hr_pct:+.1f}%" if pd.notna(hr_pct) else "N/A",
            f"{speed_pct:+.1f}%",
            f"{allure_pct:+.1f}%"
        ]
})

st.dataframe(
    compare_df,
    use_container_width=True,
    hide_index=True
    )  

    # -----------------------------
    # IMPACT MÉTÉO
    # -----------------------------
    
delta_allure = -allure_pct
delta_speed = speed_pct
delta_hr = -hr_pct
delta_time = -time_pct

impact_meteo = (
        delta_allure * 0.4 +
        delta_speed * 0.3 +
        delta_hr * 0.2 +
        delta_time * 0.1
    )
score_meteo = max(0, min(100, abs(impact_meteo)))

color = folium_color(impact_meteo)



    # -----------------------------
    # CARTE ML
    # -----------------------------

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

st.subheader("❓Quand s'entrainer ❓")

lat = selected_activity["lat_start"]
lon = selected_activity["lon_start"]

today_str = datetime.now().strftime("%Y-%m-%d")

hours_results = []

for hour in range(6, 22):

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
                datetime.now().month,
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
                "speed": speed_pred,
                "allure": allure_pred,
                "time": time_pred,
                "score": score
            })

        except Exception as e:
            st.error(f"Heure {hour} : {e}")

    # -----------------------------
    # DATAFRAME
    # -----------------------------

df_hours = pd.DataFrame(hours_results)

if not df_hours.empty:

        best_hour = df_hours.loc[
            df_hours["speed"].idxmax()
        ]
        
    # -----------------------------
    # 🗓️ DEMAIN
    # -----------------------------

tomorrow = datetime.now() + pd.Timedelta(days=1)
tomorrow_str = tomorrow.strftime("%Y-%m-%d")

hours_tomorrow = []

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

        hours_tomorrow.append({
            "hour": hour,
            "temp": meteo_hour["temp"],
            "wind": meteo_hour["wind"],
            "rh": meteo_hour["rh"],
            "speed": speed_pred,
            "score": score
        })

    except:
        pass    
        
        
    # -----------------------------
    # DATAFRAME
    # -----------------------------
    
df_tomorrow = pd.DataFrame(hours_tomorrow)
#st.write(df_tomorrow.head()) #Vérifier les valeurs 

if not df_tomorrow.empty:

        best_tomorrow = df_tomorrow.loc[
        df_tomorrow["score"].idxmax()
    ]   
        
    # -----------------------------
    # 🗓️ SURLENDEMAIN
    # -----------------------------

day_after  = datetime.now() + pd.Timedelta(days=2)
day_after_str = day_after.strftime("%Y-%m-%d")

hours_day_after = []

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

        hours_day_after.append({
            "hour": hour,
            "temp": meteo_hour["temp"],
            "wind": meteo_hour["wind"],
            "rh": meteo_hour["rh"],
            "speed": speed_pred,
            "score": score
        })

    except:
        continue    
        
        
    # -----------------------------
    # DATAFRAME
    # -----------------------------
    
df_day_after = pd.DataFrame(hours_day_after)
#st.write(df_day_after.head()) #Vérifier les valeurs 

if not df_day_after.empty:

        best_day_after = df_day_after.loc[
        df_day_after["score"].idxmax()
    ]
    # -----------------------------
    # CARTE MEILLEUR JOUR / MEILLEURE HEURE
    # -----------------------------

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(f"""
### Aujourd'hui

🏆 {int(best_hour['hour'])}h00

🌡️ {best_hour['temp']:.1f}°C

💨 {best_hour['wind']:.1f} km/h

⚡ {best_hour['speed']:.2f} km/h

🎯 {best_hour['score']:.2f}/100
""")

with col2:

    st.markdown(f"""
### Demain

🏆 {int(best_tomorrow['hour'])}h00

🌡️ {best_tomorrow['temp']:.1f}°C

💨 {best_tomorrow['wind']:.1f} km/h

⚡ {best_tomorrow['speed']:.2f} km/h

🎯 {best_tomorrow['score']:.2f}/100
""")
    
with col3:

    st.markdown(f"""
### Après-demain

🏆 {int(best_day_after['hour'])}h00

🌡️ {best_day_after['temp']:.1f}°C

💨 {best_day_after['wind']:.1f} km/h

⚡ {best_day_after['speed']:.2f} km/h

🎯 {best_day_after['score']:.2f}/100
""")

    # -----------------------------
    # TOP 3 DES HEURES
    # -----------------------------
ranking = pd.DataFrame([
    {
        "jour": "Aujourd'hui",
        "heure": int(best_hour["hour"]),
        "score": best_hour["score"]
    },
    {
        "jour": "Demain",
        "heure": int(best_tomorrow["hour"]),
        "score": best_tomorrow["score"]
    },
    {
        "jour": "Surlendemain",
        "heure": int(best_day_after["hour"]),
        "score": best_day_after["score"]
    }
])

winner = ranking.loc[
    ranking["score"].idxmax()
]

st.success(
    f"""
🏆 Meilleure opportunité d'entraînement : {winner['jour']} {winner['heure']}h00

🎯 Score météo : {winner['score']:.2f}/100

"""
)


    # -----------------------------
    # GRAPHIQUE
    # -----------------------------

fig_compare_days = go.Figure()

fig_compare_days.add_trace(
    go.Scatter(
        x=df_hours["hour"],
        y=df_hours["score"],
        mode="lines+markers",
        name="Aujourd'hui"
    )
)

fig_compare_days.add_trace(
    go.Scatter(
        x=df_tomorrow["hour"],
        y=df_tomorrow["score"],
        mode="lines+markers",
        name="Demain"
    )
)

fig_compare_days.add_trace(
    go.Scatter(
        x=df_day_after["hour"],
        y=df_day_after["score"],
        mode="lines+markers",
        name="Surlendemain"
    )
)

fig_compare_days.update_layout(
    title="📈 Qualité des conditions sur 3 jours",
    template="plotly_dark",
    height=450,
    xaxis_title="Heure",
    yaxis_title="Score météo"
)

st.plotly_chart(
    fig_compare_days,
    width="stretch"
)
        



# pour lancer streamlit : streamlit run app.py