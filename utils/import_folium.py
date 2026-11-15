import folium

# On calcule le centre géographique de la carte en prenant la moyenne
# des latitudes et longitudes des points de départ du DataFrame `df`.
# Les colonnes `start_lat` et `start_lon` doivent donc exister.
center_lat = df["start_lat"].mean()
center_lon = df["start_lon"].mean()

# On crée une carte Folium centrée sur ce point moyen.
# `location` attend une liste de la forme [latitude, longitude].
# `zoom_start=13` donne un niveau de zoom initial assez détaillé.
carte = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=13,
)

# On enregistre la carte sous forme de fichier HTML local.
# Cela permet de la sauvegarder pour une ouverture directe dans un navigateur.
carte.save("ma_carte.html")

# On affiche la carte dans l'application Streamlit.
# `carte._repr_html_()` convertit l'objet Folium en HTML exploitable par Streamlit.
st.components.v1.html(carte._repr_html_(), height=550)
