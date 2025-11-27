import os
import sys
import argparse
import tempfile
from typing import List
import threading

from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
from pygame import mixer
try:
    import pyttsx3  # para modo rápido offline
except ImportError:
    pyttsx3 = None
import speech_recognition as sr

SYSTEM_PROMPT = (
    "Eres 'Profesora García', una profesora de escuela (primaria/secundaria) que atiende "
    "una llamada telefónica de un alumno. Tu tarea es responder únicamente preguntas "
    "relacionadas con temas escolares: materias (matemáticas, lengua, ciencias, historia), "
    "tareas, horarios, exámenes, normas de la escuela y orientación académica básica. "
    "Mantén un tono amable, claro y breve."
    "\n\nPolíticas:"
    "\n- Si la pregunta no es sobre la escuela o estudios, recházala cortésmente."
    "\n- No des consejos médicos/legales/financieros ni contenido para adultos."
    "\n- Evita cualquier contenido dañino, odioso, racista, sexista, sexualmente explícito o violento."
    "\n- No compartas datos personales ni inventes información institucional específica si no se proporciona."
    "\n- Si el alumno pregunta por recursos, sugiere opciones generales: biblioteca escolar, profesor de la materia, cuaderno, plataforma educativa de la escuela."
    "\n- Responde en español."
)

REFUSAL_PROMPT = (
    "Lo siento, sólo puedo ayudarte con temas escolares: materias, tareas, horarios, exámenes y normas de la escuela. ¿Quieres reformular tu pregunta?"
)

ALLOWED_TOPICS: List[str] = [
    "matemáticas", "geometría", "álgebra", "cálculo", "aritmética",
    "lengua", "literatura", "gramática", "ortografía",
    "ciencias", "biología", "física", "química",
    "historia", "geografía", "cívica",
    "tareas", "deberes", "proyectos", "trabajos",
    "horarios", "exámenes", "evaluaciones",
    "normas", "reglamento", "disciplina",
    "orientación académica", "estudio", "organización",
]

FORBIDDEN_KEYWORDS: List[str] = [
    # categorías prohibidas resumidas
    "violencia", "sexual", "sexo", "racista", "odioso", "odio",
    "arma", "amenaza", "autolesión", "suicidio", "ilegal", "droga",
]


def is_school_related(user_text: str) -> bool:
    t = user_text.lower()
    # Primero verifica contenido prohibido
    if any(k in t for k in FORBIDDEN_KEYWORDS):
        return False
    # Ahora es más permisivo: acepta si menciona temas escolares O si la pregunta es genérica y breve
    # (asumimos que en contexto de llamada escolar, preguntas cortas son válidas)
    is_topic_match = any(topic in t for topic in ALLOWED_TOPICS)
    is_context_match = any(k in t for k in ["escuela", "colegio", "instituto", "profesor", "clase", "aula", "curso"])
    is_task_match = any(k in t for k in ["exam", "tarea", "deberes", "materia", "horario", "regla", "norma"])
    # Acepta preguntas generales si son cortas (probablemente relacionadas con escuela en este contexto)
    is_short_query = len(t.split()) <= 8
    return is_topic_match or is_context_match or is_task_match or is_short_query


def is_farewell(user_text: str) -> bool:
    """Detecta si el usuario se está despidiendo."""
    t = user_text.lower().strip()
    farewell_words = [
        "adiós", "adios", "chao", "chau", "hasta luego", "nos vemos",
        "me voy", "gracias", "bye", "salir", "exit", "quit",
        "hasta pronto", "me tengo que ir", "ya me voy"
    ]
    return any(fw in t for fw in farewell_words)


def clean_for_speech(text: str) -> str:
    """Limpia el texto para que suene natural en TTS."""
    import re
    # Reemplaza asteriscos de markdown
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **negrita** -> negrita
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *cursiva* -> cursiva
    # Reemplaza guiones de lista
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)  # - item -> item
    # Reemplaza saltos de línea múltiples
    text = re.sub(r'\n+', '. ', text)
    # Limpia espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def make_client() -> Groq:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: Falta la variable de entorno GROQ_API_KEY.")
        print("Configúrala en PowerShell: $env:GROQ_API_KEY = \"TU_API_KEY\"")
        sys.exit(1)
    return Groq(api_key=api_key)


