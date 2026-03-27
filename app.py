import os
import requests
import telebot
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# URL optimizada para la API de Inferencia gratuita
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

if URL_PROYECTO and TOKEN_TELEGRAM:
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(texto_usuario):
    # Formato de chat para Zephyr
    prompt = f"<|system|>\nResponde breve en español.</s>\n<|user|>\n{texto_usuario}</s>\n<|assistant|>\n"
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 150, "temperature": 0.7, "return_full_text": False}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        
        # Si no es un JSON, capturamos el error antes de que explote
        if "application/json" not in response.headers.get("Content-Type", ""):
            return f"⚠️ Error de Servidor: La IA no devolvió JSON. (Código: {response.status_code})"

        resultado = response.json()

        if response.status_code == 503 or "estimated_time" in str(resultado):
            return "⏳ El modelo se está cargando... reintenta en 15 segundos."
        
        if isinstance(resultado, list) and len(resultado) > 0:
            return resultado[0].get('generated_text', '').strip()
        
        if isinstance(resultado, dict) and "error" in resultado:
            return f"❌ IA dice: {resultado['error']}"
            
        return "❌ Error inesperado en el formato de la IA."
    except Exception as e:
        return f"⚠️ Error técnico: {str(e)}"

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
    return 'Forbidden', 403

@bot.message_handler(func=lambda message: True)
def responder(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, obtener_respuesta_ia(message.text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
