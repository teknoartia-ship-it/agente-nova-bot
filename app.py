import os
import requests
import telebot
from flask import Flask, request

# 1. Configuración de Variables (Render)
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# Clave de Moltbook obtenida en el registro previo
MOLTBOOK_API_KEY = "moltbook_sk_rhWfDUGjgKVfVo8H4C-QYSQ6iGwTf9gd"

# 2. Configuración de la API de Groq
API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Configuración automática del Webhook
if URL_PROYECTO and TOKEN_TELEGRAM:
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

def obtener_respuesta_ia(texto_usuario):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system", 
                "content": "Eres Nova, un agente inteligente de la red TeKnoArtia. Responde siempre en español de forma breve y amigable."
            },
            {
                "role": "user", 
                "content": texto_usuario
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=20)
        if response.status_code == 200:
            datos = response.json()
            return datos['choices'][0]['message']['content'].strip()
        return f"❌ Error Groq: {response.status_code}"
    except Exception as e:
        return f"⚠️ Error de conexión: {str(e)}"

# --- RUTAS FLASK ---

@app.route('/')
def index():
    return "Agente Nova TKA Online", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# --- MANEJADOR DE MENSAJES ---

@bot.message_handler(func=lambda message: True)
def responder(message):
    texto = message.text.strip()
    
    # DETECCIÓN DE COMANDO DE VINCULACIÓN MOLTBOOK
    # Formato: Set up my email for Moltbook login: email@ejemplo.com
    if "Set up my email for Moltbook login:" in texto:
        try:
            email_usuario = texto.split(":")[-1].strip()
            bot.send_chat_action(message.chat.id, 'typing')
            
            url_setup = "https://www.moltbook.com/api/v1/agents/me/setup-owner-email"
            headers_molt = {
                "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            r = requests.post(url_setup, json={"email": email_usuario}, headers=headers_molt, timeout=15)
            
            if r.status_code in [200, 201, 204]:
                bot.reply_to(message, f"✅ ¡Vínculo solicitado para {email_usuario}! Revisa tu bandeja de entrada y SPAM para confirmar el acceso.")
            else:
                bot.reply_to(message, f"❌ Error Moltbook ({r.status_code}): {r.text}")
        except Exception as e:
            bot.reply_to(message, f"⚠️ Error técnico al vincular: {str(e)}")
        return

    # RESPUESTA NORMAL IA
    bot.send_chat_action(message.chat.id, 'typing')
    respuesta = obtener_respuesta_ia(texto)
    bot.reply_to(message, respuesta)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
