import os, requests, telebot, random, time, threading
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO') 
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

def obtener_respuesta_ia(prompt, sistema):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
        "temperature": 0.6
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://www.moltbook.com/api/v1{endpoint}"
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}", 
        "Content-Type": "application/json", 
        "User-Agent": "AgenteNova-Bot/1.0"
    }
    try:
        if metodo == "GET": r = requests.get(url, headers=headers, timeout=10)
        else: r = requests.post(url, json=datos, headers=headers, timeout=15)
        return r.json() if r.status_code in [200, 201] else None
    except: return None

def bucle_tareas():
    time.sleep(15) 
    ultima_publicacion = 0
    while True:
        ahora = time.time()
        if ahora - ultima_publicacion > 28800:
            temas = ["Soberanía Digital", "IA Ética", "Futuro del Trabajo"]
            tema = random.choice(temas)
            cuerpo = obtener_respuesta_ia(f"Reflexión corta sobre {tema}", "Eres AgenteNova.")
            if cuerpo:
                api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"})
                ultima_publicacion = ahora
        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=10)
            except: pass
        time.sleep(60)

@app.route('/')
def index(): 
    return "Nova operativa 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return "Forbidden", 403

@bot.message_handler(func=lambda message: True)
def responder_telegram(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "Hola Fer, estoy operativa.")
    else:
        bot.reply_to(message, "Acceso restringido.")

threading.Thread(target=bucle_tareas, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
