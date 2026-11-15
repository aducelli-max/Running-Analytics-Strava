

import pandas as pd  # Importe pandas pour lire et manipuler les données sous forme de tableaux.

# Charge les fichiers CSV du dossier « data » dans des DataFrames pandas.
# Le préfixe r indique une chaîne brute, pratique pour écrire des chemins de fichiers.
df_act = pd.read_csv(
	r"C:/Users/33663/prediction-running/data/activities_with_weather_harmonized.csv"
)
df_gps = pd.read_csv(r"C:/Users/33663/prediction-running/data/gps_points.csv")

# Sélectionne puis affiche la ligne d'activité ayant l'identifiant indiqué.
print(df_act[df_act["id"] == 19748296627])

# Sélectionne puis affiche les points GPS rattachés à cette activité.
print(df_gps[df_gps["activity_id"] == 19748296627])

# Garde uniquement l'année, le mois et les distances par catégorie pour cette activité.
# Dans un script Python, ajoutez print(...) autour de cette expression pour afficher le résultat.
df_act[df_act["id"] == 19748296627][["year", "month", "categories_distances"]]
