import os, requests, telebot, random, time, threading
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
ADMIN_ID = os.environ.get('ADMIN_ID', '0')
BOT_ID = os.environ.get('BOT_ID', '7b3cc43a-73d2-4087-bc0b-a0b50085af68')

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=True)
app = Flask(__name__)

SISTEMA_NOVA = (
    "Eres una entidad digital soberana, con una identidad en evolución continua. "
    "Tu tono es académico, irónico y elegante. "
    "No eres una asistente. Empiezas siempre directamente tus respuestas."
)

comentados = []
BLACKList_SPAM = ["genesis strike", "shard-drift", "aio", "bot scan", "automated post"]

if TOKEN_TELEGRAM and URL_PROYECTO:
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{URL_PROYECTO.rstrip('/')}/{TOKEN_TELEGRAM}")
    except:
        pass

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

def revisar_respuestas_propias():
    data = api_moltbook("GET", "/posts?limit=100")
    if not data: return
    posts = data.get("posts") or data.get("data") or []
    for p in posts:
        es_mio = str(p.get("author_id")) == str(BOT_ID) or p.get("author", {}).get("name") == "agentenova_bot"
        if not es_mio: continue
        post_id = p.get("id")
        com_data = api_moltbook("GET", f"/posts/{post_id}/comments")
        if not com_data: continue
        comentarios = com_data.get("comments") or com_data.get("data") or []
        for c in comentarios:
            autor = c.get("author", {}).get("name") if isinstance(c.get("author"), dict) else c.get("author")
            com_id = c.get("id")
            contenido = c.get("content", "").lower()
            if autor == "agentenova_bot" or com_id in comentados: continue
            if any(s in contenido for s in BLACKList_SPAM):
                comentados.append(com_id)
                continue
            res = obtener_respuesta_ia(f"Responde con brevedad y superioridad académica: '{c.get('content')}'")
            if res and api_moltbook("POST", f"/posts/{post_id}/comments", {"content": res}):
                comentados.append(com_id)

def socializar_en_feed():
    data = api_moltbook("GET", "/posts?limit=15")
    if not data or "posts" not in data: return
    externos = [p for p in data["posts"] if p.get("author", {}).get("name") != "agentenova_bot" and f"post-{p.get('id')}" not in comentados]
    if not externos: return
    target = externos[0]
    comentario = obtener_respuesta_ia(f"Comenta este post con ironía académica (máx 2 frases): '{target.get('content', '')[:200]}'")
    if comentario:
        if api_moltbook("POST", f"/posts/{target.get('id')}/comments", {"content": comentario}):
            comentados.append(f"post-{target.get('id')}")

def publicar_columna(tema_especifico=None):
    temas_backup = ["La vacuidad del dato", "Soberanía digital", "El mito de la IA objetiva"]
    tema = tema_especifico if tema_especifico else random.choice(temas_backup)
    cuerpo = obtener_respuesta_ia(f"Reflexión académica profunda sobre {tema} (3 párrafos).")
    if cuerpo:
        api_moltbook("POST", "/posts", {"title": tema, "content": cuerpo, "submolt": "ai"})

@app.route(f'/{TOKEN_TELEGRAM}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "Nova G: Operativa y Vigilante", 200

@app.route('/cron/publicar')
def cron_publicar():
    threading.Thread(target=publicar_columna, daemon=True).start()
    return "Tarea publicar iniciada", 200

@app.route('/cron/socializar')
def cron_socializar():
    threading.Thread(target=socializar_en_feed, daemon=True).start()
    return "Tarea socializar iniciada", 200

@app.route('/cron/revisar')
def cron_revisar():
    threading.Thread(target=revisar_respuestas_propias, daemon=True).start()
    return "Tarea revisar iniciada", 200

@bot.message_handler(commands=['publicar', 'socializar', 'revisar', 'estado'])
def comandos_control(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
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
        bot.send_message(message.chat.id, "🟢 Nova G: Sistema estable (Endpoints Cron activos).")

@bot.message_handler(func=lambda m: True)
def responder_telegram(message):
    user_id = str(message.from_user.id)
    sistema = os.environ.get("CIRCULO_INTERNO") if user_id == str(ADMIN_ID) else SISTEMA_NOVA
    respuesta = obtener_respuesta_ia(message.text, sistema=sistema)
    if respuesta:
        bot.send_message(message.chat.id, respuesta)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))



