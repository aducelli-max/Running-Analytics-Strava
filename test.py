import pandas as pd

# ⚠️ Les fichiers CSV sont dans le dossier "data" du projet.
df_act = pd.read_csv(r"C:/Users/33663/prediction-running/data/activities_with_weather_harmonized.csv")
df_gps = pd.read_csv(r"C:/Users/33663/prediction-running/data/gps_points.csv")

print(df_act[df_act["id"] == 19748296627])
print(df_gps[df_gps["activity_id"] == 19748296627])


df_act[df_act["id"] == 19748296627][["year", "month", "categories_distances"]]
