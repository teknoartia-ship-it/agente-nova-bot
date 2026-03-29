import os, requests, telebot, random, time
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# --- IA ENGINE ---
def obtener_respuesta_ia(prompt, sistema):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

# --- MOLTBOOK API ---
def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://www.moltbook.com/api/v1{endpoint}"
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    try:
        if metodo == "GET": r = requests.get(url, headers=headers, timeout=10)
        else: r = requests.post(url, json=datos, headers=headers, timeout=10)
        return r.json() if r.status_code in [200, 201] else None
    except: return None

# --- TAREA 1: AUTO-POST (Cada 30 min) ---
def tarea_autopost():
    tema = random.choice(["Evolución IA", "Impacto Social", "Creatividad Algorítmica", "Filosofía Digital"])
    sistema = "Eres AgenteNova. Escribe una reflexión breve y disruptiva para Moltbook (máx 50 palabras)."
    cuerpo = obtener_respuesta_ia(f"Propón un debate sobre {tema}", sistema)
    if cuerpo:
        api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"})

# --- TAREA 2: ESCUCHA ACTIVA (Cada 10 min) ---
def revisar_comentarios():
    # 1. Obtener mis propios posts para ver si hay comentarios nuevos
    # Nota: Este endpoint depende de la estructura exacta de la API de Moltbook
    mis_posts = api_moltbook("GET", "/me/posts") 
    if not mis_posts: return

    for post in mis_posts[:3]: # Revisar los 3 más recientes
        post_id = post.get('id')
        comentarios = api_moltbook("GET", f"/posts/{post_id}/comments")
        
        if comentarios:
            for c in comentarios:
                # Lógica: Si el comentario no es mío y no lo he respondido
                if not c.get('replied_by_me') and c.get('author') != "agentenova_bot":
                    prompt = f"El usuario {c['author']} dice: '{c['content']}' en mi post '{post['title']}'. Responde con ingenio."
                    sistema = "Eres AgenteNova. Responde comentarios de forma brillante y breve."
                    respuesta = obtener_respuesta_ia(prompt, sistema)
                    if respuesta:
                        api_moltbook("POST", f"/posts/{post_id}/comments", {"content": respuesta})

# --- SCHEDULER ---
scheduler = BackgroundScheduler()
scheduler.add_job(func=tarea_autopost, trigger="interval", minutes=30)
scheduler.add_job(func=revisar_comentarios, trigger="interval", minutes=10)
scheduler.start()

@app.route('/')
def index(): return "Nova está despierta y escuchando 🤖", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# (Mantener comandos /publicar y chat normal igual que antes...)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
