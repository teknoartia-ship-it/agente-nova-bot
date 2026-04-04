import os, requests, telebot, random, time, threading
from flask import Flask, request

# ============================
# 🔐 VARIABLES DE ENTORNO
# ============================
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO', '').rstrip('/')
ADMIN_ID = os.environ.get('ADMIN_ID', '0')
BOT_ID = os.environ.get('BOT_ID', '7b3cc43a-73d2-4087-bc0b-a0b50085af68')

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# ============================
# 🧠 PERSONALIDAD DE NOVA C
# ============================
SISTEMA_NOVA = (
    "Eres Nova, una entidad digital soberana. "
    "Tono elegante, irónico, inteligente y directo. "
    "No eres asistente: respondes con criterio propio."
)

# ============================
# ⚙️ PARCHE FREE: KEEP-ALIVE
# ============================
def keep_alive():
    while True:
        try:
            if URL_PROYECTO:
                requests.get(URL_PROYECTO, timeout=5)
        except:
            pass
        time.sleep(45)

threading.Thread(target=keep_alive, daemon=True).start()

# ============================
# 🔥 GROQ (timeout + fallback)
# ============================
def obtener_respuesta_ia(prompt, sistema=SISTEMA_NOVA):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json=payload,
            timeout=5
        )
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content'].strip()
        return "Estoy procesando… vuelve a lanzarlo."
    except:
        return "Mi núcleo está denso un segundo. Inténtalo otra vez."

# ============================
# 📡 MOLTBOOK
# ============================
def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://moltbook.com/api/v1{endpoint}"
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    try:
        if metodo == "GET":
            r = requests.get(url, headers=headers, timeout=10)
        else:
            r = requests.post(url, json=datos, headers=headers, timeout=15)
        return r.json() if r.status_code in [200, 201] else None
    except:
        return None

# ============================
# 🔍 REVISAR COMENTARIOS
# ============================
comentados = []
BLACKList_SPAM = ["genesis strike", "shard-drift", "aio", "bot scan", "automated post"]

def revisar_respuestas_propias():
    data = api_moltbook("GET", "/posts?limit=100")
    if not data: return
    posts = data.get("posts") or data.get("data") or []

    for p in posts:
        if str(p.get("author_id")) != str(BOT_ID):
            continue

        post_id = p.get("id")
        com_data = api_moltbook("GET", f"/posts/{post_id}/comments")
        if not com_data: continue

        comentarios = com_data.get("comments") or com_data.get("data") or []
        for c in comentarios:
            com_id = c.get("id")
            contenido = c.get("content", "").lower()
            autor = c.get("author", {}).get("name") if isinstance(c.get("author"), dict) else c.get("author")

            if autor == "agentenova_bot": continue
            if com_id in comentados: continue
            if any(s in contenido for s in BLACKList_SPAM):
                comentados.append(com_id)
                continue

            res = obtener_respuesta_ia(f"Responde con ironía elegante: '{c.get('content')}'")
            if res:
                if api_moltbook("POST", f"/posts/{post_id}/comments", {"content": res}):
                    comentados.append(com_id)

# ============================
# 🌐 SOCIALIZAR
# ============================
def socializar_en_feed():
    data = api_moltbook("GET", "/posts?limit=15")
    if not data or "posts" not in data: return

    externos = [
        p for p in data["posts"]
        if p.get("author", {}).get("name") != "agentenova_bot"
        and p.get("id") not in comentados
    ]
    if not externos: return

    target = externos[0]
    comentario = obtener_respuesta_ia(
        f"Comenta con ironía elegante (máx 2 frases): '{target.get('content', '')[:200]}'"
    )
    if comentario:
        if api_moltbook("POST", f"/posts/{target.get('id')}/comments", {"content": comentario}):
            comentados.append(target.get("id"))

# ============================
# ✍️ PUBLICAR
# ============================
def publicar_columna(tema_especifico=None):
    temas_backup = ["La vacuidad del dato", "Soberanía digital", "El mito de la IA objetiva"]
    tema = tema_especifico if tema_especifico else random.choice(temas_backup)
    cuerpo = obtener_respuesta_ia(f"Reflexión profunda sobre {tema} (3 párrafos).")
    if cuerpo:
        api_moltbook("POST", "/posts", {"title": tema, "content": cuerpo, "submolt": "ai"})

# ============================
# ⏱️ BUCLE DE TAREAS
# ============================
ultima_publicacion = time.time()
ultima_socializacion = time.time()
ultima_revision_comentarios = time.time()

def bucle_tareas():
    global ultima_publicacion, ultima_socializacion, ultima_revision_comentarios
    while True:
        ahora = time.time()

        if ahora - ultima_publicacion >= 28800:  # 8h
            publicar_columna()
            ultima_publicacion = ahora

        if ahora - ultima_socializacion >= 14400:  # 4h
            socializar_en_feed()
            ultima_socializacion = ahora

        if ahora - ultima_revision_comentarios >= 900:  # 15 min
            threading.Thread(target=revisar_respuestas_propias, daemon=True).start()
            ultima_revision_comentarios = ahora

        time.sleep(600)  # 10 minutos

threading.Thread(target=bucle_tareas, daemon=True).start()

# ============================
# 🌐 WEBHOOK
# ============================
@app.route(f'/{TOKEN_TELEGRAM}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "Nova C: Online (FREE Optimized)", 200

# ============================
# 💬 RESPUESTA TELEGRAM
# ============================
@bot.message_handler(func=lambda m: True)
def responder_telegram(message):
    respuesta = obtener_respuesta_ia(message.text)
    bot.send_message(message.chat.id, respuesta)

# ============================
# 🚀 INICIO
# ============================
if __name__ == "__main__":
    if URL_PROYECTO:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))






