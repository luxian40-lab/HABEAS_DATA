import google.generativeai as genai
import json
import re
import os
import numpy as np
import time

# --- CONFIGURACIÓN ---
API_KEY = "AIzaSyA74qETI8gB2lsz2dHbdxBpOLtPDTev80E"

try:
    if not API_KEY:
        print("⚠️ CoreTex: No se detectó API Key.")
        model_gemini = None
    else:
        genai.configure(api_key=API_KEY)
        model_gemini = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ CoreTex AI: CONECTADO")
except Exception as e:
    model_gemini = None
    print(f"⚠️ CoreTex AI: OFFLINE ({e})")

# --- HERRAMIENTAS ---
def extraer_metadatos(texto):
    email = re.search(r'[\w\.-]+@[\w\.-]+', texto)
    nombre = "Cliente"
    if "Soy" in texto or "soy" in texto:
        try:
            parts = re.split(r'soy|Soy', texto)
            if len(parts) > 1:
                nombre = parts[1].split(",")[0].strip().split(".")[0]
        except: pass
    return {'email': email.group(0) if email else "no-email@vortex.ai", 'nombre': nombre, 'ticket_ref': f"REF-{np.random.randint(1000, 9999)}"}

# 🔥 FILTRO DE PRIVACIDAD 🔥
def anonimizar_regex(texto):
    texto = re.sub(r'\b(?:\d{4}[ -]?){3}\d{4}\b', '🔒<TARJETA_CENSURADA>', texto)
    texto = re.sub(r'\b\d{7,}\b', '🔒<NUM_OCULTO>', texto)
    texto = re.sub(r'[\w\.-]+@[\w\.-]+', '🔒<EMAIL_OCULTO>', texto)
    return texto

# --- ANÁLISIS ---
def procesar_ticket_inteligente(texto_ticket):
    if not model_gemini: return _respuesta_dummy()

    prompt = f"""
    Analiza este ticket: "{texto_ticket}"
    Responde SOLO JSON válido sin markdown:
    {{
        "emocion": "IRA, FRUSTRACION, URGENCIA, NEUTRAL, FELICIDAD",
        "intensidad": 1-10,
        "intencion": "SOPORTE, BAJA, VENTA, PHISHING",
        "es_phishing": boolean
    }}
    """
    try:
        response = model_gemini.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        base = {"IRA": 90, "FRUSTRACION": 70, "URGENCIA": 60, "NEUTRAL": 10, "FELICIDAD": 0}
        emocion = data.get("emocion", "NEUTRAL").upper()
        intensidad = int(data.get("intensidad", 5))
        riesgo = base.get(emocion, 20) + (intensidad * 2)
        
        if "no funciona" in texto_ticket.lower() or "error" in texto_ticket.lower():
            riesgo = max(riesgo, 60)

        return {
            'riesgo_extra': float(min(riesgo, 100)),
            'sentimiento_valor': intensidad / 10,
            'sentimiento_etiqueta': emocion,
            'tipo_ticket': data.get("intencion", "SOPORTE").upper(),
            'phishing': data.get("es_phishing", False),
            'intencion': data.get("intencion", "")
        }
    except Exception as e:
        print(f"⚠️ Error en IA: {e}")
        return _respuesta_dummy()

def _respuesta_dummy():
    # CORREGIDO: Ahora incluye 'sentimiento_valor' para evitar el KeyError
    return {
        'riesgo_extra': 50.0, 
        'sentimiento_etiqueta': "NEUTRAL", 
        'tipo_ticket': "SOPORTE", 
        'phishing': False,
        'sentimiento_valor': 0.5,  # <--- ESTO FALTABA
        'intencion': "Soporte General"
    }

def recomendar_accion(riesgo, sentimiento, phishing):
    if phishing: return "🛑 BLOQUEO TOTAL"
    if riesgo >= 85: return "🔥 CONTENCIÓN DE FUGA"
    if riesgo >= 60: return "🛠️ SOPORTE PRIORITARIO"
    return "✅ ATENCIÓN ESTÁNDAR"

# --- RESPUESTAS TÁCTICAS ---
def generar_respuesta_sugerida(texto, tipo, accion):
    if model_gemini:
        prompt = f"""
        Actúa como soporte experto. Respuesta corta para: "{texto}".
        Contexto: {tipo} | {accion}.
        NO des las gracias si están enojados.
        Respuesta (Max 25 palabras):
        """
        try: return model_gemini.generate_content(prompt).text.strip()
        except: pass

    # Plan B (Offline)
    t = str(tipo).upper()
    if "PHISHING" in t: return "⚠️ ALERTA: No comparta datos. Bloqueando enlace."
    if "FUGA" in t or "IRA" in t: return "Lamentamos esto. Un gerente revisará su caso YA."
    return "Entendido. Ingeniería está revisando su solicitud."