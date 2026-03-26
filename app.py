import os
from flask import Flask, request
import telebot

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
# Tu URL de Render ya configurada
URL_PROYECTO = "https://agente-nova-bot.onrender.com" 

bot = telebot.TeleBot(TOKEN_TELEGRAM)
app = Flask(__name__)

# --- RUTAS ---

@app.route('/')
def index():
    return "Servidor de Nova: ONLINE", 200

# Ruta segura usando el Token
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
    bot.reply_to(message, "¡Hola! Soy Nova. Ya estoy configurada correctamente.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Mensaje recibido. Procesando...")

# --- CONFIGURACIÓN ÚNICA DEL WEBHOOK ---

def configurar_webhook():
    if not TOKEN_TELEGRAM:
        print("Error: No se encontró la variable TOKEN_TELEGRAM")
        return
    
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"Webhook configurado en: {webhook_url}")
    except Exception as e:
        print(f"Error al configurar Webhook: {e}")

# Ejecutar configuración al arrancar el servidor
configurar_webhook()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
