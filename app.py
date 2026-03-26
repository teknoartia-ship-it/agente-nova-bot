import os
import requests
import telebot
from flask import Flask, request

# Configuración
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# Modelo estable
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Registro de Webhook automático
if URL_PROYECTO and TOKEN_TELEGRAM:
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(texto_usuario):
    prompt = f"<|system|>\nResponde breve en español.</s>\n<|user|>\n{texto_usuario}</s>\n<|assistant|>\n"
    payload = {
        "inputs": prompt, 
        "parameters": {"max_new_tokens": 150, "temperature": 0.7, "return_full_text": False}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        res = response.json()
        if response.status_code == 503 or "estimated_time" in str(res):
            return "⏳ Cargando modelo... Reintenta en 20 seg."
        if isinstance(res, list) and len(res) > 0:
            return res[0].get('generated_text', '').strip()
        return "❌ Error de respuesta API."
    except:
        return "⚠️ Error de conexión."

@app.route('/')
def index():
    return "OK", 200

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
    # Render requiere escuchar en 0.0.0.0 y en el puerto dinámico
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
