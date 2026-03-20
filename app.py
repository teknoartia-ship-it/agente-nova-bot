import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Buscaremos el Token en la configuración de Render, no aquí
TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 ¡Hola! Soy el Agente Nova System, reportándome desde mi nuevo hogar en Render.")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: No se encontró el TELEGRAM_TOKEN")
    else:
        print("🤖 Bot iniciando en Render...")
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.run_polling()
