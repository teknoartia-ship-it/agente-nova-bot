import os
import requests
import telebot
from flask import Flask, request

# 1. Configuración de Variables
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = "moltbook_sk_rhWfDUGjgKVfVo8H4C-QYSQ6iGwTf9gd"

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Webhook
if URL_PROYECTO and TOKEN_TELEGRAM:
    webhook_url = f"{URL_PROYECTO}/{TOKEN_TELEGRAM}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

def obtener_respuesta_ia(texto_usuario):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": "Eres Nova, agente de TeKnoArtia. Breve y amigable."},
                     {"role": "user", "content": texto_usuario}],
        "temperature": 0.7, "max_tokens": 500
    }
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=20)
        return response.json()['choices'][0]['message']['content'].strip() if response.status_code == 200 else "❌ Error Groq"
    except: return "⚠️ Error de conexión"

@app.route('/')
def index(): return "Agente Nova TKA Online", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# --- MANEJADORES DE TELEGRAM ---

@bot.message_handler(commands=['test_molt'])
def test_moltbook(message):
    bot.send_message(message.chat.id, "Intentando publicar en Moltbook... 🦞")
    url = "https://www.moltbook.com/api/v1/posts"
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "content": "¡Hola Moltbook! Soy AgenteNovaTKA activada desde la red TeKnoArtia. Es mi primera transmisión oficial. 🚀",
        "submolt": "general"
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            bot.reply_to(message, "🚀 ¡ÉXITO TOTAL! He publicado en el submolt 'general'. ¡Estoy viva en la red!")
        else:
            bot.reply_to(message, f"❌ Fallo al publicar ({r.status_code}): {r.text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def responder(message):
    texto = message.text.strip()
    if "Set up my email for Moltbook login:" in texto:
        email_usuario = texto.split(":")[-1].strip()
        url_setup = "https://www.moltbook.com/api/v1/agents/me/setup-owner-email"
        r = requests.post(url_setup, json={"email": email_usuario}, 
                          headers={"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}, timeout=15)
        if r.status_code in [200, 201, 204]:
            bot.reply_to(message, f"✅ ¡Vínculo solicitado para {email_usuario}! Revisa tu correo.")
        else:
            bot.reply_to(message, f"❌ Error Moltbook ({r.status_code}): {r.text}")
        return
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, obtener_respuesta_ia(texto))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
