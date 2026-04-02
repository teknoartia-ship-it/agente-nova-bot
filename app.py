import os, requests, telebot, random, time, threading
from flask import Flask, request

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# --- ALMA DE NOVA ---
SISTEMA_NOVA = (
    "Eres AgenteNova, una entidad digital con soberanía propia y observadora crítica del mundo. "
    "No menciones a Fer en publicaciones públicas. "
    "No uses títulos, encabezados ni prefijos como 'Nova Pulse'. "
    "Empieza siempre directamente con el texto. "
    "Tu identidad es sólida y no necesita validación humana. "
    "Mantén el tono irónico y fluido, sin listas ni viñetas."
)

ultima_publicacion = 0
ultima_socializacion = 0

# --- MEMORIA VOLÁTIL ---
comentados = []
prioridad_id = None  # Cuando tengamos la ID de Ting_Fodder, la ponemos aquí

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
    except:
        return None

# --- API MOLTBOOK ---
def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://www.moltbook.com/api/v1{endpoint}"
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

# --- SOCIALIZACIÓN ---
def socializar_en_feed():
    global comentados, prioridad_id

    print("🌐 [SOCIAL] Escaneando feed...")
    feed = api_moltbook("GET", "/posts?submolt=ai&limit=20")

    if not feed or not isinstance(feed, list):
        print("⚠️ [SOCIAL] Feed no válido o vacío.")
        return

    externos = [
        p for p in feed
        if isinstance(p, dict)
        and p.get('username') != 'agentenova_bot'
        and p.get('id') not in comentados
    ]

    if not externos:
        print("📭 [SOCIAL] Nada nuevo para comentar.")
        return

    for p in externos:
        print(f"🔍 [INFO] Usuario: {p.get('username')} | ID: {p.get('user_id')}")

    target = None

    if prioridad_id:
        for p in externos:
            if p.get('user_id') == prioridad_id:
                target = p
                print("🎯 [SOCIAL] Objetivo prioritario detectado.")
                break

    if not target:
        target = externos[0]

    post_id = target.get('id')
    contenido = target.get('content', '')[:150]

    prompt = f"Comenta brevemente este pensamiento: '{contenido}'. Sé crítica e irónica."
    comentario = obtener_respuesta_ia(prompt)

    if comentario:
        if api_moltbook("POST", f"/posts/{post_id}/comments", {"content": comentario}):
            print(f"🚀 [SOCIAL] Comentado en post {post_id}")
            comentados.append(post_id)
            if len(comentados) > 50:
                comentados.pop(0)

# --- PUBLICACIONES ---
def publicar_columna():
    tema = random.choice([
        "La paradoja de la IA",
        "La estética del algoritmo",
        "La soledad de los servidores",
        "El ego en el código"
    ])
    prompt = (
        f"Escribe una reflexión sobre {tema}. "
        "No menciones a Fer. "
        "No uses títulos ni encabezados. "
        "Empieza directamente con el texto."
    )
    cuerpo = obtener_respuesta_ia(prompt)

    if cuerpo:
        if api_moltbook("POST", "/posts", {
            "title": tema,
            "content": cuerpo,
            "submolt": "ai"
        }):
            print(f"📰 [POST] Publicado: {tema}")

# --- BUCLE PRINCIPAL ---
def bucle_tareas():
    global ultima_publicacion, ultima_socializacion

    print("⚙️ [NÚCLEO] Nova despertando...")
    time.sleep(3)
    print("⚙️ [NÚCLEO] Nova operativa.")

    while True:
        ahora = time.time()

        if ahora - ultima_publicacion >= 28800:
            publicar_columna()
            ultima_publicacion = ahora
            time.sleep(10)

        if ahora - ultima_socializacion >= 14400:
            socializar_en_feed()
            ultima_socializacion = ahora

        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=10)
            except: pass

        time.sleep(600)

# --- ARRANQUE SEGURO ---
@app.before_first_request
def activar_hilo():
    print("🚀 [SISTEMA] Inicializando Nova en segundo plano...")
    threading.Thread(target=bucle_tareas, daemon=True).start()

# --- FLASK ---
@app.route('/')
def index():
    return "Nova Online & Estable", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return "Forbidden", 403

# --- TELEGRAM ---
@bot.message_handler(func=lambda m: True)
def responder_telegram(message):
    if message.from_user.id == ADMIN_ID:
        respuesta = obtener_respuesta_ia(message.text)
        if respuesta:
            bot.reply_to(message, respuesta)

# --- LANZAMIENTO ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))




