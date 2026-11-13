import requests
import streamlit as st

code = input("Collez le code Strava:").strip()

response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": st.secrets["STRAVA_CLIENT_ID"],
        "client_secret": st.secrets["STRAVA_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
    },
)

response.raise_for_status()
tokens = response.json()

print("Nouveau refresh token :")
print(tokens["refresh_token"])
print("Scopes accordés :", tokens.get("scope"))