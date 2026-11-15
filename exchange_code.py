

"""Échange un code d'autorisation Strava contre des jetons OAuth."""

# Bibliothèque utilisée pour envoyer la requête HTTP à Strava.
import requests
# Streamlit donne accès aux identifiants configurés dans les secrets de l'application.
import streamlit as st

# Demande le code fourni par Strava et enlève les espaces superflus.
code = input("Collez le code Strava:").strip()

# Envoie le code et les identifiants de l'application à l'API OAuth de Strava.
# Le type de grant précise que le code d'autorisation est échangé contre des jetons.
response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": st.secrets["STRAVA_CLIENT_ID"],
        "client_secret": st.secrets["STRAVA_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
    },
)

# Déclenche une erreur si la requête a échoué (code invalide, identifiants incorrects, etc.).
response.raise_for_status()
# Décode la réponse JSON en dictionnaire Python.
tokens = response.json()

# Affiche le refresh token, qui permet de demander ultérieurement de nouveaux jetons.
print("Nouveau refresh token :")
print(tokens["refresh_token"])
# Affiche les permissions accordées par Strava, si la réponse les contient.
print("Scopes accordés :", tokens.get("scope"))