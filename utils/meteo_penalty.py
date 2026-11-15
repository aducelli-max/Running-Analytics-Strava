

"""Calcule une pénalité météo cumulée à partir de plusieurs conditions.

La fonction attribue une note de pénalité pour chaque facteur météo :
- température : plus il fait chaud, plus la pénalité augmente ;
- humidité relative : une humidité élevée réduit les conditions de confort ;
- vent : un vent fort augmente la pénalité ;
- précipitations : plus il pleut, plus le risque est élevé.

Le résultat final est la somme des pénalités individuelles.
"""


def meteo_penalty(temp, rh, wind, precip):
    """Retourne une pénalité globale selon les conditions météorologiques.

    Args:
        temp (float): Température en °C.
        rh (float): Humidité relative en %.
        wind (float): Vitesse du vent en km/h.
        precip (float): Quantité de pluie en mm.

    Returns:
        int: Somme des pénalités calculées pour la température, l'humidité,
             le vent et les précipitations.
    """

    # Température : la pénalité augmente avec la chaleur.
    if temp <= 10:
        pen_temp = 0      # Très frais / favorable
    elif temp <= 20:
        pen_temp = 2      # Température acceptable
    elif temp <= 25:
        pen_temp = 5      # Chaud mais tolérable
    elif temp <= 30:
        pen_temp = 10     # Très chaud
    else:
        pen_temp = 15     # Extrêmement chaud

    # Humidité : l'air est plus désagréable lorsque l'humidité est élevée.
    if rh <= 50:
        pen_rh = 0        # Air sec / confortable
    elif rh <= 70:
        pen_rh = 2        # Humidité modérée
    elif rh <= 85:
        pen_rh = 4        # Humidité élevée
    else:
        pen_rh = 6        # Humidité très élevée

    # Vent : un vent plus fort ajoute une pénalité plus importante.
    if wind <= 5:
        pen_wind = 0      # Vent faible / calme
    elif wind <= 10:
        pen_wind = 2      # Vent léger
    elif wind <= 20:
        pen_wind = 6      # Vent fort
    else:
        pen_wind = 12     # Vent très fort

    # Pluie : plus les précipitations sont importantes, plus la pénalité croit.
    if precip <= 1:
        pen_precip = 0    # Pas de pluie / très faible pluie
    elif precip <= 3:
        pen_precip = 3    # Pluie légère
    elif precip <= 7:
        pen_precip = 6    # Pluie modérée
    else:
        pen_precip = 10   # Forte pluie

    # La pénalité totale est la somme des éléments individuels.
    return pen_temp + pen_rh + pen_wind + pen_precip

