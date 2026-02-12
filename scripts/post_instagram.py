import os
import json
import requests
import subprocess

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")

COUNTER_FILE = "post_counter.json"

# 1. Ler contador atual
with open(COUNTER_FILE, "r") as f:
    data = json.load(f)

current_count = data.get("count", 0) + 1

caption = f"""Dia {current_count}

Comendo um docinho 🍬
"""

# 2. Criar container de mídia
media_url = f"https://graph.facebook.com/v24.0/{IG_USER_ID}/media"
media_payload = {
    "image_url": IMAGE_URL,
    "caption": caption,
    "access_token": ACCESS_TOKEN
}

media_response = requests.post(media_url, data=media_payload)
media_response.raise_for_status()

creation_id = media_response.json()["id"]

# 3. Publicar
publish_url = f"https://graph.facebook.com/v24.0/{IG_USER_ID}/media_publish"
publish_payload = {
    "creation_id": creation_id,
    "access_token": ACCESS_TOKEN
}

publish_response = requests.post(publish_url, data=publish_payload)
publish_response.raise_for_status()

# 4. Atualizar contador
data["count"] = current_count
with open(COUNTER_FILE, "w") as f:
    json.dump(data, f, indent=2)

# 5. Commit automático do contador
subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
subprocess.run(["git", "add", COUNTER_FILE], check=True)
subprocess.run(
    ["git", "commit", "-m", f"chore: contador Instagram dia {current_count}"],
    check=True
)
subprocess.run(["git", "push"], check=True)

print(f"Post do Dia {current_count} publicado com sucesso.")