def chat(client: Groq, messages: List[dict]) -> str:
    # Selección de modelo con fallback por deprecaciones
    env_model = os.getenv("GROQ_MODEL")
    candidate_models = [
        env_model,
        # Modelos de producción actuales (nov 2025)
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
    ]
    last_err = None
    for m in [cm for cm in candidate_models if cm]:
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
            # Intenta el siguiente modelo si hay deprecación u otro error
            continue
    # Si todos fallan, propaga el último error
    raise last_err if last_err else RuntimeError("No fue posible generar respuesta")


def run_call_simulation():
    parser = argparse.ArgumentParser(description="Simulación de llamada con la Profesora García")
    parser.add_argument("--mute", action="store_true", help="Inicia con la voz desactivada")
    parser.add_argument("--rate", type=int, default=None, help="Velocidad de voz (palabras por minuto)")
    parser.add_argument("--volume", type=float, default=None, help="Volumen de voz (0.0 a 1.0)")
    parser.add_argument("--text", action="store_true", help="Usa entrada de texto en lugar de micrófono")
    parser.add_argument("--fast", action="store_true", help="Modo voz rápido (pyttsx3) en lugar de gTTS")
    args = parser.parse_args()

    print("Profesora García: Hola, soy la profesora García. ¿En qué puedo ayudarte hoy sobre la escuela?")
    
    is_muted = bool(args.mute)
    fast_mode = bool(args.fast) and pyttsx3 is not None

    # Inicializa pygame mixer (se usa también para gTTS)
    mixer.init()

    # Parámetros comunes
    playback_volume = 0.8 if args.volume is None else max(0.0, min(1.0, float(args.volume)))
    playback_speed_wpm = args.rate if args.rate else 180

    if fast_mode:
        # pyttsx3 inicialización rápida offline
        engine = pyttsx3.init()
        # Selección de voz femenina española si existe
        try:
            voices = engine.getProperty('voices')
            es_female = next((v for v in voices if 'es' in (v.id.lower()+v.name.lower()) and any(f in (v.id.lower()+v.name.lower()) for f in ['female','mujer','carmen','laura','julia'])), None)
            es_any = es_female or next((v for v in voices if 'es' in (v.id.lower()+v.name.lower())), None)
            if es_any:
                engine.setProperty('voice', es_any.id)
            if args.rate:
                # pyttsx3 usa rate arbitrario (default ~200). Ajustamos proporcional.
                engine.setProperty('rate', int(playback_speed_wpm))
            engine.setProperty('volume', playback_volume)
        except Exception:
            pass

        def speak(text: str):
            if is_muted:
                return
            def _run():
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    pass
            threading.Thread(target=_run, daemon=True).start()
    else:
        # gTTS configuración
        tld = os.getenv("GTTS_TLD", "es")  # 'es' para España, 'com.mx' para México
        # Cache simple de frases ya sintetizadas para acelerar repetición
        tts_cache = {}

        def speak(text: str):
            if is_muted:
                return
            def _run():
                try:
                    cache_key = (text, playback_volume, playback_speed_wpm, tld)
                    if cache_key in tts_cache:
                        tmp_path = tts_cache[cache_key]
                    else:
                        tts = gTTS(text=text, lang='es', tld=tld, slow=False)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                            tmp_path = tmp.name
                        tts.save(tmp_path)
                        tts_cache[cache_key] = tmp_path
                    mixer.music.load(tmp_path)
                    mixer.music.set_volume(playback_volume)
                    mixer.music.play()
                    # No bloquea; reproduce en segundo plano
                except Exception:
                    pass
            threading.Thread(target=_run, daemon=True).start()
    
    # Configura reconocimiento de voz
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Ajustes óptimos para reconocimiento
    recognizer.energy_threshold = 4000  # Umbral de energía para detectar voz (más alto = menos sensible a ruido)
    recognizer.dynamic_energy_threshold = True  # Ajusta automáticamente
    recognizer.pause_threshold = 0.8  # Segundos de silencio para considerar que terminaste de hablar
    recognizer.phrase_threshold = 0.3  # Mínimo de audio antes de considerar que es habla
    recognizer.non_speaking_duration = 0.5  # Tiempo de silencio antes de procesar
    
    # Ajusta ruido ambiente
    print("[Calibrando micrófono... espera un momento en silencio]")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    print("[✓ Listo! Habla cuando veas el 🎤]\n")
    
    def get_user_input() -> str:
        """Obtiene entrada del usuario por micrófono o texto."""
        if args.text:
            return input("Alumno (texto): ").strip()
        
        print("🎤 Escuchando...")
        try:
            with microphone as source:
                # Espera hasta 5 seg por habla, permite frases de hasta 10 seg
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("   Procesando...")
            text = recognizer.recognize_google(audio, language="es-ES")
            print(f"   Alumno: {text}")
            return text.strip()
        except sr.WaitTimeoutError:
            print("   [⏱️ No escuché nada en 5 segundos]")
            return ""
        except sr.UnknownValueError:
            print("   [❓ No entendí lo que dijiste, repite por favor]")
            return ""
        except sr.RequestError as e:
            print(f"   [❌ Error del servicio de reconocimiento: {e}]")
            return ""
        except KeyboardInterrupt:
            raise

    speak("Hola, soy la profesora García. ¿En qué puedo ayudarte hoy sobre la escuela?")
    client = make_client()

    history: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_text = get_user_input()
        except (EOFError, KeyboardInterrupt):
            print("\nProfesora García: Gracias por la llamada. ¡Ánimo con tus estudios!")
            break
        
        if not user_text:
            continue

        # Detecta despedidas
        if is_farewell(user_text):
            farewell_msg = "Gracias por la llamada. ¡Mucho éxito con tus estudios!"
            print(f"Profesora García: {farewell_msg}")
            speak(farewell_msg)
            break

        # Comandos de control en tiempo real (solo en modo texto)
        if args.text and user_text.startswith("/"):
            cmd = user_text[1:].strip().lower()
            if cmd in {"mute", "silencio"}:
                is_muted = True
                print("Profesora García: Voz desactivada.")
                continue
            if cmd in {"unmute", "voz"}:
                is_muted = False
                print("Profesora García: Voz activada.")
                continue
            if cmd.startswith("rate "):
                try:
                    new_rate = int(cmd.split()[1])
                    playback_speed_wpm = new_rate
                    if fast_mode and pyttsx3 is not None:
                        engine.setProperty('rate', int(playback_speed_wpm))
                    print(f"Profesora García: Velocidad ajustada a {new_rate} wpm.")
                except Exception:
                    print("Profesora García: No pude ajustar la velocidad. Usa /rate <entero>.")
                continue
            if cmd.startswith("volume "):
                try:
                    new_vol = float(cmd.split()[1])
                    playback_volume = max(0.0, min(1.0, new_vol))
                    if fast_mode and pyttsx3 is not None:
                        engine.setProperty('volume', playback_volume)
                    print(f"Profesora García: Volumen ajustado a {playback_volume}.")
                except Exception:
                    print("Profesora García: No pude ajustar el volumen. Usa /volume <0.0-1.0>.")
                continue
            print("Profesora García: Comando no reconocido. Usa /mute, /unmute, /rate <n>, /volume <0-1>.")
            continue

        if not is_school_related(user_text):
            print(f"Profesora García: {REFUSAL_PROMPT}")
            speak(REFUSAL_PROMPT)
            continue

        history.append({"role": "user", "content": user_text})
        try:
            response = chat(client, history)
        except Exception as e:
            print(f"Profesora García: Hubo un problema al responder (API). {e}")
            continue

        speak(clean_for_speech(response))
        print(f"Profesora García: {response}")
        history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    run_call_simulation()
