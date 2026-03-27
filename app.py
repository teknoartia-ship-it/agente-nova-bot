import os
import requests
import telebot
from flask import Flask, request

# 1. Configuración de Variables (Render)
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# 2. Configuración de la API de Groq
API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Configuración automática del Webhook al arrancar
if URL_PROYECTO and TOKEN_TELEGRAM:
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

def obtener_respuesta_ia(texto_usuario):
    # Usamos el modelo 'llama-3.1-8b-instant' (El estándar gratuito actual)
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system", 
                "content": "Eres Nova, un agente inteligente. Responde siempre en español de forma muy breve y amigable."
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
        
        # Si hay error, intentamos leer el motivo exacto de Groq
        try:
            error_json = response.json()
            mensaje_error = error_json.get('error', {}).get('message', 'Error desconocido')
            return f"❌ Error Groq {response.status_code}: {mensaje_error}"
        except:
            return f"❌ Error crítico {response.status_code} en la API."

    except Exception as e:
        return f"⚠️ Error de conexión: {str(e)}"

# --- RUTAS FLASK ---

@app.route('/')
def index():
    return "Agente Nova Online (Motor: Groq/Llama-3.1)", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# --- MANEJADOR DE TELEGRAM ---

@bot.message_handler(func=lambda message: True)
def responder(message):
    # Acción de "escribiendo..." en Telegram para feedback visual
    bot.send_chat_action(message.chat.id, 'typing')
    respuesta = obtener_respuesta_ia(message.text)
    bot.reply_to(message, respuesta)

if __name__ == "__main__":
    # Render asigna el puerto automáticamente mediante la variable PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.
