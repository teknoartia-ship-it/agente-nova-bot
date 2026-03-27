import os
import requests
import telebot
from flask import Flask, request

# Configuración
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# URL DEFINITIVA PARA 2026 (Ruta directa de Inferencia)
API_URL = API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b-it"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Configuración del Webhook
if URL_PROYECTO and TOKEN_TELEGRAM:
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(texto_usuario):
    # Formato optimizado para Zephyr
    prompt = f"<|system|>\nResponde breve en español.</s>\n<|user|>\n{texto_usuario}</s>\n<|assistant|>\n"
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.7,
            "return_full_text": False
        },
        "options": {"wait_for_model": True} # Obliga a esperar si el modelo está cargando
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # Log de seguridad para ti
        print(f"INFO: Status IA {response.status_code}")

        if response.status_code == 200:
            resultado = response.json()
            if isinstance(resultado, list) and len(resultado) > 0:
                return resultado[0].get('generated_text', '').strip()
            return "No obtuve respuesta del modelo."
            
        elif response.status_code == 503:
            return "⏳ La IA se está despertando. Prueba en 15 segundos."
            
        else:
            # Capturamos el error exacto para no adivinar más
            error_msg = response.text
            print(f"ERROR DETALLE: {error_msg}")
            return f"❌ Error {response.status_code}: Problema con el motor de IA."

    except Exception as e:
        return f"⚠️ Error técnico: {str(e)}"

@app.route('/')
def index():
    return "Bot Nova Live", 200

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
