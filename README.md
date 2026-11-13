## Running-Analytics-Strava ![Illustration du projet](./large.jpg)

Application d’analyse de performances de course à pied qui croise tes données Strava avec la météo. Un modèle de machine learning estime l’effet des conditions extérieures sur ta durée de parcours et ta charge physique, puis recommande le meilleur créneau d’entraînement sur les trois prochains jours.

Une même sortie de 10 km ne coûte pas le même effort à 8 °C sans vent qu’à 28 °C avec 70 % d’humidité. 

Les données brutes de Strava ignorent ce contexte ; Le projet le réintroduit.

# Comment ça marche ?

1. Collecte Strava : récupération de l’historique des activités (distance, allure, durée, fréquence cardiaque, dénivelé) via l’API Strava.

2. Collecte météo : températures, vent, humidité et précipitations, passées (pour les sorties déjà réalisées) et prévues (J, J+1, J+2).

3. Modélisation ML : recalcul de la durée de parcours et de l’impact sur les conditions physiques selon la météo.

4. Comparaison : écart entre la donnée d’origine (Strava) et la donnée recalculée.

5. Recommandation : classement des créneaux d’aujourd’hui, demain et après-demain, avec le meilleur moment pour s’entraîner.

Exemple simple :

Aujourd’hui, 17 h : 
26 °C, vent de face → durée estimée +4 min, effort élevé.


Demain, 7 h : 
12 °C, vent faible → durée estimée conforme à l’historique, effort modéré.
Recommandation : demain 7 h.

# Stack : 
- Python/pandas
- API Strava (OAuth 2.0),
- API open-meteo
- scikit-learn
- visualisation (Plotly express)

# Compétences démontrées :
Intégration d’API, nettoyage et fusion de données hétérogènes, feature engineering, modélisation prédictive, comparaison avant/après, restitution orientée décision.
