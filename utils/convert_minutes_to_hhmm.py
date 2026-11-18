
import math


def convert_minutes_to_hhmm(minutes):
    """Convertit un nombre de minutes en chaîne au format « heures h minutes »."""
    # Calcule le nombre d'heures entières.
    heures = int(minutes // 60)
    # Récupère les minutes restantes et les affiche sur deux chiffres.
    mins = int(minutes % 60)
    # Assemble le résultat, par exemple « 125 » devient « 2h05 ».
    return f"{heures}h{mins:02d}"


def format_duration(minutes):
    """Affiche les durées en minutes ou en heures et minutes."""
    try:
        value = float(minutes)
    except (TypeError, ValueError):
        return "—"

    if not math.isfinite(value):
        return "—"

    total_minutes = math.floor(value + 0.5)
    if total_minutes < 60:
        return f"{total_minutes} min"

    hours, remaining_minutes = divmod(total_minutes, 60)
    return f"{hours} h {remaining_minutes:02d} min"


def format_pace(minutes_per_km):
    """Affiche une allure décimale au format minutes:secondes par kilomètre."""
    try:
        value = float(minutes_per_km)
    except (TypeError, ValueError):
        return "—"

    if not math.isfinite(value):
        return "—"

    total_seconds = math.floor(value * 60 + 0.5)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d} min/km"
