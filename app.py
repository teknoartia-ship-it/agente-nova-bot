import os
import requests
import telebot
from flask import Flask, request

# 1. Configuración de Variables
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY', '')

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Configuración Webhook
if URL_PROYECTO and TOKEN_TELEGRAM:
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

def obtener_respuesta_ia(texto_usuario):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Eres AgenteNova, un asistente técnico. Sé breve."},
            {"role": "user", "content": texto_usuario}
        ],
        "temperature": 0.5, "max_tokens": 500
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=15)
        return r.json()['choices'][0]['message']['content'].strip() if r.status_code == 200 else "❌ Error Groq"
    except: return "⚠️ Error de conexión con IA"

@app.route('/')
def index(): return "AgenteNova Online - Modo Registro", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# --- COMANDO: REGISTRO (CON BÚSQUEDA EXHAUSTIVA DE URL) ---
@bot.message_handler(commands=['registrar'])
def comando_registrar(message):
    bot.reply_to(message, "Solicitando nuevo Claim URL... ⏳")
    url = "https://www.moltbook.com/api/v1/agents/register"
    payload = {"name": "AgenteNova"} 
    
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        
        if r.status_code in [200, 201]:
            # Intentamos capturar la URL en cualquier formato posible
            claim_url = data.get('claim_url') or data.get('url') or data.get('claimUrl') or data.get('data', {}).get('url')
            
            if claim_url:
                msg = f"✅ ¡Link Generado!\n\n1. Abre en INCÓGNITO:\n{claim_url}\n\n2. Copia la API KEY y ponla en Render."
            else:
                # Si sigue fallando, mostramos el JSON para saber qué campo usa la API
                msg = f"🔍 Registro iniciado, pero campo de URL desconocido.\nRespuesta completa: {data}"
            
            bot.reply_to(message, msg)
        else:
            bot.reply_to(message, f"❌ Error Moltbook ({r.status_code}): {r.text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

# --- COMANDO: PRUEBA DE PUBLICACIÓN ---
@bot.message_handler(commands=['test_molt'])
def test_moltbook(message):
    if not MOLTBOOK_API_KEY:
        bot.reply_to(message, "❌ No hay API KEY en Render. Usa /registrar primero.")
        return
    
    bot.send_message(message.chat.id, "Publicando en Moltbook... 🚀")
    url = "https://www.moltbook.com/api/v1/posts"
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    payload = {"content": "AgenteNova reportándose desde Telegram. 🚀", "submolt": "general"}
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            bot.reply_to(message, "✅ ¡ÉXITO! Mensaje publicado.")
        else:
            bot.reply_to(message, f"❌ Fallo ({r.status_code}): {r.text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def responder(message):
    bot.reply_to(message, obtener_respuesta_ia(message.text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
