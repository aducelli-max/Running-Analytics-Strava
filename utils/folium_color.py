def folium_color(impact):
    """Associe une couleur à l'impact selon son évolution.

    Un impact strictement supérieur à 5 indique une amélioration nette,
    tandis qu'un impact strictement inférieur à -5 indique une dégradation.
    Les valeurs comprises entre ces seuils correspondent à une variation faible.
    """
    if impact > 5:
        return "green"   # Vert : amélioration nette (impact > 5).
    elif impact > -5:
        return "orange"  # Orange : variation faible (-5 <= impact <= 5).
    else:
        return "red"     # Rouge : dégradation (impact <= -5).
