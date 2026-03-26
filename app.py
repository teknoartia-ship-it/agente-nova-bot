import os
import requests
import telebot
from flask import Flask, request

# Variables de entorno
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
# URL de Render (ej: https://tu-app.onrender.com)
URL_PROYECTO = os.environ.get('URL_PROYECTO') 

# URL del modelo en Hugging Face
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM)
app = Flask(__name__)

def obtener_respuesta_ia(texto_usuario):
    payload = {
        "inputs": f"Responde breve en español: {texto_usuario}", 
        "parameters": {"max_new_tokens": 150}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        if response.status_code == 503: 
            return "⏳ El modelo se está cargando en Hugging Face, espera 20 segundos y reintenta."
        
        resultado = response.json()
        if isinstance(resultado, list) and len(resultado) > 0:
            # Limpiamos la respuesta para que no repita el prompt
            respuesta = resultado[0].get('generated_text', '')
            return respuesta.split("Responde breve en español:")[-1].strip()
        return "❌ No pude obtener una respuesta clara."
    except Exception as e: 
        return f"⚠️ Error de conexión: {str(e)}"

@app.route('/')
def index():
    return "Bot Nova Online", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Error', 403

@bot.message_handler(func=lambda message: True)
def responder(message):
    bot.send_chat_action(message.chat.id, 'typing')
    respuesta = obtener_respuesta_ia(message.text)
    bot.reply_to(message, respuesta)

# Esta función registra la URL en Telegram para que sepa dónde enviar los mensajes
def configurar_webhook():
    if URL_PROYECTO:
        bot.remove_webhook()
        # Telegram necesita HTTPS, Render lo da por defecto
        exito = bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")
        if exito:
            print(f"✅ Webhook configurado en: {URL_PROYECTO}")
        else:
            print("❌ Falló la configuración del Webhook")

if __name__ == "__main__":
    configurar_webhook()
    # Usamos el puerto que Render nos asigne
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
