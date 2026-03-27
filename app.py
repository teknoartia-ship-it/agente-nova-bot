import os, requests, telebot
from flask import Flask, request

# Variables de Render
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# Configuración de Groq (Cerebro rápido y estable)
API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

if URL_PROYECTO and TOKEN_TELEGRAM:
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(texto_usuario):
    payload = {
        "model": "llama3-8b-8192", 
        "messages": [
            {"role": "system", "content": "Eres Nova, un agente inteligente. Responde de forma muy breve y amigable en español."},
            {"role": "user", "content": texto_usuario}
        ],
        "temperature": 0.6
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        return f"❌ Error Groq {response.status_code}. Revisa la API Key."
    except Exception as e:
        return f"⚠️ Error técnico: {str(e)}"

@app.route('/')
def index(): return "Agente Nova Online con Groq", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@bot.message_handler(func=lambda message: True)
def responder(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, obtener_respuesta_ia(message.text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
