import os
import requests
import telebot
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# Cambiamos a un modelo muy ligero y estable
API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

if URL_PROYECTO and TOKEN_TELEGRAM:
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(texto_usuario):
    payload = {"inputs": texto_usuario}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        resultado = response.json()
        
        # LOG DE DEBUG (Mira esto en Render si falla)
        print(f"DEBUG HF Status: {response.status_code}")
        print(f"DEBUG HF Res: {resultado}")

        if response.status_code == 503:
            return "⏳ Modelo cargando... reintenta en 10s."
        
        if isinstance(resultado, list) and len(resultado) > 0:
            return resultado[0].get('generated_text', 'No entiendo eso.')
        
        if isinstance(resultado, dict) and "error" in resultado:
            return f"❌ Error IA: {resultado['error']}"
            
        return "❌ Error de respuesta API."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

@app.route('/')
def index(): return "OK", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@bot.message_handler(func=lambda message: True)
def responder(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, obtener_respuesta_ia(message.text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
