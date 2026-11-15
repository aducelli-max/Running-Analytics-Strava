import requests
# Dépendances pour les requêtes HTTP et la lecture des secrets Streamlit.
import streamlit as st

def refresh_tokens():
    """
    Rafraîche les tokens Strava (access_token et refresh_token).
    - Charge .env
    - Lit client_id, client_secret, refresh_token
    - Envoie la requête OAuth à Strava
    - Vérifie la réponse
    - Met à jour le refresh_token dans .env
    - Retourne (access_token, refresh_token)
    """

    # Lire les identifiants Strava depuis les secrets de l’application.
    
    client_id = st.secrets["STRAVA_CLIENT_ID"]
    client_secret = st.secrets["STRAVA_CLIENT_SECRET"]
    refresh_token = st.secrets["STRAVA_REFRESH_TOKEN"]

    
    #print("client_id =", client_id)
    #print("client_secret =", client_secret)
    #print("refresh_token =", refresh_token)

    # Vérifier que les identifiants requis sont bien configurés.
    if not client_id or not client_secret or not refresh_token:
        raise ValueError(
        "STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET ou "
        "STRAVA_REFRESH_TOKEN manquant dans .streamlit/secrets.toml"
    )

    # Préparer les paramètres de la demande de renouvellement OAuth.
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    # Envoyer la demande de renouvellement à l’API Strava.
    response = requests.post(url, data=data)

    # Vérifier que l’API a répondu sans erreur HTTP.
    if response.status_code != 200:
        raise RuntimeError(f"Erreur OAuth Strava : {response.status_code} — {response.text}")

    # Convertir la réponse de l’API en objet JSON.
    tokens = response.json()

    # Vérifier la présence des tokens attendus dans la réponse.
    if "access_token" not in tokens or "refresh_token" not in tokens:
        raise KeyError("Réponse Strava invalide : clés manquantes dans le JSON")

    # Extraire les nouveaux tokens reçus de Strava.
    new_access_token = tokens["access_token"]
    new_refresh_token = tokens["refresh_token"]

    # Conserver le refresh token renouvelé pour le renvoyer à l’appelant.
    
    # Renvoyer le token d’accès et le nouveau token de renouvellement.
    return new_access_token, new_refresh_token


