def pace_color_pct(pct):
    """Retourne la couleur associée à l'évolution du rythme.

    Les seuils sont définis comme suit :
    - pct < -5 : amélioration nette, donc couleur verte
    - -5 <= pct < 5 : variation faible, donc couleur orange
    - pct >= 5 : dégradation nette, donc couleur rouge
    """

    if pct < -5:      # amélioration nette (plus de 5 % d'amélioration)
        return "green"
    elif pct < 5:     # variation faible ou proche de zéro
        return "orange"
    else:             # dégradation nette (au moins 5 % de perte)
        return "red"
