import os, requests, telebot, time
from flask import Flask, request

TOKEN = os.environ.get("TOKEN_TELEGRAM")
GROQ = os.environ.get("GROQ_API_KEY")
URL = os.environ.get("URL_PROYECTO", "").rstrip("/")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route("/")
def index():
    print("🟢 Flask vivo")
    return "OK", 200

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    print("📩 Llego mensaje a webhook")
    data = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(data)
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(func=lambda m: True)
def responder(m):
    print(f"📨 Mensaje recibido de {m.from_user.id}: {m.text}")
    bot.reply_to(m, "Test OK")

if __name__ == "__main__":
    if TOKEN and URL:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{URL}/{TOKEN}")
        print("🔗 Webhook configurado")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))




