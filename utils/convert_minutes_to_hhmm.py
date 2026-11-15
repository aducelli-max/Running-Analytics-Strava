
def convert_minutes_to_hhmm(minutes):
    """Convertit un nombre de minutes en chaîne au format « heures h minutes »."""
    # Calcule le nombre d'heures entières.
    heures = int(minutes // 60)
    # Récupère les minutes restantes et les affiche sur deux chiffres.
    mins = int(minutes % 60)
    # Assemble le résultat, par exemple « 125 » devient « 2h05 ».
    return f"{heures}h{mins:02d}"
