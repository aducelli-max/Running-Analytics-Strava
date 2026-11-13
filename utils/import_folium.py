import folium

center_lat = df["start_lat"].mean()
center_lon = df["start_lon"].mean()

carte = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=13,
)

carte.save("ma_carte.html")
st.components.v1.html(carte._repr_html_(), height=550)
