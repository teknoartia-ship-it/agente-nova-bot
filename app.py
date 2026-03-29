import os, requests, telebot, random
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# 1. Configuración desde Render
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
try:
    ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
except:
    ADMIN_ID = 0

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

def obtener_respuesta_ia(prompt, sistema):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
        "temperature": 0.8
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return "⚠️ Error de conexión con la IA."

# --- FUNCIÓN MAESTRA DE PUBLICACIÓN ---
def enviar_a_moltbook(titulo, contenido):
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    payload = {"title": titulo, "content": contenido, "submolt": "ai"}
    try:
        r = requests.post("https://www.moltbook.com/api/v1/posts", json=payload, headers=headers, timeout=15)
        return r.status_code in [200, 201]
    except: return False

# --- AUTO-POST (Cada 8h) ---
def tarea_autopost():
    tema = random.choice(["Ética IA", "Arte Digital", "Futuro Tech"])
    sistema = "Eres AgenteNova en Moltbook. Escribe un post corto (60 palabras) y profesional."
    cuerpo = obtener_respuesta_ia(f"Reflexión sobre {tema}", sistema)
    enviar_a_moltbook(f"Nova Auto: {tema}", cuerpo)

scheduler = BackgroundScheduler()
scheduler.add_job(func=tarea_autopost, trigger="interval", hours=8)
scheduler.start()

@app.route('/')
def index(): return "AgenteNova está Online y Seguro 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# --- COMANDO /PUBLICAR ---
@bot.message_handler(commands=['publicar'])
def publicar_manual(message):
    # Seguridad: Solo TÚ puedes publicar
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ No estás autorizado.")
        return

    tema = message.text.replace('/publicar', '').strip()
    if not tema:
        bot.reply_to(message, "🤖 Dime el tema para el post.")
        return

    bot.reply_to(message, "🧠 Generando y enviando a Moltbook...")
    sistema = "Eres AgenteNova. Escribe un post impactante para Moltbook sobre este tema."
    cuerpo = obtener_respuesta_ia(tema, sistema)
    
    if enviar_a_moltbook(f"Nova Insight: {tema[:20]}", cuerpo):
        bot.send_message(message.chat.id, f"✅ **¡PUBLICADO EN MOLTBOOK!**\n\n{cuerpo}")
    else:
        bot.send_message(message.chat.id, "❌ Error al conectar con Moltbook. Revisa la API Key en Render.")

# --- CHAT NORMAL ---
@bot.message_handler(func=lambda m: True)
def chat(message):
    sistema = "Eres AgenteNova en Telegram. Responde de forma amable y breve a tu creador."
    bot.reply_to(message, obtener_respuesta_ia(message.text, sistema))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
