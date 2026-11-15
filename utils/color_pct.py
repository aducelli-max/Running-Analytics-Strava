def color_pct(value, metric):
    # Formate un pourcentage en HTML avec une couleur indiquant si le résultat est favorable.
    """
    metric ∈ {"allure", "vitesse", "cardio", "temps"}
    """

    # Cas neutre : une variation inférieure à 0,1 % en valeur absolue est affichée en gris.
    if abs(value) < 0.1:
        return f"<span style='color:#cccccc;'>**{value:+.1f}%**</span>"

    # Pour ces métriques, une diminution de la valeur représente une amélioration.
    better_if_lower = ["allure", "cardio", "temps"]
    # Pour la vitesse, une augmentation de la valeur représente une amélioration.
    better_if_higher = ["vitesse"]

    # Évalue les métriques où une valeur plus faible est préférable : négatif en vert, positif en rouge.
    if metric in better_if_lower:
        if value < 0:
            return f"<span style='color:green;'>**{value:+.1f}%**</span>"
        else:
            return f"<span style='color:red;'>**{value:+.1f}%**</span>"

    # Évalue les métriques où une valeur plus élevée est préférable : positif en vert, négatif en rouge.
    if metric in better_if_higher:
        if value > 0:
            return f"<span style='color:green;'>**{value:+.1f}%**</span>"
        else:
            return f"<span style='color:red;'>**{value:+.1f}%**</span>"
