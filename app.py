import os
import requests
import telebot
from flask import Flask, request

# 1. Configuración de Variables de Entorno
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# 2. Configuración de la IA (Usamos Zephyr para mayor estabilidad)
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# 3. Inicialización
bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# --- CONFIGURACIÓN AUTOMÁTICA DEL WEBHOOK ---
if URL_PROYECTO and TOKEN_TELEGRAM:
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook configurado en: {webhook_url}")

# 4. Función de IA corregida
def obtener_respuesta_ia(texto_usuario):
    # Prompt formateado para modelos de Chat
    prompt = f"<|system|>\nResponde de forma breve y amigable en español.</s>\n<|user|>\n{texto_usuario}</s>\n<|assistant|>\n"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.7,
            "return_full_text": False  # Evita que repita tu pregunta
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        resultado = response.json()

        # Caso 1: El modelo se está cargando
        if response.status_code == 503 or "estimated_time" in str(resultado):
            return "⏳ La IA se está preparando (Hugging Face está cargando el modelo). Reintenta en 15 segundos."

        # Caso 2: Respuesta exitosa
        if isinstance(resultado, list) and len(resultado) > 0:
            texto = resultado[0].get('generated_text', '').strip()
            # Limpieza extra por si acaso
            return texto if texto else "No supe qué responder a eso."

        # Caso 3: Error en el JSON o API
        print(f"DEBUG Error HF: {resultado}")
        return "❌ La IA está ocupada o devolvió un formato extraño. Prueba de nuevo."

    except Exception as e:
        print(f"DEBUG Exception: {str(e)}")
        return "⚠️ Error de conexión con el cerebro de la IA."

# 5. Rutas de Flask
@app.route('/')
def index():
    return "Bot Nova Operativo", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# 6. Manejador de Mensajes
@bot.message_handler(func=lambda message: True)
def responder(message):
    bot.send_chat_action(message.chat.id, 'typing')
    respuesta = obtener_respuesta_ia(message.text)
    bot.reply_to(message, respuesta)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
