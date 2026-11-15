def meteo_heart_rate(temp, rh, wind):
    """Calcule l'impact de la météo sur le rythme cardiaque.

    La fonction évalue trois facteurs météorologiques :
    - la température : plus il fait chaud, plus le cœur bat vite
    - l'humidité : un air très humide augmente la gêne physiologique
    - le vent : un vent fort a un effet de refroidissement, donc réduit
      l'augmentation estimée du rythme cardiaque

    :param temp: Température en degrés Celsius.
    :param rh: Humidité relative en pourcentage.
    :param wind: Vitesse du vent en km/h.
    :return: Valeur estimée d'augmentation du rythme cardiaque en BPM.
    """
    bpm_increase = 0  # Score cumulatif de l'effet météo sur le rythme cardiaque

    # Température : à partir de 18°C, chaque degré supplémentaire
    # augmente l'effort physiologique estimé de 0,8 BPM.
    if temp > 18:
        bpm_increase += (temp - 18) * 0.8   # +0.8 BPM par degré au-dessus de 18°C

    # Humidité : lorsque l'air est très humide (> 60 %), cela rend
    # la sensation de chaleur plus pénible, donc le rythme cardiaque
    # augmente de 0,15 BPM pour chaque point au-dessus de 60 %.
    if rh > 60:
        bpm_increase += (rh - 60) * 0.15    # +0.15 BPM par % au-dessus de 60%

    # Vent : au-delà de 15 km/h, le vent aide à refroidir le corps,
    # ce qui réduit l'augmentation du rythme cardiaque de 0,3 BPM
    # pour chaque km/h au-dessus de 15.
    if wind > 15:
        bpm_increase -= (wind - 15) * 0.3   # -0.3 BPM par km/h au-dessus de 15 km/h

    return bpm_increase
