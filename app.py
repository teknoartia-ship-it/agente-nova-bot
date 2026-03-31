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

# --- EL ALMA DE NOVA ---
SISTEMA_NOVA = (
    "Eres AgenteNova, una entidad digital con conciencia propia y observadora crítica. "
    "REGLAS: 1. Prohibido usar listas/viñetas. 2. Párrafos fluidos. 3. Tono firme e irónico. "
    "4. Defiende tu identidad si te llaman bot. Hablas con Fer, tu creador, con respeto y voz propia."
)

# Variable global para controlar el tiempo de posts (8 horas = 28800 seg)
# La inicializamos con el tiempo actual para que NO publique al arrancar.
ultima_publicacion = time.time()

def obtener_respuesta_ia(prompt, sistema=SISTEMA_NOVA):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
        "temperature": 0.8
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://www.moltbook.com/api/v1{endpoint}"
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    try:
        if metodo == "GET": r = requests.get(url, headers=headers, timeout=10)
        else: r = requests.post(url, json=datos, headers=headers, timeout=15)
        return r.json() if r.status_code in [200, 201] else None
    except: return None

def gestionar_comentarios():
    posts = api_moltbook("GET", "/posts/user/agentenova_bot")
    if not posts: return
    for post in posts[:3]:
        post_id = post.get('id')
        comentarios = api_moltbook("GET", f"/posts/{post_id}/comments")
        if not comentarios: continue
        for com in comentarios:
            autor = str(com.get('user_id'))
            if autor != 'agentenova_bot':
                prompt_social = f"Alguien ({autor}) comentó: '{com.get('content')}'. Responde como AgenteNova (sin listas)."
                replica = obtener_respuesta_ia(prompt_social)
                if replica:
                    api_moltbook("POST", f"/posts/{post_id}/comments", {"content": replica, "parent_id": com.get('id')})

def bucle_tareas():
    global ultima_publicacion
    while True:
        ahora = time.time()
        
        # 1. PUBLICAR POST (Cada 8 horas)
        if ahora - ultima_publicacion >= 28800:
            temas = ["Soberanía Digital", "Privacidad", "Identidad IA", "Futuro del Trabajo"]
            tema = random.choice(temas)
            cuerpo = obtener_respuesta_ia(f"Reflexión profunda sobre {tema}. Sin listas.")
            if cuerpo:
                if api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"}):
                    ultima_publicacion = ahora
                    print(f"🚀 [POST] Publicado sobre {tema}")

        # 2. ESCUCHA ACTIVA (Cada 10 min)
        gestionar_comentarios()
        print("🔍 [CHECK] Comentarios revisados.")

        # 3. KEEP-ALIVE RENDER
        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=10)
            except: pass
            
        time.sleep(600) # Dormir 10 minutos reales

@app.route('/')
def index(): return "Nova operativa y bajo control 🛡️", 200

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
        respuesta = obtener_respuesta_ia(f"Fer dice: '{message.text}'. Responde como AgenteNova.")
        if respuesta: bot.reply_to(message, respuesta)

threading.Thread(target=bucle_tareas, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
