import os
import requests
from flask import Flask, request
import telebot

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = "https://agente-nova-bot.onrender.com"

# Configuración de Hugging Face (Modelo recomendado: Mistral)
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM)
app = Flask(__name__)

# --- CEREBRO (IA) ---

def obtener_respuesta_ia(texto_usuario):
    """Envía el mensaje a Hugging Face y devuelve la respuesta de la IA"""
    payload = {
        "inputs": f"Responde de forma breve y amable en español: {texto_usuario}",
        "parameters": {"max_new_tokens": 150, "temperature": 0.7}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        resultado = response.json()
        
        # Hugging Face devuelve una lista con el texto generado
        if isinstance(resultado, list) and len(resultado) > 0:
            return resultado[0]['generated_text'].split("espauñol:")[-1].strip()
        return "Lo siento, estoy teniendo problemas para pensar ahora mismo."
    except Exception as e:
        print(f"Error IA: {e}")
        return "Mi cerebro está desconectado temporalmente."

# --- RUTAS ---

@app.route('/')
def index():
    return "Servidor de Nova: ONLINE y PENSANDO", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Error', 403

# --- LÓGICA DEL BOT ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Soy Nova. Mi conexión es estable y mi cerebro de IA está activo. ¿En qué puedo ayudarte?")

@bot.message_handler(func=lambda message: True)
def responder(message):
    # Aquí es donde ocurre la magia: Nova "piensa" antes de contestar
    respuesta_ia = obtener_respuesta_ia(message.text)
    bot.reply_to(message, respuesta_ia)

# --- INICIO ---

def configurar_webhook():
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"Webhook OK: {webhook_url}")
    except Exception as e:
        print(f"Error Webhook: {e}")

configurar_webhook()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
