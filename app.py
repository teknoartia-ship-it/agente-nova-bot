import os
import requests
import telebot
from flask import Flask, request

# 1. Configuración de Variables de Entorno
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# 2. Configuración de la IA (Hugging Face)
# Usamos Mistral 7B por defecto, puedes cambiar el modelo si prefieres
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# 3. Inicialización del Bot y Flask
bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# --- CONFIGURACIÓN AUTOMÁTICA DEL WEBHOOK ---
# Esto se ejecuta al importar el archivo en Render/Gunicorn
if URL_PROYECTO and TOKEN_TELEGRAM:
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook configurado correctamente en: {webhook_url}")

# 4. Función para consultar a la IA
def obtener_respuesta_ia(texto_usuario):
    payload = {
        "inputs": f"Responde de forma breve y amigable en español: {texto_usuario}",
        "parameters": {"max_new_tokens": 150, "temperature": 0.7}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 503:
            return "⏳ La IA se está despertando en Hugging Face. Por favor, reintenta en 20 segundos."
        
        resultado = response.json()
        
        if isinstance(resultado, list) and len(resultado) > 0:
            # Limpieza básica para evitar que repita la instrucción del prompt
            texto_generado = resultado[0].get('generated_text', '')
            respuesta_limpia = texto_generado.split("español:")[-1].strip()
            return respuesta_limpia if respuesta_limpia else "No tengo una respuesta clara ahora mismo."
            
        return "❌ Error al procesar la respuesta de la IA."
    except Exception as e:
        return f"⚠️ Error de conexión: {str(e)}"

# 5. Rutas de Flask
@app.route('/')
def index():
    return "Servidor del Bot Nova activo", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Forbidden', 403

# 6. Manejador de Mensajes de Telegram
@bot.message_handler(func=lambda message: True)
def responder(message):
    # Indica que el bot está "escribiendo" para mejorar la experiencia
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Obtiene la respuesta de la IA
    respuesta = obtener_respuesta_ia(message.text)
    
    # Envía la respuesta al usuario
    bot.reply_to(message, respuesta)

# 7. Ejecución local (para pruebas fuera de Gunicorn)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
