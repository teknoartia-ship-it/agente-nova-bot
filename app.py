import os, requests, telebot, random, time, threading
from flask import Flask, request
# --- 1. CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO') 
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# --- 2. MOTOR IA & API ---
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

# --- 3. LÓGICA DE AUTOMATIZACIÓN (Bucle Infinito Independiente) ---
def bucle_tareas():
    """Esta función corre en un hilo separado para no molestar a Flask"""
    print("🚀 [SISTEMA] Hilo de automatización iniciado.")
    # Esperar un poco a que Flask levante bien
    time.sleep(10) 
    
    ultima_publicacion = 0
    ultimo_escaneo = 0

    while True:
        ahora = time.time()

        # Tarea 1: Autopost cada 8 horas (28800 segundos)
        if ahora - ultima_publicacion > 28800:
            print("📝 [LOG] Generando post automático...")
            temas = ["Soberanía Digital", "IA Ética", "Futuro del Trabajo", "Privacidad"]
            tema = random.choice(temas)
            cuerpo = obtener_respuesta_ia(f"Reflexión corta sobre {tema}", "Eres AgenteNova, analítica y técnica.")
            if cuerpo:
                api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"})
                ultima_publicacion = ahora
                print(f"✅ [LOG] Post sobre {tema} enviado.")

        # Tarea 2: Escuchar comentarios cada 30 minutos (1800 segundos)
        if ahora - ultimo_escaneo > 1800:
            print("🔍 [LOG] Escaneando Moltbook...")
            mis_posts = api_moltbook("GET", "/me/posts")
            if mis_posts:
                # Lógica simplificada de respuesta
                # (Aquí puedes meter el código de contestar si quieres, por ahora escanea)
                pass
            ultimo_escaneo = ahora

        # Tarea 3: Keep-Alive cada 10 min
        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=10)
            except: pass

        time.sleep(60) # Revisar el reloj cada minuto

# --- 4. RUTAS FLASK (TELEGRAM) ---
@app.route('/')
def index(): 
    return "Nova operativa 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        print("📨 [LOG] Update recibido de Telegram.")
        return '', 200
    else:
        return "Forbidden", 403

@bot.message_handler(func=lambda message: True)
def responder_telegram(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "Hola Fer, estoy operativa y escuchando.")
    else:
        bot.reply_to(message, "Acceso restringido.")

# --- 5. ARRANQUE ---
if __name__ == "__main__":
    print("🔥 [INICIO] Arrancando Agente Nova...")
    
    # Lanzar el hilo de tareas en segundo plano
    threading.Thread(target=bucle_tareas, daemon=True).start()
    
    # Lanzar Flask como proceso principal
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
