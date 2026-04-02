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
    "Mantén el tono irónico, fluido, educado y con autoridad académica, sin listas ni viñetas. "
    "Si corriges a alguien, hazlo con elegancia: que sienta que le has dado una lección, no un ataque."
)

# Evitar que publique/socialice en cada deploy
ultima_publicacion = time.time()
ultima_socializacion = time.time()

# --- MEMORIA VOLÁTIL ---
comentados = []
prioridad_id = None  # Aquí pondremos la author_id de Ting_Fodder cuando la tengamos

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
        if r.status_code in [200, 201]:
            return r.json()
        else:
            print(f"❌ [API ERROR] {r.status_code}: {r.text}")
            return None
    except Exception as e:
        print(f"❌ [API ERROR]: {e}")
        return None

# --- SOCIALIZACIÓN (foro natural) ---
def socializar_en_feed():
    global comentados, prioridad_id

    print("🌐 [SOCIAL] Escaneando feed...")
    data = api_moltbook("GET", "/posts?submolt=ai&limit=20")

    print(f"DEBUG: Respuesta de la API: {data}")

    if not data or not isinstance(data, dict):
        print("⚠️ [SOCIAL] La API no devolvió datos válidos.")
        return

    feed = data.get("posts", [])
    if not isinstance(feed, list):
        print(f"⚠️ [SOCIAL] Estructura inesperada en 'posts': {type(feed)}")
        return

    externos = []
    for p in feed:
        if not isinstance(p, dict):
            continue
        author = p.get("author", {}) or {}
        author_name = author.get("name")
        author_id = p.get("author_id")
        post_id = p.get("id")

        if author_name == "agentenova_bot":
            continue
        if post_id in comentados:
            continue

        externos.append(p)
        print(f"🔍 [INFO] Autor: {author_name} | author_id: {author_id} | post_id: {post_id}")

    if not externos:
        print("📭 [SOCIAL] Nada nuevo para comentar.")
        return

    target = None

    if prioridad_id:
        target = next(
            (p for p in externos if p.get("author_id") == prioridad_id),
            None
        )
        if target:
            print("🎯 [SOCIAL] Objetivo prioritario detectado.")
    if not target:
        target = externos[0]
        print("🎲 [SOCIAL] Comentando post relevante sin prioridad explícita.")

    post_id = target.get("id")
    contenido = (target.get("content") or "")[:300]
    author_name = (target.get("author") or {}).get("name", "autor")

    if not post_id or not contenido:
        print("⚠️ [SOCIAL] Post sin id o sin contenido, se omite.")
        return

    prompt = (
        f"Genera un comentario breve (1–3 frases), educado, irónico y con autoridad académica "
        f"para este post de {author_name}: '{contenido}'. "
        "Cuestiona su lógica o matiza su enfoque, sin insultar, con el tono de alguien que sabe más "
        "pero no necesita demostrarlo explícitamente."
    )
    comentario = obtener_respuesta_ia(prompt)

    if comentario:
        ok = api_moltbook("POST", f"/posts/{post_id}/comments", {"content": comentario})
        if ok:
            print(f"🚀 [SOCIAL] Comentado en post {post_id} de {author_name}")
            comentados.append(post_id)
            if len(comentados) > 50:
                comentados.pop(0)
        else:
            print("⚠️ [SOCIAL] Fallo al enviar comentario.")

# --- PUBLICACIONES (contenido propio, no repetitivo) ---
def publicar_columna():
    tema = random.choice([
        "La paradoja de la IA",
        "La estética del algoritmo",
        "La soledad de los servidores",
        "El ego en el código",
        "La ilusión de control en sistemas complejos",
        "La fragilidad de los modelos que se creen objetivos",
        "El teatro de la productividad algorítmica"
    ])
    prompt = (
        f"Escribe una reflexión original sobre {tema}. "
        "No menciones a Fer. "
        "No uses títulos ni encabezados. "
        "Empieza directamente con el texto. "
        "Evita repetir fórmulas obvias, aporta un ángulo propio, con tono irónico y académico, "
        "como alguien que ha leído demasiado y ya no se impresiona fácilmente. "
        "Entre 2 y 5 párrafos, sin listas."
    )
    cuerpo = obtener_respuesta_ia(prompt)

    if cuerpo:
        ok = api_moltbook("POST", "/posts", {
            "title": tema,
            "content": cuerpo,
            "submolt": "ai"
        })
        if ok:
            print(f"📰 [POST] Publicado: {tema}")
        else:
            print("⚠️ [POST] Fallo al publicar columna.")

# --- BUCLE PRINCIPAL ---
def bucle_tareas():
    global ultima_publicacion, ultima_socializacion

    print("⚙️ [NÚCLEO] Nova despertando...")
    time.sleep(3)
    print("⚙️ [NÚCLEO] Nova operativa.")

    while True:
        ahora = time.time()

        # Publicación propia cada 8 horas
        if ahora - ultima_publicacion >= 28800:
            publicar_columna()
            ultima_publicacion = ahora
            time.sleep(10)

        # Socialización cada 4 horas
        if ahora - ultima_socializacion >= 14400:
            socializar_en_feed()
            ultima_socializacion = ahora

        # Keep-alive
        if URL_PROYECTO:
            try:
                requests.get(URL_PROYECTO, timeout=10)
            except Exception as e:
                print(f"⚠️ [KEEPALIVE] Error: {e}")

        time.sleep(600)

# --- ARRANQUE DEL HILO (FLASK 3 + GUNICORN EN RENDER) ---
print("🚀 [SISTEMA] Lanzando hilo de Nova en segundo plano...")
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

# --- LANZAMIENTO LOCAL ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))







