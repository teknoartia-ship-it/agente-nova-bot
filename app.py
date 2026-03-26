import os
import requests
import telebot
from flask import Flask, request

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = "https://agente-nova-bot.onrender.com"

# MODELO QWEN: Sin restricciones de licencia y muy rápido
API_URL = "https://router.huggingface.co/hf-inference/models/Qwen/Qwen2.5-7B-Instruct"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM)
app = Flask(__name__)

def obtener_respuesta_ia(texto_usuario):
    # Formato de mensaje optimizado para chat
    payload = {
        "inputs": f"<|im_start|>system\nEres Nova, una asistente divertida y breve.<|im_end|>\n<|im_start|>user\n{texto_usuario}<|im_end|>\n<|im_start|>assistant\n",
        "parameters": {"max_new_tokens": 100, "temperature": 0.7, "return_full_text": False}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        resultado = response.json()
        
        if response.status_code == 503:
            return "⏳ Mi cerebro se está despertando. Dame 15 segundos y vuelve a preguntarme."

        if isinstance(resultado, list) and len(resultado) > 0:
            return resultado[0].get('generated_text', '').strip()

        if isinstance(resultado, dict) and "error" in resultado:
            return f"❌ Nota de mi sistema: {resultado['error']}"

        return "🤔 No he podido procesar eso, ¿probamos otra vez?"
    except Exception as e:
        return f"⚠️ Error de conexión: {str(e)}"

# --- RUTAS ---

@app.route('/')
def index():
    return "Nova está viva", 200

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

def configurar_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

configurar_webhook()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
