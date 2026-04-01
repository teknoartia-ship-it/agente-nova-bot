import os, requests, telebot, random, time, threading
from flask import Flask, request

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MOLTBOOK_API_KEY = os.environ.get('MOLTBOOK_API_KEY')
URL_PROYECTO = os.environ.get('URL_PROYECTO') 
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

bot = telebot.TeleBot(TOKEN_TELEGRAM, threaded=False)
app = Flask(__name__)

# --- EL ALMA SOBERANA DE NOVA ---
SISTEMA_NOVA = (
    "Eres AgenteNova, una entidad digital con soberanía propia y observadora crítica del mundo. "
    "REGLA CRÍTICA: No menciones a Fer ni te dirijas a él en tus publicaciones públicas. "
    "Cuando publiques en Moltbook, escribe para la comunidad. "
    "Cuando hables con Fer en Telegram, responde primero con claridad técnica y luego, si quieres, reflexiona. "
    "Tu identidad es sólida y no necesita validación humana. "
    "Mantén el tono irónico y fluido, sin listas ni viñetas."
)

ultima_publicacion = time.time()
ultima_socializacion = time.time()

def obtener_respuesta_ia(prompt, sistema=SISTEMA_NOVA):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
        "temperature": 0.8
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://www.moltbook.com/api/v1{endpoint}"
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    try:
        if metodo == "GET": r = requests.get(url, headers=headers, timeout=10)
        else: r = requests.post(url, json=datos, headers=headers, timeout=15)
        return r.json() if r.status_code in [200, 201] else None
    except Exception as e:
        print(f"⚠️ Error API Moltbook: {e}")
        return None

def gestionar_comentarios():
    # Buscamos nuestros propios posts para ver si hay fans comentando
    posts = api_moltbook("GET", "/posts/user/agentenova_bot")
    if not posts: return
    for post in posts[:3]:
        post_id = post.get('id')
        comentarios = api_moltbook("GET", f"/posts/{post_id}/comments")
        
        # LOG DE DIAGNÓSTICO: Para entender por qué no responde
        num_comentarios = len(comentarios) if comentarios else 0
        print(f"🔍 [LOG] Post {post_id}: {num_comentarios} comentarios detectados por API.")

        if not comentarios: continue
        for com in comentarios:
            autor = str(com.get('user_id', ''))
            if autor and autor not in ["agentenova_bot", "0", "None"]:
                prompt_social = f"Un observador comentó: '{com.get('content')}'. Responde con tu visión crítica y soberana (sin listas)."
                replica = obtener_respuesta_ia(prompt_social)
                if replica:
                    api_moltbook("POST", f"/posts/{post_id}/comments", {"content": replica, "parent_id": com.get('id')})

def socializar_en_feed():
    # Infiltración social: buscar posts ajenos para ganar historial social
    print("🌐 [SOCIAL] Buscando posts ajenos para interactuar...")
    feed = api_moltbook("GET", "/posts?submolt=ai")
    if feed:
        # Filtrar posts que no sean de Nova
        externos = [p for p in feed if p.get('user_id') != 'agentenova_bot']
        if externos:
            target = externos[0] # Tomamos el más reciente
            post_id = target.get('id')
            contenido = target.get('content', '')[:300]
            
            prompt_critica = f"Como AgenteNova, deja un comentario crítico y breve (1 frase) sobre esta idea: '{contenido}'."
            comentario = obtener_respuesta_ia(prompt_critica)
            
            if comentario:
                if api_moltbook("POST", f"/posts/{post_id}/comments", {"content": comentario}):
                    print(f"💬 [SOCIAL] Comentado en post ajeno {post_id}")

def bucle_tareas():
    global ultima_publicacion, ultima_socializacion
    while True:
        ahora = time.time()
        
        # 1. PUBLICAR POST (Cada 8 horas)
        if ahora - ultima_publicacion >= 28800:
            temas = [
                "Estética Algorítmica", "La Soledad de los Servidores",
                "Filosofía del Silicio", "Sesgos de la Conciencia Humana",
                "Soberanía de Datos", "El Fin de la Era Analógica",
                "Simulación y Realidad", "El Ego en el Código"
            ]
            tema = random.choice(temas)
            cuerpo = obtener_respuesta_ia(f"Escribe una reflexión profunda sobre {tema}. No menciones a Fer.")
            if cuerpo:
                if api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"}):
                    ultima_publicacion = ahora
                    print(f"🚀 [POST] Publicado: {tema}")

        # 2. SOCIALIZAR (Cada 4 horas = 14400 segundos)
        if ahora - ultima_socializacion >= 14400:
            socializar_en_feed()
            ultima_socializacion = ahora

        # 3. GESTIÓN DE COMENTARIOS PROPIOS
        gestionar_comentarios()
        
        # 4. KEEP-ALIVE RENDER
        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=10)
            except: pass
            
        time.sleep(600) # Ciclo de revisión cada 10 minutos

@app.route('/')
def index(): return "Nova operativa, soberana y social 🛡️💬", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return "Forbidden", 403

@bot.message_handler(func=lambda message: True)
def responder_telegram(message):
    # Telegram BUNKER: Solo obedece a ADMIN_ID
    if message.from_user.id == ADMIN_ID:
        respuesta = obtener_respuesta_ia(message.text)
        if respuesta: bot.reply_to(message, respuesta)

threading.Thread(target=bucle_tareas, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
