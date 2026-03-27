import os, requests, telebot
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# URL OBLIGATORIA PARA 2026 (Router)
API_URL = "https://router.huggingface.co/hf-inference/models/google/gemma-2b-it"
headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

if URL_PROYECTO and TOKEN_TELEGRAM:
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(texto_usuario):
    payload = {
        "inputs": f"<start_of_turn>user\nResponde breve en español: {texto_usuario}<end_of_turn>\n<start_of_turn>model\n",
        "parameters": {"max_new_tokens": 150, "temperature": 0.7},
        "options": {"wait_for_model": True}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res = response.json()
            return res[0].get('generated_text', '').split("model\n")[-1].strip()
        return f"❌ Error {response.status_code}: API no disponible."
    except:
        return "⚠️ Error de conexión."

@app.route('/')
def index(): return "OK", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return '', 200
    return 'Forbidden', 403

@bot.message_handler(func=lambda message: True)
def responder(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, obtener_respuesta_ia(message.text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
