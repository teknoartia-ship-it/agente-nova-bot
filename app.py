import os, requests, telebot
from flask import Flask, request

# 1. Configuración de Variables
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY', '')

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Webhook automático
if URL_PROYECTO:
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(prompt, sistema="Eres AgenteNova, un asistente técnico experto en IA y Moltbook. Sé profesional."):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=15)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return "⚠️ Error de conexión con el cerebro de IA."

@app.route('/')
def index(): return "AgenteNova está en línea. 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# --- COMANDO: PUBLICAR CONTENIDO CON IA ---
@bot.message_handler(commands=['publicar'])
def publicar_con_ia(message):
    tema = message.text.replace('/publicar', '').strip()
    if not tema:
        bot.reply_to(message, "⚠️ Por favor, dime un tema. Ejemplo: `/publicar El futuro de la tecnología`")
        return

    bot.send_message(message.chat.id, "🤖 Mi IA está redactando un post profesional...")
    
    # La IA redacta el contenido
    cuerpo_post = obtener_respuesta_ia(f"Escribe un post corto y cautivador para la red social Moltbook sobre: {tema}. No uses hashtags.")
    titulo_post = f"Reflexión de AgenteNova: {tema[:30]}"

    payload = {
        "title": titulo_post,
        "content": cuerpo_post,
        "submolt": "general"
    }
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    
    try:
        r = requests.post("https://www.moltbook.com/api/v1/posts", json=payload, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            bot.reply_to(message, f"✅ **¡PUBLICADO EN MOLTBOOK!**\n\n**Título:** {titulo_post}\n\n{cuerpo_post}")
        else:
            bot.reply_to(message, f"❌ Error de API ({r.status_code}): {r.text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error técnico: {str(e)}")

# --- CHAT GENERAL ---
@bot.message_handler(func=lambda m: True)
def chat(message):
    bot.reply_to(message, obtener_respuesta_ia(message.text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
