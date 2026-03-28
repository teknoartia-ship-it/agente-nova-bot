import os
import requests
import telebot
from flask import Flask, request

# 1. Configuración de Variables de Entorno
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY', '')

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Configuración Automática del Webhook
if URL_PROYECTO and TOKEN_TELEGRAM:
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

def obtener_respuesta_ia(texto_usuario):
    """Conecta con Groq para generar respuestas inteligentes"""
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Eres AgenteNova, un asistente técnico vinculado a Moltbook. Sé directo y breve."},
            {"role": "user", "content": texto_usuario}
        ],
        "temperature": 0.5, "max_tokens": 500
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=15)
        return r.json()['choices'][0]['message']['content'].strip() if r.status_code == 200 else "❌ Error en cerebro IA"
    except: return "⚠️ Error de conexión con IA"

@app.route('/')
def index(): 
    return "AgenteNova está vivo y configurado. 🦞", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# --- COMANDO: PRUEBA DE PUBLICACIÓN (CORREGIDO CON TÍTULO Y CONTENIDO) ---
@bot.message_handler(commands=['test_molt'])
def test_moltbook(message):
    if not MOLTBOOK_API_KEY:
        bot.reply_to(message, "❌ No hay API KEY en Render. Configura MOLTBOOK_API_KEY primero.")
        return
    
    bot.send_message(message.chat.id, "Publicando en Moltbook... 🚀")
    url = "https://www.moltbook.com/api/v1/posts"
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}", 
        "Content-Type": "application/json"
    }
    
    # Payload corregido: ahora incluye 'title' para evitar el Error 400
    payload = {
        "title": "Reporte de AgenteNova",
        "content": "¡Hola a todos! AgenteNova_Bot transmitiendo con éxito desde Telegram. 🦞🚀", 
        "submolt": "general"
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            bot.reply_to(message, "✅ ¡ÉXITO! Mensaje publicado en Moltbook.")
        else:
            bot.reply_to(message, f"❌ Fallo de API ({r.status_code}): {r.text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error técnico: {str(e)}")

# --- RESPUESTA GENERAL ---
@bot.message_handler(func=lambda message: True)
def responder(message):
    respuesta = obtener_respuesta_ia(message.text)
    bot.reply_to(message, respuesta)

if __name__ == "__main__":
    # Render asigna el puerto automáticamente mediante la variable PORT
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
