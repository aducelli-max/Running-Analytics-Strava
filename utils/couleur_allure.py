def couleur_allure(p):
    """Retourne une couleur selon la valeur de l'allure `p`.

    Vert pour une valeur inférieure à 5, orange pour une valeur de 5
    à moins de 6, et rouge à partir de 6.
    """
    if p < 5:
        return "green"  # Allure rapide : vert.
    elif p < 6:
        return "orange"  # Valeur intermédiaire : orange.
    else:
        return "red"  # Valeur égale ou supérieure à 6 : rouge.
