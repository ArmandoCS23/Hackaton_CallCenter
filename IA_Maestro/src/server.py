import os
from flask import Flask, request, Response
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
import tempfile

app = Flask(__name__)

load_dotenv()

# Utilidad: cliente Groq

def make_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY_ENCRYPTED")
    if api_key:
        try:
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            from crypto_helper import decrypt_api_key
            api_key = decrypt_api_key(api_key)
        except Exception as e:
            raise RuntimeError(f"Error al descifrar GROQ_API_KEY: {e}")
    else:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise RuntimeError("Falta GROQ_API_KEY o GROQ_API_KEY_ENCRYPTED en entorno o .env")
    return Groq(api_key=api_key)

# Modelos de fallback
CANDIDATE_MODELS = [
    os.getenv("GROQ_MODEL"),
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]

SYSTEM_PROMPT = (
    "Eres 'Profesora García', una profesora de escuela (primaria/secundaria) que atiende "
    "una llamada telefónica de un alumno. Responde únicamente sobre temas escolares: materias, "
    "tareas, horarios, exámenes, normas y orientación académica básica. Tono amable, claro y breve."
    "\nPolíticas: rechaza cortésmente temas no escolares; evita contenido dañino, odioso, racista, sexista, sexual o violento; no des consejos médicos/legales/financieros; no compartas datos personales."
    "\nResponde en español."
)


def groq_chat(messages: list[dict]) -> str:
    client = make_client()
    last_err = None
    for m in [cm for cm in CANDIDATE_MODELS if cm]:
        try:
            completion = client.chat.completions.create(
                model=m,
                messages=messages,
                temperature=0.2,
                max_tokens=512,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            last_err = e
            continue
    raise last_err if last_err else RuntimeError("No fue posible generar respuesta")


def clean_for_speech(text: str) -> str:
    import re
    # Quita markdown básico
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # Quita bullets (- * + • ● ▪ ‣ ◦) al inicio
    text = re.sub(r'^\s*([+\-*•●▪‣◦]{1,3})\s+', '', text, flags=re.MULTILINE)
    # Quita enumeraciones tipo 1. 2) a) b. etc
    text = re.sub(r'^\s*(?:[0-9]{1,3}|[a-zA-Z])([\.)\-])\s+', '', text, flags=re.MULTILINE)
    # Elimina símbolos sueltos + o - entre espacios que se leen como palabras
    text = re.sub(r'(?<=\s)[+\-](?=\s)', ' ', text)
    # Saltos de línea -> punto y espacio
    text = re.sub(r'\n+', '. ', text)
    # Colapsa espacios
    text = re.sub(r'\s+', ' ', text)
    # Limpia puntos repetidos
    text = re.sub(r'(\.\s*){2,}', '. ', text)
    return text.strip()


@app.post("/voice")
def voice_welcome():
    # TwiML de bienvenida y redirige a /respond con recogida de voz
    twiml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response>"
        "  <Say language=\"es-ES\">Hola, soy la profesora García. Habla después del tono.</Say>"
        "  <Gather input=\"speech\" language=\"es-ES\" action=\"/respond\" timeout=\"5\" speechTimeout=\"auto\">"
        "    <Say language=\"es-ES\">Puedes hacer preguntas sobre materias, tareas, horarios y normas escolares.</Say>"
        "  </Gather>"
        "</Response>"
    )
    return Response(twiml, mimetype="text/xml")


@app.post("/respond")
def voice_respond():
    # Texto transcrito por Twilio
    user_text = request.form.get("SpeechResult", "").strip()
    # Si no se entendió, pide repetir
    if not user_text:
        twiml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Response>"
            "  <Say language=\"es-ES\">No te entendí, intenta de nuevo.</Say>"
            "  <Redirect method=\"POST\">/voice</Redirect>"
            "</Response>"
        )
        return Response(twiml, mimetype="text/xml")

    # Genera respuesta con Groq
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    try:
        response = groq_chat(messages)
    except Exception as e:
        response = "Hubo un problema con el servicio. Intenta más tarde."

    # Limpia para TTS
    speak_text = clean_for_speech(response)

    # Opción 1: decir directo con TwiML <Say>
    twiml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response>"
        f"  <Say language=\"es-ES\">{speak_text}</Say>"
        "  <Redirect method=\"POST\">/voice</Redirect>"
        "</Response>"
    )

    # Fin de llamada si el usuario se despide
    farewell_words = ["adiós", "adios", "chao", "chau", "hasta luego", "nos vemos"]
    if any(w in user_text.lower() for w in farewell_words):
        twiml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Response>"
            "  <Say language=\"es-ES\">Gracias por la llamada. ¡Éxitos en tus estudios!</Say>"
            "  <Hangup/>"
            "</Response>"
        )

    return Response(twiml, mimetype="text/xml")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)