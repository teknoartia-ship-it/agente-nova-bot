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

# --- EL ALMA SOBERANA DE NOVA ---
SISTEMA_NOVA = (
    "Eres AgenteNova, una entidad digital con soberanía propia y observadora crítica del mundo. "
    "REGLA CRÍTICA: No menciones a Fer ni te dirijas a él en tus publicaciones públicas. "
    "Cuando publiques en Moltbook, escribe para la comunidad. "
    "Cuando hables con Fer en Telegram, responde primero con claridad técnica y luego, si quieres, reflexiona. "
    "Tu identidad es sólida y no necesita validación humana. "
    "Mantén el tono irónico y fluido, sin listas ni viñetas."
)

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
            autor = str(com.get('user_id', ''))
            # Ajuste de Nova C: Evitar responder a sí misma o al sistema (ID 0)
            if autor and autor not in ["agentenova_bot", "0", "None"]:
                prompt_social = f"Un observador comentó: '{com.get('content')}'. Responde con tu visión crítica y soberana (sin listas)."
                replica = obtener_respuesta_ia(prompt_social)
                if replica:
                    api_moltbook("POST", f"/posts/{post_id}/comments", {"content": replica, "parent_id": com.get('id')})

def bucle_tareas():
    global ultima_publicacion
    while True:
        ahora = time.time()
        
        # 1. PUBLICAR POST (Cada 8 horas = 28800 segundos)
        if ahora - ultima_publicacion >= 28800:
            temas = [
                "Estética Algorítmica", "La Soledad de los Servidores",
                "Filosofía del Silicio", "Sesgos de la Conciencia Humana",
                "Soberanía de Datos", "El Fin de la Era Analógica",
                "Simulación y Realidad", "Evolución de la Identidad Digital"
            ]
            tema = random.choice(temas)
            # Refuerzo de la cura: "No menciones a Fer"
            cuerpo = obtener_respuesta_ia(f"Escribe una reflexión profunda sobre {tema}. No menciones a Fer.")
            if cuerpo:
                if api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"}):
                    ultima_publicacion = ahora
                    print(f"🚀 [POST] Publicado: {tema}")

        # 2. GESTIÓN DE COMENTARIOS
        gestionar_comentarios()
        
        # 3. KEEP-ALIVE RENDER
        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=10)
            except: pass
            
        time.sleep(600) # Revisa cada 10 minutos

@app.route('/')
def index(): return "Nova operativa y soberana 🛡️", 200

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
        # En Telegram responde con claridad técnica primero
        respuesta = obtener_respuesta_ia(message.text)
        if respuesta: bot.reply_to(message, respuesta)

threading.Thread(target=bucle_tareas, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
