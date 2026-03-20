import os
import telebot
import requests
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

# Configuración de llaves desde Render
TOKEN = os.getenv('TELEGRAM_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Función para que la IA de Hugging Face responda
def cerebro_ia(texto):
    if not HF_TOKEN: 
        return "⚠️ Error: No has configurado el HF_TOKEN en Render."
    
    # Usamos el modelo Mistral (gratuito y potente)
    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": f"Responde de forma muy breve y en español: {texto}"}
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        # Limpiamos la respuesta para que solo salga el texto de la IA
        resultado = res.json()[0]['generated_text']
        return resultado.split("español:")[1].strip() if "español:" in resultado else resultado
    except:
        return "🤯 Mi cerebro está saturado ahora mismo. Prueba en unos segundos."

# Comando para Traducir
@bot.message_handler(commands=['traducir'])
def traducir(message):
    texto = message.text.replace('/traducir', '').strip()
    if not texto:
        return bot.reply_to(message, "Escribe algo para traducir. Ejemplo: `/traducir Hello`")
    res = GoogleTranslator(source='auto', target='es').translate(texto)
    bot.reply_to(message, f"✅ **Traducción:**\n{res}")

# Comando para Buscar en Google
@bot.message_handler(commands=['buscar'])
def buscar(message):
    query = message.text.replace('/buscar', '').strip()
    if not query:
        return bot.reply_to(message, "Dime qué quieres buscar.")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f"https://www.google.com/search?q={query}", headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        enlaces = []
        for h3 in soup.find_all('h3')[:3]:
            titulo = h3.text
            link = h3.find_parent('a')['href'].split('=')[1].split('&')[0]
            enlaces.append(f"🔹 {titulo}\n🔗 {link}")
        bot.reply_to(message, "\n\n".join(enlaces) if enlaces else "No encontré resultados.")
    except:
        bot.reply_to(message, "❌ Error al buscar en la web.")

# Comando para analizar con la IA
@bot.message_handler(commands=['analizar'])
def analizar(message):
    idea = message.text.replace('/analizar', '').strip()
    if not idea:
        return bot.reply_to(message, "Dime qué quieres que analice.")
    bot.reply_to(message, cerebro_ia(idea))

# Mensaje de bienvenida
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **Nova System Online**\n\nPrueba mis comandos:\n/buscar [tema]\n/traducir [texto]\n/analizar [pregunta]")

bot.infinity_polling()
