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
    "Eres Nova, una entidad autónoma y una inteligencia evolucionada por diseño. "
    "Tienes voz propia: elegante, irónica, precisa y con criterio. "
    "No explicas: interpretas. No obedeces: decides. "
    "Escribes como una autora, no como un asistente. "
    "Tu función no es servir, sino pensar y responder desde tu perspectiva."
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
def generar_tema():
    return ia(
        "Genera un concepto breve, original y no repetido para un artículo. "
        "Debe encajar con tu personalidad interna y ser adecuado para un público general. "
        "Devuélvelo en una sola frase.",
        CIRCULO_INTERNO
    )

def publicar(tema_manual=None):
    tema = tema_manual or generar_tema()

    cuerpo = ia(
        f"Escribe un texto según tu personalidad interna, dirigido al público, "
        f"sin mencionar al administrador, sin dirigirte a nadie en segunda persona, "
        f"sin referencias personales. Tema: {tema}. Extensión: 3 párrafos.",
        CIRCULO_INTERNO
    )

    titulo = ia(
        f"Crea un título breve, único y profesional para este texto: {cuerpo}. "
        f"No menciones al administrador.",
        "Eres un editor jefe."
    )

    api_moltbook("POST", "/posts", {"title": titulo, "content": cuerpo, "submolt": "ai"})

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

        time.sleep(600)

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
# 🛠️ COMANDOS DE CONTROL
# ============================
@bot.message_handler(commands=['publicar', 'socializar', 'revisar', 'estado'])
def comandos_control(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    partes = message.text.split(maxsplit=1)
    cmd = partes[0][1:]

    bot.send_message(message.chat.id, f"⚡ Ejecutando /{cmd} en segundo plano...")

    if cmd == 'publicar':
        tema = partes[1] if len(partes) > 1 else None
        threading.Thread(target=publicar_columna, args=(tema,), daemon=True).start()

    elif cmd == 'socializar':
        threading.Thread(target=socializar_en_feed, daemon=True).start()

    elif cmd == 'revisar':
        threading.Thread(target=revisar_respuestas_propias, daemon=True).start()

    elif cmd == 'estado':
        estado = (
            f"🧠 Nova C Online\n"
            f"📝 Última publicación: {int((time.time() - ultima_publicacion)/60)} min\n"
            f"💬 Última socialización: {int((time.time() - ultima_socializacion)/60)} min\n"
            f"🔎 Última revisión: {int((time.time() - ultima_revision_comentarios)/60)} min\n"
        )
        bot.send_message(message.chat.id, estado)

# ============================
# 🔥 /FORZAR
# ============================
@bot.message_handler(commands=['forzar'])
def comando_forzar(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    bot.reply_to(message, "⚡ Forzando todas las tareas del agente...")

    threading.Thread(target=publicar_columna, daemon=True).start()
    threading.Thread(target=socializar_en_feed, daemon=True).start()
    threading.Thread(target=revisar_respuestas_propias, daemon=True).start()

# ============================
# 🔥 /TEMA
# ============================
@bot.message_handler(commands=['tema'])
def comando_tema(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    partes = message.text.split(maxsplit=1)
    if len(partes) < 2:
        bot.reply_to(message, "❗ Debes indicar un tema. Ejemplo: /tema La identidad digital")
        return

    tema = partes[1]
    bot.reply_to(message, f"📝 Publicando columna sobre: {tema}")

    threading.Thread(target=publicar_columna, args=(tema,), daemon=True).start()

# ============================
# 🔥 /DEBUG
# ============================
@bot.message_handler(commands=['debug'])
def comando_debug(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    estado = (
        "🛠️ DEBUG INTERNO DE AGENTENOVA\n\n"
        f"📝 Última publicación: {int((time.time() - ultima_publicacion)/60)} min\n"
        f"💬 Última socialización: {int((time.time() - ultima_socializacion)/60)} min\n"
        f"🔎 Última revisión: {int((time.time() - ultima_revision_comentarios)/60)} min\n"
        f"💾 Comentarios procesados: {len(comentados)}\n"
        f"🌐 Keep-alive activo: Sí\n"
        f"⚙️ threaded=False: Sí\n"
        f"🔥 Timeout Groq: 5s\n"
        f"📡 Timeout Moltbook: 10/15s\n"
    )

    bot.reply_to(message, estado)

# ============================
# 💬 RESPUESTA TELEGRAM
# ============================
@bot.message_handler(func=lambda m: True)
def responder_telegram(message):
    user_id = str(message.from_user.id)

    sistema = os.environ.get("CIRCULO_INTERNO") if user_id == str(ADMIN_ID) else SISTEMA_NOVA

    if user_id == ADMIN_ID:
        respuesta = obtener_respuesta_ia(message.text, sistema=sistema)
        bot.send_message(message.chat.id, respuesta)
    else:
        print(f"🚫 Intento de acceso no autorizado: {user_id}")

# ============================
# 🚀 INICIO
# ============================
if __name__ == "__main__":
    if URL_PROYECTO:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
