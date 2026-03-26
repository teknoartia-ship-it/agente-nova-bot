import os
import requests
from flask import Flask, request
from telebot import TeleBot

# Configuración desde Variables de Entorno en Render
TOKEN_TELEGRAM = os.environ.get("TOKEN_TELEGRAM")
HF_TOKEN = os.environ.get("HF_TOKEN")

bot = TeleBot(TOKEN_TELEGRAM)
app = Flask(__name__)

def cerebro_ia(texto):
    # Usamos la URL directa del modelo Phi-3
    API_URL = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    payload = {
        "inputs": f"<|user|>\nResponde muy corto y en español: {texto}<|end|>\n<|assistant|>",
        "parameters": {"max_new_tokens": 50, "return_full_text": False}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        
        # Si Hugging Face devuelve un error, el bot te dirá cuál es
        if response.status_code != 200:
            return f"⚠️ HF dice: {response.status_code} - {response.text[:50]}"
            
        resultado = response.json()
        # Extraemos el texto generado
        if isinstance(resultado, list) and 'generated_text' in resultado[0]:
            return resultado[0]['generated_text'].strip()
        else:
            return "No recibí una respuesta clara de la IA."
            
    except Exception as e:
        return f"❌ Error de conexión: {str(e)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ ¡Nova viva! Prueba con /analizar [tu mensaje]")

@bot.message_handler(commands=['analizar'])
def handle_analizar(message):
    texto_usuario = message.text.replace('/analizar', '').strip()
    if not texto_usuario:
        bot.reply_to(message, "Escribe algo después de /analizar")
        return
    
    msg_espera = bot.reply_to(message, "🧠 Pensando...")
    respuesta = cerebro_ia(texto_usuario)
    bot.edit_message_text(respuesta, message.chat.id, msg_espera.message_id)
@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    # Solo intentamos poner el webhook si entramos manualmente a la URL principal
    try:
        bot.remove_webhook()
        bot.set_webhook(url='https://agente-nova-bot.onrender.com/' + TOKEN_TELEGRAM)
        return "Bot de Nova Configurado y Funcionando", 200
    except Exception as e:
        return f"Error al configurar: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
