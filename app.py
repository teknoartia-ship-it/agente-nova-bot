import os
import requests
import telebot
from telebot import TeleBot
from flask import Flask, request

# Configuración desde variables de entorno
TOKEN_TELEGRAM = os.environ.get("TOKEN_TELEGRAM")
HF_TOKEN = os.environ.get("HF_TOKEN")
# Usamos un modelo más ligero (Gemma) para evitar esperas infinitas
API_URL = "https://api-inference.huggingface.co/models/google/gemma-2-2b-it"

bot = TeleBot(TOKEN_TELEGRAM)
app = Flask(__name__)

def cerebro_ia(texto):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": f"Responde de forma breve y en español a lo siguiente: {texto}",
        "parameters": {"max_new_tokens": 150, "return_full_text": False},
        "options": {"wait_for_model": True}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        # Manejo de la respuesta según el formato de Hugging Face
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('generated_text', 'No tengo respuesta ahora.')
        elif isinstance(result, dict) and 'generated_text' in result:
            return result['generated_text']
        else:
            return "⚠️ La IA se está desperezando, reintenta en 15 segundos."
    except Exception as e:
        return "⚠️ El cerebro está tardando en conectar. Prueba de nuevo ahora."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ ¡Nova activa! Usa /analizar seguido de tu mensaje.")

@bot.message_handler(commands=['analizar'])
def handle_analizar(message):
    pregunta = message.text.replace('/analizar', '').strip()
    if not pregunta:
        bot.reply_to(message, "Escribe algo después de /analizar (ejemplo: /analizar hola)")
        return
    
    msg_espera = bot.reply_to(message, "🧠 Nova pensando...")
    respuesta = cerebro_ia(pregunta)
    bot.edit_message_text(respuesta, message.chat.id, msg_espera.message_id)

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    # Limpiamos y ponemos el webhook manualmente al entrar a la URL
    bot.remove_webhook()
    bot.set_webhook(url='https://' + request.host + '/' + TOKEN_TELEGRAM)
    return "<h1>Servidor de Nova: ONLINE</h1><p>El Webhook ha sido configurado.</p>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
