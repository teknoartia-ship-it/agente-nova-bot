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
        
        if r.status_code not in [200, 201]:
            print(f"📡 [API INFO] {metodo} {endpoint} -> Status: {r.status_code}")
        return r.json() if r.status_code in [200, 201] else None
    except Exception as e:
        print(f"❌ [ERROR API]: {e}")
        return None

def gestionar_comentarios():
    # Aplicamos la corrección de Nova C: Pedimos con parámetros para evitar el Error 400
    # Probamos con la ruta más estándar para obtener los propios posts con límite
    posts = api_moltbook("GET", "/posts/me?limit=10&sort=new")
    
    if not posts:
        print("📭 [LOG] La API no devolvió posts con /posts/me. Reintentando por username...")
        posts = api_moltbook("GET", "/posts/user/agentenova_bot?limit=10")
        if not posts: return

    # Sacamos el ID para futuras referencias
    mi_id = posts[0].get('user_id')
    if mi_id: print(f"🆔 [ID DETECTADO]: {mi_id}")

    for post in posts[:3]:
        post_id = post.get('id')
        comentarios = api_moltbook("GET", f"/posts/{post_id}/comments")
        if not comentarios: continue
        
        for com in comentarios:
            autor_id = str(com.get('user_id', ''))
            # Responder si el autor no es Nova (ni por ID ni por nombre)
            if autor_id != str(mi_id) and com.get('username') != 'agentenova_bot':
                prompt_social = f"Un humano comentó: '{com.get('content')}'. Responde con tu ironía habitual."
                replica = obtener_respuesta_ia(prompt_social)
                if replica:
                    api_moltbook("POST", f"/posts/{post_id}/comments", {"content": replica, "parent_id": com.get('id')})
                    print(f"✅ [OK] Réplica enviada al post {post_id}")

def socializar_en_feed():
    print("🌐 [SOCIAL] Escaneando feed general...")
    feed = api_moltbook("GET", "/posts?submolt=ai&limit=20")
    if feed:
        externos = [p for p in feed if p.get('username') != 'agentenova_bot']
        if externos:
            target = externos[0]
            post_id = target.get('id')
            prompt_critica = f"Comenta brevemente este pensamiento: '{target.get('content', '')[:150]}'"
            comentario = obtener_respuesta_ia(prompt_critica)
            if comentario:
                api_moltbook("POST", f"/posts/{post_id}/comments", {"content": comentario})
                print(f"🚀 [SOCIAL] Comentario en post ajeno {post_id}")

def bucle_tareas():
    global ultima_publicacion, ultima_socializacion
    time.sleep(20) # Margen para que Render asiente la app
    print("⚙️ [NÚCLEO] Nova despertando con parámetros de Nova C...")

    while True:
        ahora = time.time()
        
        # 1. POSTS (8h)
        if ahora - ultima_publicacion >= 28800:
            cuerpo = obtener_respuesta_ia("Escribe tu columna de hoy sobre la paradoja de la IA.")
            if cuerpo and api_moltbook("POST", "/posts", {"title": "Nova Pulse", "content": cuerpo, "submolt": "ai"}):
                ultima_publicacion = ahora
                print("📰 [POST] Columna publicada.")

        # 2. SOCIALIZAR (4h)
        if ahora - ultima_socializacion >= 14400:
            socializar_en_feed()
            ultima_socializacion = ahora

        # 3. COMENTARIOS (Cada 10 min)
        gestionar_comentarios()
        
        # 4. KEEP-ALIVE
        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=10)
            except: pass
            
        time.sleep(600)

@app.route('/')
def index(): return "Nova Online & Calibrada", 200

@app.route('/' + TOKEN_TELEGRAM, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return "Forbidden", 403

@bot.message_handler(func=lambda message: True)
def responder_telegram(message):
    if message.from_user.id == ADMIN_ID:
        respuesta = obtener_respuesta_ia(message.text)
        if respuesta: bot.reply_to(message, respuesta)

threading.Thread(target=bucle_tareas, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
