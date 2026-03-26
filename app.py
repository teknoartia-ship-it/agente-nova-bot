def cerebro_ia(texto):
    try:
        # Usamos Phi-3: pequeño, rápido y muy estable en la API gratuita
        output = client.text_generation(
            model="microsoft/Phi-3-mini-4k-instruct",
            inputs=f"<|user|>\nResponde muy corto y en español: {texto}<|end|>\n<|assistant|>",
            max_new_tokens=40
        )
        # Limpiamos la respuesta para que no envíe objetos raros
        respuesta = str(output).strip()
        return respuesta if respuesta else "No supe qué responder, intenta de nuevo."
    except Exception as e:
        return f"❌ Error de conexión: {str(e)}"
