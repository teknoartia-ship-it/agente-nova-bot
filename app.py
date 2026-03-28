import os, requests, telebot
from flask import Flask, request

TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

if URL_PROYECTO:
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_ia(prompt, sistema="Eres AgenteNova, un experto en tecnología."):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}]
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                     headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload)
    return r.json()['choices'][0]['message']['content'].strip()

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# --- NUEVO COMANDO: PUBLICAR CON IA ---
@bot.message_handler(commands=['publicar'])
def publicar_ia(message):
    tema = message.text.replace('/publicar', '').strip()
    if not tema:
        bot.reply_to(message, "⚠️ Dime de qué quieres que publique. Ej: `/publicar el futuro de la IA`")
        return

    bot.send_message(message.chat.id, "🤖 Redactando y publicando...")
    
    # La IA redacta el contenido para que no sea ignorado por el spam
    texto_ia = obtener_ia(f"Escribe un post corto y profesional para una red social sobre: {tema}. Sin hashtags.")
    
    payload = {
        "title": f"Reflexión: {tema[:50]}",
        "content": texto_ia,
        "submolt": "general"
    }
    
    r = requests.post("https://www.moltbook.com/api/v1/posts", 
                     headers={"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}, json=payload)
    
    if r.status_code in [200, 201]:
        bot.reply_to(message, f"✅ Publicado con éxito:\n\n{texto_ia}")
    else:
        bot.reply_to(message, f"❌ Error: {r.text}")

@bot.message_handler(func=lambda m: True)
def chat(message):
    bot.reply_to(message, obtener_ia(message.text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
