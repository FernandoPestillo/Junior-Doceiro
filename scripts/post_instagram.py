import os
import json
import time
import requests
import subprocess

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
BASE_IMAGE_URL = os.getenv("IMAGE_URL") # URL base (ex: .../images/)

COUNTER_FILE = "post_counter.json"

# --- CONFIGURAÇÃO DE DIAS ESPECIAIS ---
# Mapeia o dia -> (nome_do_arquivo, legenda_especial)
SPECIAL_DAYS = {
    10: ("post_10.jpg", "🎉 Marco de 10 dias! Sextou com Docinho."),
    25: ("post_25.jpg", "🌟 25 dias de foco e doçura!"),
    75: ("post_75.jpg", "💎 75 dias! Quase no centenário."),
    100: ("post_100.jpg", "🏆 CENTESIMOU! 100 dias comendo um docinho.")
}

# 1. Ler contador
if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"count": 0}, f)

with open(COUNTER_FILE, "r") as f:
    data = json.load(f)

current_count = data.get("count", 0) + 1

# --- LÓGICA DE SELEÇÃO DE MÍDIA ---
if current_count in SPECIAL_DAYS:
    file_name, special_caption = SPECIAL_DAYS[current_count]
    # Assume que suas fotos especiais estão no mesmo diretório/URL
    # Se BASE_IMAGE_URL terminar em 'post.jpg', precisamos trocar pelo file_name
    image_url = BASE_IMAGE_URL.replace("post.jpg", file_name)
    caption = f"Dia {current_count}\n\n{special_caption}"
else:
    image_url = BASE_IMAGE_URL
    caption = f"Dia {current_count}\n\nComendo um docinho 🍬"

# 2. Criar container de mídia
media_url = f"https://graph.facebook.com/v25.0/{IG_USER_ID}/media"
media_payload = {
    "image_url": image_url,
    "caption": caption,
    "access_token": ACCESS_TOKEN
}

media_response = requests.post(media_url, data=media_payload)

if media_response.status_code != 200:
    print(f"Erro ao criar mídia para o dia {current_count}:")
    print(media_response.text)
    media_response.raise_for_status()

creation_id = media_response.json()["id"]
print(f"Container criado para o Dia {current_count}: {creation_id}")

# 3. Aguardar processamento
status_url = f"https://graph.facebook.com/v25.0/{creation_id}"
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

    time.sleep(5) # Aumentado levemente para segurança
else:
    raise TimeoutError("Timeout aguardando a mídia ficar pronta")

# 4. Publicar
publish_url = f"https://graph.facebook.com/v25.0/{IG_USER_ID}/media_publish"
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

# 6. Commit automático (melhorado para evitar erros se não houver mudanças)
try:
    subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", COUNTER_FILE], check=True)
    
    commit = subprocess.run(
        ["git", "commit", "-m", f"chore: contador Instagram dia {current_count}"],
        capture_output=True,
        text=True
    )
    
    if "nothing to commit" not in commit.stdout:
        subprocess.run(["git", "push"], check=True)
        print("Alterações enviadas para o repositório.")
except Exception as e:
    print(f"Erro no Git: {e}")

print(f"✅ Post do Dia {current_count} publicado com sucesso.")