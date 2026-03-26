import os
import requests
import telebot
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = ""

API_URL = ""
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM)
app = Flask(name)

def obtener_respuesta_ia(texto_usuario):
payload = {"inputs": f"Responde breve en español: {texto_usuario}", "parameters": {"max_new_tokens": 100}}
try:
response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
if response.status_code == 503: return "⏳ Cargando... Reintenta en 10 seg."
resultado = response.json()
if isinstance(resultado, list) and len(resultado) > 0:
return resultado[0].get('generated_text', '').replace(payload["inputs"], "").strip()
return "❌ Error en respuesta."
except Exception as e: return f"⚠️ Error: {str(e)}"

@app.route('/')
def index(): return "OK", 200

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
bot.reply_to(message, obtener_respuesta_ia(message.text))

def configurar_webhook():
bot.remove_webhook()
bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

configurar_webhook()

if name == "main":
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
