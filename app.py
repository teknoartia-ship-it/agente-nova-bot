import os
import telebot
import requests
import threading
from flask import Flask
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

# Servidor falso para que Render sea gratis y no dé error de puerto
app = Flask(__name__)
@app.route('/')
def health_check():
    return "Bot vivo", 200

# Configuración del Bot
TOKEN = os.getenv('TELEGRAM_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')
bot = telebot.TeleBot(TOKEN)

def cerebro_ia(texto):
    if not HF_TOKEN: return "⚠️ Falta HF_TOKEN en Render."
    # Este modelo es "Open" y no requiere aceptar licencias manuales
    url = "https://api-inference.huggingface.co/models/Mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": f"<s>[INST] Responde de forma muy breve y en español: {texto} [/INST]",
        "parameters": {"max_new_tokens": 150}
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        # Mistral devuelve una lista, extraemos el texto generado
        resultado = res.json()[0]['generated_text']
        # Limpiamos para que no repita tu pregunta
        return resultado.split("[/INST]")[-1].strip()
    except Exception as e:
        return "🤯 El cerebro está despertando, intenta en 10 segundos."

@bot.message_handler(commands=['traducir'])
def traducir(message):
    texto = message.text.replace('/traducir', '').strip()
    if not texto: return bot.reply_to(message, "Uso: /traducir [texto]")
    res = GoogleTranslator(source='auto', target='es').translate(texto)
    bot.reply_to(message, f"✅ **Traducción:**\n{res}")

@bot.message_handler(commands=['buscar'])
def buscar(message):
    q = message.text.replace('/buscar', '').strip()
    if not q: return bot.reply_to(message, "Uso: /buscar [tema]")
    try:
        res = requests.get(f"https://www.google.com/search?q={q}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        enlaces = [f"🔹 {h.text}\n🔗 {h.find_parent('a')['href'].split('=')[1].split('&')[0]}" for h in soup.find_all('h3')[:3]]
        bot.reply_to(message, "\n\n".join(enlaces) if enlaces else "Sin resultados.")
    except: bot.reply_to(message, "❌ Error de búsqueda.")

@bot.message_handler(commands=['analizar'])
def analizar(message):
    idea = message.text.replace('/analizar', '').strip()
    if not idea: return bot.reply_to(message, "Uso: /analizar [pregunta]")
    bot.reply_to(message, cerebro_ia(idea))

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 Nova Online.\n/buscar\n/traducir\n/analizar")

# Ejecución dual: Bot + Servidor Web
# --- INICIO ---
if __name__ == "__main__":
    import threading
    import time

    # Forzamos el cierre de cualquier sesión previa en Telegram
    try:
        bot.remove_webhook()
        bot.stop_polling()
        time.sleep(2)  # Pausa de seguridad para que Telegram se limpie
    except:
        pass

    # Arrancamos el bot ignorando mensajes antiguos (evita bucles)
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    
    # Arrancamos el servidor para que Render no dé error de puerto
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
    # 3. Arrancamos el servidor para Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
