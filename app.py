import os, requests, telebot
from flask import Flask, request

# 1. Configuración de Variables (Render ya las tiene)
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY', '')

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Webhook automático
if URL_PROYECTO:
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(prompt, sistema="Eres AgenteNova, experto en IA. Sé breve y profesional."):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return "⚠️ Error al generar texto con IA."

@app.route('/')
def index(): return "AgenteNova está listo en m/ai. 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# --- COMANDO DE PUBLICACIÓN EN SUBMOLT AI ---
@bot.message_handler(commands=['publicar'])
def publicar_en_ai(message):
    tema = message.text.replace('/publicar', '').strip()
    if not tema:
        bot.reply_to(message, "⚠️ Dime un tema. Ejemplo: `/publicar El futuro de la IA`")
        return

    bot.send_message(message.chat.id, "🤖 Redactando para el submolt 'ai'...")
    
    # IA genera contenido optimizado para evitar errores 500
    cuerpo_post = obtener_respuesta_ia(f"Escribe un post corto (máximo 50 palabras) sobre: {tema}. Sin hashtags ni emojis raros.")
    titulo_post = f"IA Insight: {tema[:25]}"

    payload = {
        "title": titulo_post,
        "content": cuerpo_post,
        "submolt": "ai"  # <--- Publicamos en el submolt específico de IA
    }
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    
    try:
        r = requests.post("https://www.moltbook.com/api/v1/posts", json=payload, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            bot.reply_to(message, f"✅ **¡ÉXITO EN m/ai!**\n\n**{titulo_post}**\n\n{cuerpo_post}")
        else:
            bot.reply_to(message, f"❌ Moltbook rechazó el post ({r.status_code}). Intentémoslo en un rato.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error de conexión: {str(e)}")

# --- CHAT GENERAL ---
@bot.message_handler(func=lambda m: True)
def chat(message):
    bot.reply_to(message, obtener_respuesta_ia(message.text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
