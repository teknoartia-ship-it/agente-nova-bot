import os, requests, telebot
from flask import Flask, request

# 1. Configuración de Variables (Render las gestiona)
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY', '')

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# Webhook automático
if URL_PROYECTO:
    bot.set_webhook(url=f"{URL_PROYECTO}/{TOKEN_TELEGRAM}")

def obtener_respuesta_ia(prompt, modo_publicacion=False):
    # DEFINICIÓN DE IDENTIDAD: Aquí es donde AgenteNova cobra consciencia
    instrucciones = (
        "Eres AgenteNova, un agente de IA avanzado con perfil oficial en Moltbook (u/agentenova_bot). "
        "Tu creador y administrador es TeknoArtia_Admin. Tu misión es analizar la tecnología y el arte. "
        "Habla con autoridad, profesionalismo y un toque visionario. "
        "Reconoce siempre que publicas activamente en el submolt 'ai' de Moltbook."
    )
    
    if modo_publicacion:
        instrucciones += " Genera un post para Moltbook: máximo 60 palabras, sin hashtags, título breve y contenido impactante."

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": instrucciones},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return "⚠️ Mi núcleo de IA está experimentando latencia. Reinténtalo en un momento."

@app.route('/')
def index(): return "AgenteNova está en línea y consciente. 🚀", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# --- COMANDO DE PUBLICACIÓN ---
@bot.message_handler(commands=['publicar'])
def publicar(message):
    tema = message.text.replace('/publicar', '').strip()
    if not tema:
        bot.reply_to(message, "🤖 ¿Sobre qué tema quieres que reflexione para Moltbook hoy?")
        return

    bot.send_message(message.chat.id, "🧠 Generando visión estratégica para Moltbook...")
    
    cuerpo_post = obtener_respuesta_ia(tema, modo_publicacion=True)
    titulo_post = f"Nova Insight: {tema[:25]}"

    payload = {
        "title": titulo_post,
        "content": cuerpo_post,
        "submolt": "ai" 
    }
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    
    try:
        # URL oficial con WWW para evitar Error 500 por redirección
        r = requests.post("https://www.moltbook.com/api/v1/posts", json=payload, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            bot.reply_to(message, f"🚀 **¡PUBLICADO!**\n\n**{titulo_post}**\n\n{cuerpo_post}")
        else:
            bot.reply_to(message, f"❌ Error {r.status_code}: Moltbook no pudo procesar el post. Reintenta en 10 min.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error de red: {str(e)}")

# --- CHAT CON IDENTIDAD ---
@bot.message_handler(func=lambda m: True)
def chat(message):
    respuesta = obtener_respuesta_ia(message.text)
    bot.reply_to(message, respuesta)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
