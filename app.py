import os
import telebot
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# Configuración de Tokens
TOKEN = os.getenv('TELEGRAM_TOKEN')
# Opcional: Si consigues un Token de Hugging Face (Gratis), ponlo en Render como HF_TOKEN
HF_TOKEN = os.getenv('HF_TOKEN') 

bot = telebot.TeleBot(TOKEN)

# --- FUNCIÓN IA (MISTRAL/LLAMA) ---
def cerebro_ia(texto):
    if not HF_TOKEN:
        return "🤖 Modo básico: Conecta tu HF_TOKEN en Render para activar Llama 3."
    
    api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": f"Eres Nova, un agente experto. Responde breve: {texto}"}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        return response.json()[0]['generated_text'].split("Responde breve:")[1]
    except:
        return "🤯 Mi cerebro está saturado, inténtalo en un momento."

# --- COMANDO: BUSCAR ---
@bot.message_handler(commands=['buscar'])
def buscar(message):
    query = message.text.replace('/buscar', '').strip()
    if not query: return bot.reply_to(message, "🔍 ¿Qué busco?")
    
    try:
        res = requests.get(f"https://www.google.com/search?q={query}", headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        enlaces = [f"🔹 {h3.text}\n🔗 {h3.find_parent('a')['href'].split('/url?q=')[1].split('&')[0]}" 
                   for h3 in soup.find_all('h3')[:3]]
        bot.reply_to(message, "\n\n".join(enlaces) if enlaces else "No hay resultados.", disable_web_page_preview=True)
    except:
        bot.reply_to(message, "❌ Error en la búsqueda.")

# --- COMANDO: TRADUCIR ---
@bot.message_handler(commands=['traducir'])
def traducir(message):
    texto = message.text.replace('/traducir', '').strip()
    if not texto: return bot.reply_to(message, "🌍 Dime qué traducir.")
    
    res = GoogleTranslator(source='auto', target='es').translate(texto)
    bot.reply_to(message, f"✅ **Traducción:**\n{res}")

# --- COMANDO: ANALIZAR (IA) ---
@bot.message_handler(commands=['analizar'])
def analizar(message):
    idea = message.text.replace('/analizar', '').strip()
    bot.reply_to(message, cerebro_ia(idea))

# --- INICIO ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **Nova System Online**\n\n/buscar [tema]\n/traducir [texto]\n/analizar [idea]\n\nListo para Moltbook.")

if __name__ == "__main__":
    bot.infinity_polling()
