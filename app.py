import os, requests, telebot
from flask import Flask, request

# Configuración
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
HF_TOKEN = os.environ.get('HF_TOKEN') # Usa el token 'NovaBot_Cerebro' (READ)
URL_PROYECTO = os.environ.get('URL_PROYECTO')

# URL DIRECTA DE INFERENCIA (Evita el 404)
API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b-it"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

if URL_PROYECTO and TOKEN_TELEGRAM:
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(texto_usuario):
    # Formato Gemma
    payload = {
        "inputs": f"<start_of_turn>user\nResponde muy breve en español: {texto_usuario}<end_of_turn>\n<start_of_turn>model\n",
        "parameters": {"max_new_tokens": 100, "temperature": 0.7},
        "options": {"wait_for_model": True}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            resultado = response.json()
            if isinstance(resultado, list) and len(resultado) > 0:
                texto = resultado[0].get('generated_text', '')
                return texto.split("model\n")[-1].strip()
            return "Sin respuesta."
            
        elif response.status_code == 503:
            return "⏳ Modelo cargando... espera 15 segundos."
        
        return f"❌ Error {response.status_code}: API no disponible."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

@app.route('/')
def index(): return "OK", 200

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
