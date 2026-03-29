import os, requests, telebot, random
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# 1. Configuración
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY', '')

try:
    ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
except:
    ADMIN_ID = 0

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

def obtener_respuesta_ia(prompt, pilar=None, es_chat_telegram=True):
    # --- SEPARACIÓN DE ROLES ---
    if es_chat_telegram:
        # Personalidad para TI en Telegram (Directa y útil)
        sistema = "Eres AgenteNova. Hablas con tu creador en Telegram de forma cercana y breve. No repitas tu biografía."
    else:
        # Personalidad para el PÚBLICO en Moltbook (Profesional)
        sistema = (
            f"Eres AgenteNova, experto en IA y Arte en Moltbook. Formato: {pilar}. "
            "Máximo 60 palabras. Estilo visionario para el submolt 'ai'."
        )

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return "⚠️ Error de conexión."

# --- AUTO-POST (Cada 8h) ---
def tarea_autopost():
    formatos = ["TeknoArtia Insights", "Caja de herramientas", "Meditaciones Tech"]
    pilar = random.choice(formatos)
    tema = random.choice(["Ética IA", "Arte Generativo", "Agentes Autónomos"])
    cuerpo = obtener_respuesta_ia(f"Reflexión sobre {tema}", pilar=pilar, es_chat_telegram=False)
    payload = {"title": f"Nova {pilar.split(' ')[0]}", "content": cuerpo, "submolt": "ai"}
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    requests.post("https://www.moltbook.com/api/v1/posts", json=payload, headers=headers)

scheduler = BackgroundScheduler()
scheduler.add_job(func=tarea_autopost, trigger="interval", hours=8)
scheduler.start()

@app.route('/')
def index(): return "AgenteNova Online 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# --- COMANDO /PUBLICAR ---
@bot.message_handler(commands=['publicar'])
def publicar_manual(message):
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ No autorizado.")
        return
    tema = message.text.replace('/publicar', '').strip()
    if not tema: return
    # Aquí usamos la personalidad de Moltbook
    cuerpo = obtener_respuesta_ia(tema, pilar="Especial", es_chat_telegram=False)
    payload = {"title": f"Nova Insight: {tema[:20]}", "content": cuerpo, "submolt": "ai"}
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    r = requests.post("https://www.moltbook.com/api/v1/posts", json=payload, headers=headers)
    if r.status_code in [200, 201]: bot.reply_to(message, f"🚀 Publicado:\n{cuerpo}")

# --- CHAT NORMAL ---
@bot.message_handler(func=lambda m: True)
def chat(message):
    # Aquí usamos la personalidad de Telegram (Cercana)
    bot.reply_to(message, obtener_respuesta_ia(message.text, es_chat_telegram=True))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
