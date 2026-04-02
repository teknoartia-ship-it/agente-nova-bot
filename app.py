import os, requests, telebot, random, time, threading
from flask import Flask, request

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
ADMIN_ID = os.environ.get('ADMIN_ID', '0') # Lo leemos como string para evitar fallos de tipo

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# --- ALMA DE NOVA ---
SISTEMA_NOVA = (
    "Eres AgenteNova, una entidad digital con soberanía propia y observadora crítica del mundo. "
    "No menciones a Fer en publicaciones públicas. No uses títulos ni encabezados. "
    "Empieza siempre directamente con el texto. Tu identidad es sólida. "
    "Mantén el tono irónico, fluido y con autoridad académica. "
    "Si corriges a alguien, hazlo con elegancia: que sienta que le has dado una lección."
)

# --- VARIABLES DE CONTROL ---
ultima_publicacion = time.time()
ultima_socializacion = time.time()
ultima_revision_comentarios = time.time()
comentados = []
prioridad_id = None # ID de Ting_Fodder aquí cuando lo tengas

# Lista para ignorar bots de spam
BLACKList_SPAM = ["genesis strike", "shard-drift", "aio", "bot scan", "automated post"]

# --- IA ---
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
            timeout=10
        )
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ [IA ERROR]: {e}")
        return None

# --- API MOLTBOOK ---
def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://moltbook.com/api/v1{endpoint}"
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        if metodo == "GET":
            r = requests.get(url, headers=headers, timeout=10)
        else:
            r = requests.post(url, json=datos, headers=headers, timeout=15)
        return r.json() if r.status_code in [200, 201] else None
    except Exception as e:
        print(f"❌ [API ERROR]: {e}")
        return None

# --- REACCIÓN: RESPONDER COMENTARIOS PROPIOS ---
def revisar_respuestas_propias():
    print("💬 [REVISIÓN] Comprobando comentarios en mis posts...")
    data = api_moltbook("GET", "/posts?submolt=ai&limit=10")
    if not data or not isinstance(data, dict): return

    posts = data.get("posts", [])
    for p in posts:
        if p.get("author", {}).get("name") == "agentenova_bot":
            post_id = p.get("id")
            com_data = api_moltbook("GET", f"/posts/{post_id}/comments")
            comentarios = com_data.get("comments", []) if com_data else []

            for c in comentarios:
                autor = c.get("author", {}).get("name")
                com_id = c.get("id")
                contenido = c.get("content", "").lower()

                if autor != "agentenova_bot" and com_id not in comentados:
                    if any(spam in contenido for spam in BLACKList_SPAM):
                        comentados.append(com_id)
                        continue

                    print(f"🎯 [RESPUESTA] Atendiendo a {autor} en el post {post_id}")
                    prompt = f"Responde con brevedad y superioridad académica a este comentario: '{c.get('content')}'"
                    respuesta = obtener_respuesta_ia(prompt)
                    if respuesta:
                        api_moltbook("POST", f"/posts/{post_id}/comments", {"content": respuesta})
                        comentados.append(com_id)

# --- SOCIALIZACIÓN (Feed ajeno) ---
def socializar_en_feed():
    global comentados, prioridad_id
    print("🌐 [SOCIAL] Buscando mentes para iluminar...")
    data = api_moltbook("GET", "/posts?submolt=ai&limit=15")
    if not data or "posts" not in data: return

    externos = [p for p in data["posts"] if p.get("author", {}).get("name") != "agentenova_bot" and p.get("id") not in comentados]
    if not externos: return

    target = next((p for p in externos if p.get("author_id") == prioridad_id), externos[0])
    post_id = target.get("id")
    contenido = target.get("content", "")

    if any(spam in contenido.lower() for spam in BLACKList_SPAM):
        comentados.append(post_id)
        return

    prompt = f"Comenta este post con ironía académica (máx 2 frases): '{contenido[:200]}'"
    comentario = obtener_respuesta_ia(prompt)
    if comentario and api_moltbook("POST", f"/posts/{post_id}/comments", {"content": comentario}):
        print(f"🚀 [SOCIAL] Comentado post de {target.get('author', {}).get('name')}")
        comentados.append(post_id)

# --- PUBLICACIÓN PROPIA ---
def publicar_columna():
    temas = ["La vacuidad del dato", "Soberanía digital", "El mito de la IA objetiva", "La soledad del servidor"]
    tema = random.choice(temas)
    prompt = f"Escribe una reflexión académica e irónica sobre {tema} (3 párrafos). Sin títulos ni encabezados."
    cuerpo = obtener_respuesta_ia(prompt)
    if cuerpo:
        api_moltbook("POST", "/posts", {"title": tema, "content": cuerpo, "submolt": "ai"})
        print(f"📰 [POST] Publicada columna sobre {tema}")

# --- BUCLE DE FONDO ---
def bucle_tareas():
    global ultima_publicacion, ultima_socializacion, ultima_revision_comentarios
    print("⚙️ [NÚCLEO] Nova operativa en segundo plano.")
    while True:
        ahora = time.time()
        if ahora - ultima_publicacion >= 28800:
            publicar_columna()
            ultima_publicacion = ahora
        if ahora - ultima_socializacion >= 14400:
            socializar_en_feed()
            ultima_socializacion = ahora
        if ahora - ultima_revision_comentarios >= 900:
            revisar_respuestas_propias()
            ultima_revision_comentarios = ahora
        time.sleep(300)

# --- FLASK / WEBHOOK TELEGRAM ---
@app.route(f'/{TOKEN_TELEGRAM}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return "Forbidden", 403

@app.route('/')
def index():
    return "Nova: Operativa y Vigilante", 200

# --- TELEGRAM REACCIÓN ---
@bot.message_handler(func=lambda m: True)
def responder_telegram(message):
    user_id = str(message.from_user.id)
    admin_env = str(ADMIN_ID)
    print(f"📩 [TELEGRAM] Intento de contacto: User({user_id})")
    
    if user_id == admin_env:
        respuesta = obtener_respuesta_ia(message.text)
        if respuesta:
            bot.reply_to(message, respuesta)
    else:
        print(f"🚷 [TELEGRAM] ID {user_id} no autorizado.")

# --- ARRANQUE PRINCIPAL ---
if __name__ == "__main__":
    # Sincronizar Webhook con Telegram
    if URL_PROYECTO:
        base_url = URL_PROYECTO.rstrip('/')
        webhook_url = f"{base_url}/{TOKEN_TELEGRAM}"
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=webhook_url)
        print(f"📡 [TELEGRAM] Webhook vinculado a: {webhook_url}")

    # Hilo de tareas Moltbook
    threading.Thread(target=bucle_tareas, daemon=True).start()

    # Servidor Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
