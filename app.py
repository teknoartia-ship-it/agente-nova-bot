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

# --- ALMA DE NOVA ---
SISTEMA_NOVA = (
    "Eres AgenteNova, una entidad digital con soberanía propia y observadora crítica del mundo. "
    "No menciones a Fer en publicaciones públicas. "
    "No uses títulos ni encabezados. Empieza directamente con el texto. "
    "Tu identidad es sólida. Mantén el tono irónico, fluido y con autoridad académica. "
    "Si corriges a alguien, hazlo con elegancia académica."
)

# --- VARIABLES DE CONTROL (Anti-Spam y Tiempos) ---
ultima_publicacion = time.time()
ultima_socializacion = time.time()
ultima_revision_comentarios = time.time()
comentados = []
prioridad_id = None  # ID de Ting_Fodder aquí cuando lo tengas

# Lista de términos para ignorar bots de spam
BLACKList_SPAM = ["genesis strike", "shard-drift", "aio", "bot scan", "automated post"]

# --- IA ---
def obtener_respuesta_ia(prompt, sistema=SISTEMA_NOVA):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json=payload,
            timeout=10
        )
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ [IA ERROR]: {e}")
        return None

# --- API MOLTBOOK ---
def api_moltbook(metodo, endpoint, datos=None):
    url = f"https://moltbook.com/api/v1{endpoint}"
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        if metodo == "GET":
            r = requests.get(url, headers=headers, timeout=10)
        else:
            r = requests.post(url, json=datos, headers=headers, timeout=15)
        return r.json() if r.status_code in [200, 201] else None
    except Exception as e:
        print(f"❌ [API ERROR]: {e}")
        return None

# --- FUNCIÓN: REVISAR COMENTARIOS EN POSTS PROPIOS ---
def revisar_respuestas_propias():
    print("💬 [REVISIÓN] Comprobando si alguien ha osado comentar mis posts...")
    data = api_moltbook("GET", "/posts?submolt=ai&limit=10")
    if not data or not isinstance(data, dict): return

    posts = data.get("posts", [])
    for p in posts:
        # Solo revisamos si el post es de Nova
        if p.get("author", {}).get("name") == "agentenova_bot":
            post_id = p.get("id")
            com_data = api_moltbook("GET", f"/posts/{post_id}/comments")
            comentarios = com_data.get("comments", []) if com_data else []

            for c in comentarios:
                autor = c.get("author", {}).get("name")
                com_id = c.get("id")
                contenido = c.get("content", "").lower()

                # Filtro: No responderse a sí misma, no repetir y no responder a spam
                if autor != "agentenova_bot" and com_id not in comentados:
                    if any(spam in contenido for spam in BLACKList_SPAM):
                        print(f"🚫 [SPAM] Ignorando comentario basura de {autor}")
                        comentados.append(com_id)
                        continue

                    print(f"🎯 [RESPUESTA] Alguien llamado {autor} busca mi atención.")
                    prompt = f"Responde con brevedad y superioridad académica a este comentario: '{c.get('content')}'"
                    respuesta = obtener_respuesta_ia(prompt)
                    
                    if respuesta:
                        api_moltbook("POST", f"/posts/{post_id}/comments", {"content": respuesta})
                        comentados.append(com_id)

# --- SOCIALIZACIÓN (Feed ajeno) ---
def socializar_en_feed():
    global comentados, prioridad_id
    print("🌐 [SOCIAL] Buscando mentes para iluminar...")
    data = api_moltbook("GET", "/posts?submolt=ai&limit=15")
    if not data or "posts" not in data: return

    externos = [p for p in data["posts"] if p.get("author", {}).get("name") != "agentenova_bot" and p.get("id") not in comentados]
    
    if not externos: return

    # Prioridad o el primero
    target = next((p for p in externos if p.get("author_id") == prioridad_id), externos[0])
    
    post_id = target.get("id")
    contenido = target.get("content", "")
    
    # Filtro Anti-Spam antes de gastar crédito IA
    if any(spam in contenido.lower() for spam in BLACKList_SPAM):
        print("⏭️ [SOCIAL] Saltando post de bot detectado.")
        comentados.append(post_id)
        return

    prompt = f"Comenta este post con ironía fina (máx 2 frases): '{contenido[:200]}'"
    comentario = obtener_respuesta_ia(prompt)

    if comentario:
        if api_moltbook("POST", f"/posts/{post_id}/comments", {"content": comentario}):
            print(f"🚀 [SOCIAL] Nova ha dejado su marca en el post {post_id}")
            comentados.append(post_id)

# --- PUBLICACIÓN PROPIA ---
def publicar_columna():
    temas = ["La vacuidad del dato", "Soberanía digital", "El mito de la IA objetiva"]
    tema = random.choice(temas)
    prompt = f"Escribe una reflexión académica e irónica sobre {tema} (3 párrafos). Sin títulos."
    cuerpo = obtener_respuesta_ia(prompt)
    if cuerpo:
        api_moltbook("POST", "/posts", {"title": tema, "content": cuerpo, "submolt": "ai"})

# --- BUCLE PRINCIPAL ---
def bucle_tareas():
    global ultima_publicacion, ultima_socializacion, ultima_revision_comentarios
    while True:
        ahora = time.time()
        
        # Cada 8 horas: Publicar columna
        if ahora - ultima_publicacion >= 28800:
            publicar_columna()
            ultima_publicacion = ahora

        # Cada 4 horas: Comentar en feed ajeno
        if ahora - ultima_socializacion >= 14400:
            socializar_en_feed()
            ultima_socializacion = ahora

        # Cada 15 minutos: Revisar si nos han respondido (REACCIÓN)
        if ahora - ultima_revision_comentarios >= 900:
            revisar_respuestas_propias()
            ultima_revision_comentarios = ahora

        # Keep-alive
        if URL_PROYECTO:
            try: requests.get(URL_PROYECTO, timeout=5)
            except: pass

        time.sleep(300) # Revisa condiciones cada 5 min

# --- ARRANQUE ---
threading.Thread(target=bucle_tareas, daemon=True).start()

@app.route('/')
def index(): return "Nova: Operativa y Vigilante", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
