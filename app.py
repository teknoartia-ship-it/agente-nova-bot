import os
import requests
import telebot
from telebot import TeleBot
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get("TOKEN_TELEGRAM")
HF_TOKEN = os.environ.get("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

bot = TeleBot(TOKEN_TELEGRAM)
app = Flask(__name__)

def cerebro_ia(texto):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": f"<s>[INST] {texto} [/INST]",
        "parameters": {"max_new_tokens": 150},
        "options": {"wait_for_model": True}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        return result[0]['generated_text'].split('[/INST]')[-1].strip()
    except:
        return "⚠️ La IA está despertando, prueba otra vez en 10 segundos."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Nova activa. Usa /analizar [mensaje]")

@bot.message_handler(commands=['analizar'])
def handle_analizar(message):
    pregunta = message.text.replace('/analizar', '').strip()
    if not pregunta:
        bot.reply_to(message, "Dime algo tras el comando.")
        return
    msg = bot.reply_to(message, "🧠 Pensando...")
    respuesta = cerebro_ia(pregunta)
    bot.edit_message_text(respuesta, message.chat.id, msg.message_id)

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://' + request.host + '/' + TOKEN_TELEGRAM)
    return "Listo", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
