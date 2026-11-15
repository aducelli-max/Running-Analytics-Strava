import requests


client_id = "260547"
client_secret = "8d62dc9b4357bcdf5adf17514fea0ef46e995685"
code = "3ac8e1dcea5311beb87a3d4373febc7b5e9cb04f"

response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": client_id,  # Identifiant de l'application Strava.
        "client_secret": client_secret,  # Clé secrète de l'application.
        "code": code,  # Code que Strava échange contre un jeton.
        "grant_type": "authorization_code",  # Type d'échange OAuth demandé.
    }
)

# Convertit la réponse JSON en objet Python (généralement un dictionnaire)
# puis l'affiche, notamment pour examiner les jetons retournés.
print(response.json())
