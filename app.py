import os
import requests
import telebot
from flask import Flask, request

# 1. Configuración de Variables de Entorno
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# 2. Nueva URL del Router de Hugging Face (Actualizada 2026)
# Formato: https://router.huggingface.co/hf-inference/models/[MODEL_ID]
API_URL = "https://router.huggingface.co/hf-inference/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Configuración del Webhook
if URL_PROYECTO and TOKEN_TELEGRAM:
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

def obtener_respuesta_ia(texto_usuario):
    # Formato de Chat (Prompt Engineering)
    prompt = f"<|system|>\nResponde de forma breve y amigable en español.</s>\n<|user|>\n{texto_usuario}</s>\n<|assistant|>\n"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    
    try:
        # Petición al nuevo Router
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        
        # Si el servidor responde pero no es un JSON válido (ej. mantenimiento)
        if response.status_code != 200:
            try:
                err_data = response.json()
                if "estimated_time" in str(err_data):
                    return "⏳ La IA está arrancando. Reintenta en 20 segundos."
                return f"❌ Error IA ({response.status_code}): {err_data.get('error', 'Error desconocido')}"
            except:
                return f"⚠️ Error del Servidor de IA (Código: {response.status_code})"

        resultado = response.json()

        # Procesar respuesta exitosa
        if isinstance(resultado, list) and len(resultado) > 0:
            return resultado[0].get('generated_text', '').strip()
            
        return "❌ Formato de respuesta no reconocido."

    except Exception as e:
        return f"⚠️ Error de conexión: {str(e)}"

# 3. Rutas de Flask
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

# 4. Manejador de Telegram
@bot.message_handler(func=lambda message: True)
def responder(message):
    bot.send_chat_action(message.chat.id, 'typing')
    respuesta = obtener_respuesta_ia(message.text)
    bot.reply_to(message, respuesta)

# 5. Arranque (Compatible con python app.py)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
