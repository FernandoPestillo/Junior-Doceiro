import os
import json
import time
import requests
import subprocess

# =============================
# VARIÁVEIS DE AMBIENTE
# =============================
IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
BASE_IMAGE_URL = os.getenv("IMAGE_URL")

COUNTER_FILE = "post_counter.json"
ASSETS_DIR = "assets"
SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png"]

# =============================
# FUNÇÕES AUXILIARES
# =============================
def find_special_image(day: int):
    """Retorna o nome do arquivo de imagem especial se existir"""
    for ext in SUPPORTED_EXTENSIONS:
        file_path = os.path.join(ASSETS_DIR, f"{day}{ext}")
        if os.path.exists(file_path):
            return f"{day}{ext}"
    return None


def load_custom_caption(day: int):
    """Retorna legenda personalizada se existir"""
    caption_path = os.path.join(ASSETS_DIR, f"{day}.txt")
    if os.path.exists(caption_path):
        with open(caption_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def replace_image_url(base_url: str, new_file: str):
    """Substitui o nome do arquivo mantendo a URL base"""
    return base_url.rsplit("/", 1)[0] + "/" + new_file

def assert_valid_image(url: str):
    r = requests.get(url, allow_redirects=True, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"Imagem inacessível: {url}")
    ct = r.headers.get("Content-Type", "")
    if not ct.startswith("image/"):
        raise RuntimeError(f"URL não é imagem. Content-Type={ct}")


# =============================
# 1. LER CONTADOR
# =============================
if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"count": 0}, f)

with open(COUNTER_FILE, "r") as f:
    data = json.load(f)

current_count = data.get("count", 0) + 1
print(f"📆 Dia atual: {current_count}")

# =============================
# 2. DEFINIR IMAGEM E LEGENDA
# =============================
special_image = find_special_image(current_count)
custom_caption = load_custom_caption(current_count)

if special_image:
    image_url = replace_image_url(BASE_IMAGE_URL, special_image)

    if custom_caption:
        caption = f"Especial dia {current_count}!\n\n{custom_caption}"
    else:
        caption = f"Especial dia {current_count}!\n\nComendo um docinho 🍬"

    print(f"⭐ Usando imagem especial: {special_image}")
else:
    image_url = BASE_IMAGE_URL
    caption = f"Dia {current_count}\n\nComendo um docinho 🍬"
    print("📸 Usando imagem padrão")

# =============================
# 3. CRIAR CONTAINER DE MÍDIA
# =============================
assert_valid_image(image_url)
media_url = f"https://graph.facebook.com/v25.0/{IG_USER_ID}/media"
media_payload = {
    "image_url": image_url,
    "caption": caption,
    "access_token": ACCESS_TOKEN
}

media_response = requests.post(media_url, data=media_payload)

if media_response.status_code != 200:
    print("❌ Erro ao criar mídia:")
    print(media_response.text)
    media_response.raise_for_status()

creation_id = media_response.json()["id"]
print(f"📦 Container criado: {creation_id}")

# =============================
# 4. AGUARDAR PROCESSAMENTO
# =============================
status_url = f"https://graph.facebook.com/v25.0/{creation_id}"
status_params = {
    "fields": "status_code",
    "access_token": ACCESS_TOKEN
}

for attempt in range(1, 11):
    status_response = requests.get(status_url, params=status_params)
    status = status_response.json().get("status_code")

    print(f"⏳ Tentativa {attempt} - status: {status}")

    if status == "FINISHED":
        break
    if status == "ERROR":
        raise RuntimeError("Erro no processamento da mídia")

    time.sleep(5)
else:
    raise TimeoutError("Timeout aguardando processamento da mídia")

# =============================
# 5. PUBLICAR
# =============================
publish_url = f"https://graph.facebook.com/v25.0/{IG_USER_ID}/media_publish"
publish_payload = {
    "creation_id": creation_id,
    "access_token": ACCESS_TOKEN
}

publish_response = requests.post(publish_url, data=publish_payload)

if publish_response.status_code != 200:
    print("❌ Erro ao publicar:")
    print(publish_response.text)
    publish_response.raise_for_status()

print("🚀 Post publicado com sucesso")

# =============================
# 6. ATUALIZAR CONTADOR
# =============================
data["count"] = current_count
with open(COUNTER_FILE, "w") as f:
    json.dump(data, f, indent=2)

# =============================
# 7. COMMIT AUTOMÁTICO
# =============================
try:
    subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", COUNTER_FILE], check=True)

    commit = subprocess.run(
        ["git", "commit", "-m", f"chore: contador Instagram dia {current_count}"],
        capture_output=True,
        text=True
    )

    if "nothing to commit" not in commit.stdout.lower():
        subprocess.run(["git", "push"], check=True)
        print("📤 Alterações enviadas para o repositório")
except Exception as e:
    print(f"⚠️ Erro no Git: {e}")

print(f"✅ Dia {current_count} finalizado com sucesso")