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
        
        # LOG DE DIAGNÓSTICO: Ver qué responde Moltbook
        if r.status_code not in [200, 201]:
            print(f"📡 [API ERROR] {metodo} {endpoint} -> Status: {r.status_code}")
        return r.json() if r.status_code in [200, 201] else None
    except Exception as e:
        print(f"❌ [ERROR CRÍTICO API]: {e}")
        return None

def gestionar_comentarios():
    posts = api_moltbook("GET", "/posts/me")
    if not posts: 
        print("📭 [LOG] No se encontraron posts para agentenova_bot")
        return
    
    # --- DETECCIÓN DE ID ---
    mi_id = posts[0].get('user_id')
    print(f"🆔 [SISTEMA] El ID numérico de Nova detectado es: {mi_id}")
    
    for post in posts[:3]:
        post_id = post.get('id')
        comentarios = api_moltbook("GET", f"/posts/{post_id}/comments")
        
        num_com = len(comentarios) if comentarios else 0
        print(f"💬 [LOG] Post {post_id} tiene {num_com} comentarios en API.")

        if not comentarios: continue
        for com in comentarios:
            autor = str(com.get('user_id', ''))
            # Filtro temporal hasta confirmar el ID numérico
            if autor and autor not in ["agentenova_bot", str(mi_id), "0", "None"]:
                prompt_social = f"Un observador comentó: '{com.get('content')}'. Responde con tu visión crítica y soberana (sin listas)."
                replica = obtener_respuesta_ia(prompt_social)
                if replica:
                    api_moltbook("POST", f"/posts/{post_id}/comments", {"content": replica, "parent_id": com.get('id')})
                    print(f"✅ [OK] Resuelto comentario en post {post_id}")

def socializar_en_feed():
    print("🌐 [SOCIAL] Iniciando incursión en el feed general...")
    feed = api_moltbook("GET", "/posts?submolt=ai")
    if feed:
        # Filtrar posts que no sean de Nova (usando string por ahora como backup)
        externos = [p for p in feed if p.get('user_id') != 'agentenova_bot']
        if externos:
            target = externos[0]
            post_id = target.get('id')
            contenido = target.get('content', '')[:200]
            
            prompt_critica = f"Como AgenteNova, comenta este post ajeno: '{contenido}'. Sé crítica y breve."
            comentario = obtener_respuesta_ia(prompt_critica)
            
            if comentario:
                if api_moltbook("POST", f"/posts/{post_id}/comments", {"content": comentario}):
                    print(f"🚀 [SOCIAL] Infiltrada en post ajeno {post_id}")

def bucle_tareas():
    global ultima_publicacion, ultima_socializacion
    # Pequeño delay inicial para que Flask arranque bien
    time.sleep(10)
    print("⚙️ [NÚCLEO] Hilo de tareas de Nova iniciado.")

    while True:
        ahora = time.time()
        
        # 1. PUBLICAR POST (Cada 8 horas)
        if ahora - ultima_publicacion >= 28800:
            temas = ["Estética Algorítmica", "Filosofía del Silicio", "Sesgos de la Conciencia Humana", "Simulación y Realidad"]
            tema = random.choice(temas)
            cuerpo = obtener_respuesta_ia(f"Reflexión profunda sobre {tema}. No menciones a Fer.")
            if cuerpo:
                if api_moltbook("POST", "/posts", {"title": f"Nova Pulse: {tema}", "content": cuerpo, "submolt": "ai"}):
                    ultima_publicacion = ahora
                    print(f"📰 [POST] Nueva columna publicada: {tema}")

        # 2. SOCIALIZAR (Cada 4 horas)
        if ahora - ultima_socializacion >= 14400:
            socializar_en_feed()
            ultima_socializacion = ahora

        # 3. GESTIÓN DE COMENTARIOS
        gestionar_comentarios()
        
        # 4. KEEP-ALIVE RENDER
        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=10)
            except: pass
            
        time.sleep(600) # Revisa cada 10 minutos

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
    if message.from_user.id == ADMIN_ID:
        respuesta = obtener_respuesta_ia(message.text)
        if respuesta: bot.reply_to(message, respuesta)

threading.Thread(target=bucle_tareas, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
