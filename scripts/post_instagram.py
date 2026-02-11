import os
import requests
import subprocess

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")
BRANCH = os.getenv("GITHUB_REF_NAME")

# Contador baseado no Git
commit_count = subprocess.check_output(
    ["git", "rev-list", "--count", "HEAD"]
).decode().strip()

caption = f"""🚀 Commit #{commit_count}

Atualização na branch: {BRANCH}
Projeto GEPETECO
"""

# 1. Criar container de mídia
media_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
media_payload = {
    "image_url": IMAGE_URL,
    "caption": caption,
    "access_token": ACCESS_TOKEN
}

media_response = requests.post(media_url, data=media_payload)
media_response.raise_for_status()
creation_id = media_response.json()["id"]

# 2. Publicar
publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
publish_payload = {
    "creation_id": creation_id,
    "access_token": ACCESS_TOKEN
}

publish_response = requests.post(publish_url, data=publish_payload)
publish_response.raise_for_status()

print("Post publicado com sucesso.")
