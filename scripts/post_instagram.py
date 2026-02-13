import os
import json
import time
import requests
import subprocess

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")

COUNTER_FILE = "post_counter.json"

# 1. Ler contador
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

if media_response.status_code != 200:
    print("Erro ao criar mídia:")
    print(media_response.text)
    media_response.raise_for_status()

creation_id = media_response.json()["id"]
print("Container criado:", creation_id)

# 3. Aguardar processamento
status_url = f"https://graph.facebook.com/v24.0/{creation_id}"
status_params = {
    "fields": "status_code",
    "access_token": ACCESS_TOKEN
}

for attempt in range(1, 11):
    status_response = requests.get(status_url, params=status_params)
    status = status_response.json().get("status_code")

    print(f"Tentativa {attempt} - status da mídia: {status}")

    if status == "FINISHED":
        break
    if status == "ERROR":
        raise RuntimeError("Erro no processamento da mídia")

    time.sleep(3)
else:
    raise TimeoutError("Timeout aguardando a mídia ficar pronta")

# 4. Publicar
publish_url = f"https://graph.facebook.com/v24.0/{IG_USER_ID}/media_publish"
publish_payload = {
    "creation_id": creation_id,
    "access_token": ACCESS_TOKEN
}

publish_response = requests.post(publish_url, data=publish_payload)

if publish_response.status_code != 200:
    print("Erro ao publicar mídia:")
    print(publish_response.text)
    publish_response.raise_for_status()

# 5. Atualizar contador
data["count"] = current_count
with open(COUNTER_FILE, "w") as f:
    json.dump(data, f, indent=2)

# 6. Commit automático
subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
subprocess.run(["git", "add", COUNTER_FILE], check=True)

commit = subprocess.run(
    ["git", "commit", "-m", f"chore: contador Instagram dia {current_count}"],
    capture_output=True,
    text=True
)

if commit.returncode == 0:
    subprocess.run(["git", "push"], check=True)
else:
    print("Nada para commitar")

print(f"Post do Dia {current_count} publicado com sucesso.")
