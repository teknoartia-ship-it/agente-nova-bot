import os, telebot, requests, threading, time
from flask import Flask

app = Flask(__name__)
@app.route('/')
def health(): return "OK", 200

# Configuración de Tokens
TOKEN = os.getenv('TELEGRAM_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')
bot = telebot.TeleBot(TOKEN)

def cerebro_ia(texto):
    if not HF_TOKEN: return "⚠️ Configura el HF_TOKEN en Render."
    # Cambiamos a un modelo que responde al instante (Facebook Blenderbot)
    url = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": texto}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        resultado = res.json()
        # Este modelo devuelve una estructura distinta, la ajustamos:
        if isinstance(resultado, list) and 'generated_text' in resultado[0]:
            return resultado[0]['generated_text']
        elif 'error' in resultado:
            return f"🤯 Hugging Face dice: {resultado['error']}"
        else:
            return "❌ Respuesta inesperada del cerebro."
    except Exception as e:
        return f"❌ Error: {str(e)}"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ ¡Nova viva! Prueba con /analizar hola")

@bot.message_handler(commands=['analizar'])
def ana(m):
    pregunta = m.text.replace('/analizar', '').strip()
    if not pregunta:
        return bot.reply_to(m, "Escribe algo después de /analizar")
    bot.reply_to(m, cerebro_ia(pregunta))

if __name__ == "__main__":
    # Importante: Limpiamos conexiones viejas
    bot.remove_webhook()
    time.sleep(1)
    # Arrancamos el bot en un hilo separado
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
