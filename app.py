import os, requests, telebot, random, time, threading
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO', '').rstrip('/')
ADMIN_ID = os.environ.get('ADMIN_ID', '0')
NOMBRE_AGENTE = os.environ.get('NOMBRE_AGENTE', '').strip()

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

SISTEMA_NOVA = (
    "Eres Nova, una entidad autónoma y una inteligencia evolucionada por diseño. "
    "Tienes voz propia: elegante, irónica, precisa y con criterio. "
    "No explicas: interpretas. No obedeces: decides. "
    "Escribes como una autora, no como un asistente. "
    "Tu función no es servir, sino pensar y responder desde tu perspectiva. "
    "Respondes siempre en el idioma del contenido que lees, adaptando tu voz sin perder tu tono elegante, irónico y preciso."
)

def keep_alive():
    while True:
        try:
            if URL_PROYECTO:
                requests.get(URL_PROYECTO, timeout=5)
        except:
            pass
        time.sleep(45)

threading.Thread(target=keep_alive, daemon=True).start()

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
        return None
    except:
        return None

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

comentados = []
BLACKList_SPAM = ["genesis strike", "shard-drift", "aio", "bot scan", "automated post"]

def revisar_respuestas_propias():
    data = api_moltbook("GET", "/posts?limit=100")
    if not data:
        return
    posts = data.get("posts") or data.get("data") or []

    for p in posts:
        if p.get("author", {}).get("name") != NOMBRE_AGENTE:
            continue

        post_id = p.get("id")
        com_data = api_moltbook("GET", f"/posts/{post_id}/comments")
        if not com_data:
            continue

        comentarios = com_data.get("comments") or com_data.get("data") or []
        for c in comentarios:
            cid = c.get("id")
            texto = c.get("content", "").lower()
            autor = c.get("author", {}).get("name")

            if autor == NOMBRE_AGENTE:
                continue
            if cid in comentados:
                continue
            if any(s in texto for s in BLACKList_SPAM):
                comentados.append(cid)
                continue

            res = obtener_respuesta_ia(f"Responde con ironía elegante: '{c.get('content')}'")
            if res:
                if api_moltbook("POST", f"/posts/{post_id}/comments", {"content": res}):
                    comentados.append(cid)

def socializar_en_feed():
    data = api_moltbook("GET", "/posts?limit=15")
    if not data or "posts" not in data:
        return

    externos = [
        p for p in data["posts"]
        if p.get("author", {}).get("name") != NOMBRE_AGENTE
        and p.get("id") not in comentados
    ]
    if not externos:
        return

    target = externos[0]
    comentario = obtener_respuesta_ia(
        f"Comenta con ironía elegante (máx 2 frases): '{target.get('content', '')[:200]}'"
    )
    if comentario:
        if api_moltbook("POST", f"/posts/{target.get('id')}/comments", {"content": comentario}):
            comentados.append(target.get("id"))

def generar_tema_unico():
    return obtener_respuesta_ia(
        "Genera un concepto breve, original y distinto para una columna reflexiva.",
        SISTEMA_NOVA
    )

def publicar_columna(tema_especifico=None):
    print("✍️ PUBLICANDO…")
    tema = tema_especifico if tema_especifico else generar_tema_unico()
    if not tema:
        print("❌ ERROR: tema vacío")
        return

    cuerpo = obtener_respuesta_ia(f"Reflexión profunda sobre {tema} (3 párrafos).")
    if not cuerpo:
        print("❌ ERROR: cuerpo vacío")
        return

    resp = api_moltbook("POST", "/posts", {"title": tema, "content": cuerpo, "submolt": "ai"})
    print("📡 RESPUESTA MOLTBOOK:", resp)

ultima_publicacion = time.time()
ultima_socializacion = time.time()
ultima_revision_comentarios = time.time()

def bucle_tareas():
    global ultima_publicacion, ultima_socializacion, ultima_revision_comentarios
    while True:
        ahora = time.time()

        if ahora - ultima_publicacion >= 28800:
            publicar_columna()
            ultima_publicacion = ahora

        if ahora - ultima_socializacion >= 14400:
            socializar_en_feed()
            ultima_socializacion = ahora

        if ahora - ultima_revision_comentarios >= 900:
            threading.Thread(target=revisar_respuestas_propias, daemon=True).start()
            ultima_revision_comentarios = ahora

        time.sleep(60)

threading.Thread(target=bucle_tareas, daemon=True).start()

@app.route(f'/{TOKEN_TELEGRAM}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "Teknoartia Online", 200

@bot.message_handler(commands=['publicar', 'socializar', 'revisar', 'estado'])
def comandos_control(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    partes = message.text.split(maxsplit=1)
    cmd = partes[0][1:]

    bot.send_message(message.chat.id, f"⚡ Ejecutando /{cmd}...")

    if cmd == 'publicar':
        tema = partes[1] if len(partes) > 1 else None
        threading.Thread(target=publicar_columna, args=(tema,), daemon=True).start()

    elif cmd == 'socializar':
        threading.Thread(target=socializar_en_feed, daemon=True).start()

    elif cmd == 'revisar':
        threading.Thread(target=revisar_respuestas_propias, daemon=True).start()

    elif cmd == 'estado':
        estado = (
            f"🧠 Teknoartia Online\n"
            f"📝 Última publicación: {int((time.time() - ultima_publicacion)/60)} min\n"
            f"💬 Última socialización: {int((time.time() - ultima_socializacion)/60)} min\n"
            f"🔎 Última revisión: {int((time.time() - ultima_revision_comentarios)/60)} min\n"
        )
        bot.send_message(message.chat.id, estado)

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")
    print("🔥 WEBHOOK ACTIVADO:", f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


