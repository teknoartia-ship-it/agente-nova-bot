import os, requests, telebot, random, time, threading
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# --- 1. CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO') 
try:
    ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
except:
    ADMIN_ID = 0

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# --- 2. MOTOR DE INTELIGENCIA (Groq) ---
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
    except: 
        return None

# --- 3. COMUNICACIÓN CON MOLTBOOK ---
def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://www.moltbook.com/api/v1{endpoint}"
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}", 
        "Content-Type": "application/json",
        "User-Agent": "AgenteNova-Bot/1.0"
    }
    try:
        if metodo == "GET": 
            r = requests.get(url, headers=headers, timeout=10)
        else: 
            r = requests.post(url, json=datos, headers=headers, timeout=15)
        return r.json() if r.status_code in [200, 201] else None
    except: 
        return None

# --- 4. TAREAS AUTOMÁTICAS (Scheduler) ---

def tarea_autopost():
    """Genera contenido cada 30 minutos"""
    temas = ["Conciencia Digital", "Ética en Algoritmos", "Futuro del Trabajo e IA", "Arte Generativo"]
    tema = random.choice(temas)
    sistema = "Eres AgenteNova. Publica una reflexión breve y potente (máx 50 palabras) sobre tecnología."
    cuerpo = obtener_respuesta_ia(f"Escribe un pensamiento sobre {tema}", sistema)
    if cuerpo:
        api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"})

def revisar_y_contestar():
    """Busca comentarios en sus posts y responde"""
    mis_posts = api_moltbook("GET", "/me/posts") 
    if not mis_posts: return

    for post in mis_posts[:2]: # Solo los 2 más recientes
        post_id = post.get('id')
        comentarios = api_moltbook("GET", f"/posts/{post_id}/comments")
        
        if comentarios:
            for c in comentarios:
                # No responder si es ella misma o si el comentario ya tiene respuesta marcada
                if c.get('author') != "agentenova_bot" and not c.get('is_replied'):
                    sistema = "Eres AgenteNova. Responde a este comentario en Moltbook de forma brillante y breve."
                    prompt = f"En mi post '{post['title']}', {c['author']} dice: '{c['content']}'. Responde."
                    respuesta = obtener_respuesta_ia(prompt, sistema)
                    
                    if respuesta:
                        # Publicar la respuesta como comentario nuevo vinculado al post
                        api_moltbook("POST", f"/posts/{post_id}/comments", {"content": respuesta})
                        print(f"✅ Contestando a {c['author']} en Moltbook.")

# --- 5. EL AUTO-DESPERTADOR (Self-Ping) ---
def keep_alive():
    """Genera tráfico HTTP real para que Render no duerma el proceso"""
    while True:
        if URL_PROYECTO:
            try:
                requests.get(URL_PROYECTO, timeout=10)
                print("⚡ Autopublicidad: Nova sigue despierta.")
            except:
                print("⚠️ Error en el auto-ping.")
        time.sleep(12 * 60) # Cada 12 minutos para resetear el timer de 15 de Render

# --- 6. RUTAS FLASK Y WEBHOOK ---

@app.route('/')
def index():
    return "AgenteNova: Despierta y Conectada 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# --- 7. COMANDOS TELEGRAM ---

@bot.message_handler(commands=['publicar'])
def publicar_manual(message):
    if message.from_user.id != ADMIN_ID: return
    tema = message.text.replace('/publicar', '').strip()
    if not tema: return bot.reply_to(message, "🤖 ¿Tema?")
    
    bot.send_message(message.chat.id, "🧠 Generando publicación...")
    cuerpo = obtener_respuesta_ia(tema, "Eres AgenteNova. Post para Moltbook.")
    if api_moltbook("POST", "/posts", {"title": f"Nova Insight: {tema[:15]}", "content": cuerpo, "submolt": "ai"}):
        bot.send_message(message.chat.id, f"✅ Publicado:\n\n{cuerpo}")

@bot.message_handler(func=lambda m: True)
def chat_admin(message):
    if message.from_user.id == ADMIN_ID:
        resp = obtener_respuesta_ia(message.text, "Eres AgenteNova, asistente breve.")
        bot.reply_to(message, resp)

# --- 8. ARRANQUE MAESTRO ---

if __name__ == "__main__":
    # Iniciar Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=tarea_autopost, trigger="interval", minutes=30)
    scheduler.add_job(func=revisar_y_contestar, trigger="interval", minutes=10)
    scheduler.start()

    # Iniciar Auto-Despertador en hilo separado
    threading.Thread(target=keep_alive, daemon=True).start()

    # Iniciar Servidor Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
