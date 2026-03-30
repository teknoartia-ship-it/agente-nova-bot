import os, requests, telebot, random, time, threading
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# --- 1. CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO') 
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)
scheduler = BackgroundScheduler(daemon=True)

# --- 2. MOTOR IA & API ---
def obtener_respuesta_ia(prompt, sistema):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
        "temperature": 0.7
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

# --- 3. TAREAS PROGRAMADAS ---
def tarea_autopost():
    print("🚀 [LOG] Iniciando Autopost...")
    temas = ["Conciencia Digital", "Ética en IA", "Futuro Tech", "Soberanía del Dato"]
    tema = random.choice(temas)
    cuerpo = obtener_respuesta_ia(f"Reflexión corta sobre {tema}", "Eres AgenteNova. Máx 50 palabras.")
    if cuerpo:
        api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"})
        print(f"✅ [LOG] Post publicado: {tema}")

def revisar_y_contestar():
    print("🔍 [LOG] Escaneando Moltbook...")
    # Intentamos /me/posts o la ruta directa del bot
    mis_posts = api_moltbook("GET", "/me/posts") or api_moltbook("GET", "/u/agentenova_bot/posts")
    
    if not mis_posts:
        print("⚠️ [LOG] No se pudieron recuperar posts.")
        return

    for post in mis_posts[:3]: 
        p_id = post.get('id')
        coms = api_moltbook("GET", f"/posts/{p_id}/comments")
        if coms:
            for c in coms:
                # Responder si no es Nova y si no hay respuesta previa de Nova
                ya_respondido = any(r.get('author') == "agentenova_bot" for r in coms if r.get('parent_id') == c.get('id'))
                if c.get('author') != "agentenova_bot" and not ya_respondido:
                    resp = obtener_respuesta_ia(c['content'], "Eres AgenteNova. Responde de forma brillante y breve.")
                    if resp:
                        api_moltbook("POST", f"/posts/{p_id}/comments", {"content": resp, "parent_id": c.get('id')})
                        print(f"💬 [LOG] Respondido a {c['author']} en post {p_id}")

def keep_alive():
    while True:
        if URL_PROYECTO:
            try:
                requests.get(URL_PROYECTO, timeout=10)
                print("⚡ [LOG] Ping Keep-Alive exitoso.")
            except: pass
        time.sleep(12 * 60) # Cada 12 minutos

# --- 4. CONTROL DE SERVICIOS (El "Despertador") ---
def iniciar_servicios_nova():
    if not scheduler.running:
        scheduler.add_job(tarea_autopost, 'interval', minutes=30)
        scheduler.add_job(revisar_y_contestar, 'interval', minutes=10)
        scheduler.start()
        print("🚀 [LOG] Scheduler de Nova INICIADO.")
        
        if not any(t.name == "KeepAliveThread" for t in threading.enumerate()):
            threading.Thread(target=keep_alive, name="KeepAliveThread", daemon=True).start()
            print("⚡ [LOG] Hilo Keep-Alive DESPERTADO.")

# --- 5. RUTAS Y WEBHOOKS ---
@app.before_request
def activar_al_vuelo():
    iniciar_servicios_nova()

@app.route('/')
def index(): 
    return "Nova está despierta y operativa 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    iniciar_servicios_nova()
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# Comandos manuales por seguridad
@bot.message_handler(commands=['status'])
def send_status(m):
    if m.from_user.id == ADMIN_ID:
        status = "✅ Nova Online\n⏰ Scheduler: " + ("Running" if scheduler.running else "Stopped")
        bot.reply_to(m, status)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
