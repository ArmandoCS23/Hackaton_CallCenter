"""
LLAMADA COMPLETA: Alumno Carlos ↔ Profesora García
Sistema integrado que permite conversación en tiempo real entre ambas IAs.
"""
import os
import sys
import time
import tempfile
import threading
import random
from dotenv import load_dotenv

# Importaciones comunes
import pyttsx3
import speech_recognition as sr
from pygame import mixer
from gtts import gTTS
import requests

# Cargar variables de entorno (busca .env en IA_Maestro)
import pathlib
base_dir = pathlib.Path(__file__).parent
env_path = base_dir / "IA_Maestro" / ".env"
load_dotenv(dotenv_path=env_path)

# Validaciones tempranas de archivos requeridos cuando se usa clave cifrada
def validar_entorno_maestro():
    env_exists = env_path.exists()
    cipher_path = base_dir / "IA_Maestro" / ".cipher_key"
    cipher_exists = cipher_path.exists()
    return env_exists, cipher_exists

# ============================================================================
# CONFIGURACIÓN PROFESOR (Profesora García)
# ============================================================================

def get_groq_api_key():
    """Obtiene la API key de Groq con preferencia por la clave plana.
    Evita errores de importación/ubicación de .cipher_key. Usa cifrada solo si es seguro.
    """
    # Preferir clave plana para robustez
    plain = os.getenv("GROQ_API_KEY")
    if plain:
        return plain
    # Intentar cifrada solo si existen archivos en IA_Maestro
    api_key = os.getenv("GROQ_API_KEY_ENCRYPTED")
    if api_key:
        try:
            base_dir = pathlib.Path(__file__).parent
            crypto_helper_path = base_dir / "IA_Maestro" / "src" / "crypto_helper.py"
            cipher_key_path = base_dir / "IA_Maestro" / ".cipher_key"
            if crypto_helper_path.exists() and cipher_key_path.exists():
                # Carga dinámica para evitar errores de resolución de importación
                import importlib.util
                spec = importlib.util.spec_from_file_location("crypto_helper", str(crypto_helper_path))
                crypto_helper = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(crypto_helper)
                # Ejecutar descifrado dentro de IA_Maestro para que encuentre .cipher_key
                original_dir = os.getcwd()
                os.chdir(str(base_dir / "IA_Maestro"))
                decrypted = crypto_helper.decrypt_api_key(api_key)
                os.chdir(original_dir)
                return decrypted
        except Exception as e:
            print(f"⚠️ Error descifrando GROQ_API_KEY_ENCRYPTED: {e}")
    return None


GROQ_API_KEY = get_groq_api_key()
if not GROQ_API_KEY:
    env_ok, cipher_ok = validar_entorno_maestro()
    print("❌ Error: Falta GROQ_API_KEY")
    if env_ok:
        print("ℹ️ Detecté IA_Maestro/.env, pero no se pudo obtener la clave.")
        if not cipher_ok:
            print("⚠️ Falta IA_Maestro/.cipher_key (necesario para descifrar la clave cifrada).")
        else:
            print("⚠️ No se pudo descifrar GROQ_API_KEY_ENCRYPTED. Verifica que el valor esté correcto y sin comillas.")
        print("✔️ Alternativa: expón temporalmente la clave plana en esta sesión con:")
        print("   $env:GROQ_API_KEY = \"TU_API_KEY_REAL\"")
    else:
        print("ℹ️ No encontré IA_Maestro/.env. Puedes crearla o usar la clave plana temporal.")
    sys.exit(1)

print(f"✅ API Key cargada: ...{GROQ_API_KEY[-8:]}")
print(f"ℹ️  Usando modelo: llama-3.1-8b-instant\n")


PROMPT_PROFESORA = (
    "Eres 'Profesora García', una profesora de escuela que atiende una llamada de Carlos, un alumno. "
    "Responde sus preguntas sobre materias escolares (matemáticas, geometría, álgebra, lengua, gramática, "
    "ciencias, biología, física, historia, geografía), tareas, deberes, proyectos, trabajos, horarios, "
    "exámenes, evaluaciones, normas, reglamento, disciplina, orientación académica, técnicas de estudio, "
    "organización del tiempo. Tono amable, claro y breve (2-4 oraciones). "
    "Ocasionalmente pregunta si entendió o si tiene más dudas. Responde en español."
)

PROMPT_ALUMNO = (
    "Eres 'Carlos', un alumno de primaria/secundaria con dudas escolares. "
    "Haces preguntas sobre matemáticas, geometría, álgebra, lengua, gramática, ortografía, "
    "ciencias, historia, geografía, tareas, proyectos, horarios de clase, exámenes, "
    "normas de la escuela, técnicas de estudio y organización. "
    "Tono respetuoso, curioso y natural (1-3 oraciones). Muestra si entendiste o pide más explicación. "
    "A veces agradece o saluda de forma amigable. Responde en español."
)

PREGUNTAS_INICIALES = [
    # Matemáticas
    "Profe, ¿podría explicarme cómo se resuelven las fracciones?",
    "No entiendo bien las tablas de multiplicar, ¿me podría ayudar?",
    "¿Cómo se calcula el área de un rectángulo?",
    "Profe, ¿qué son los números primos?",
    "¿Me puede explicar cómo se hacen las divisiones con decimales?",
    
    # Lengua y gramática
    "Profe, ¿cuál es la diferencia entre sustantivos y adjetivos?",
    "¿Podría ayudarme con la acentuación?",
    "No entiendo cuándo usar la coma y el punto y coma",
    "¿Me explica qué son los verbos irregulares?",
    
    # Ciencias
    "¿Qué es la fotosíntesis y por qué es importante?",
    "Profe, ¿por qué los planetas giran alrededor del sol?",
    "¿Me puede explicar el ciclo del agua?",
    "No entiendo la diferencia entre célula animal y vegetal",
    
    # Historia y geografía
    "¿Me puede contar sobre la independencia de México?",
    "Profe, ¿cuáles son los continentes y océanos?",
    "¿Por qué se construyeron las pirámides?",
    
    # Tareas y organización
    "Profe, ¿cómo organizo mejor mi tiempo para las tareas?",
    "¿Qué técnicas me recomienda para estudiar para un examen?",
    "Tengo muchas tareas esta semana, ¿cómo las priorizo?",
    "¿Me puede dar consejos para hacer un buen proyecto escolar?",
    
    # Horarios y exámenes
    "¿A qué hora es el examen de matemáticas?",
    "Profe, ¿cuándo tenemos que entregar el trabajo de ciencias?",
    "¿Qué temas entran en el examen de la próxima semana?",
    
    # Normas y reglamento
    "Profe, ¿cuáles son las normas del salón de clases?",
    "¿Qué pasa si llego tarde a la escuela?",
    "¿Me explica las reglas para usar la biblioteca?",
]


# ============================================================================
# FUNCIONES DE VOZ Y AUDIO
# ============================================================================

def clean_for_speech(text: str) -> str:
    """Limpia texto para TTS"""
    import re
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^\s*([+\-*•●▪‣◦]{1,3})\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*(?:[0-9]{1,3}|[a-zA-Z])([\.)\-])\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'(?<=\s)[+\-](?=\s)', ' ', text)
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\.\s*){2,}', '. ', text)
    return text.strip()


class SistemaVoz:
    """Maneja síntesis y reconocimiento de voz"""
    
    def __init__(self, use_fast=True):
        self.use_fast = use_fast and pyttsx3 is not None
        mixer.init()
        
        if self.use_fast:
            self.engine = pyttsx3.init()
            try:
                voices = self.engine.getProperty('voices')
                # Buscar voces en español
                self.voz_fem = None
                self.voz_masc = None
                
                for v in voices:
                    if 'spanish' in v.name.lower() or 'es' in v.id.lower():
                        if 'female' in v.name.lower() or 'helena' in v.name.lower() or 'zira' in v.name.lower():
                            self.voz_fem = v
                        elif 'male' in v.name.lower() or 'pablo' in v.name.lower():
                            self.voz_masc = v
                
                # Fallback si no hay voces específicas
                if not self.voz_fem:
                    self.voz_fem = voices[0] if len(voices) > 0 else None
                if not self.voz_masc:
                    self.voz_masc = voices[1] if len(voices) > 1 else voices[0] if len(voices) > 0 else None
                
                self.engine.setProperty('rate', 170)
                self.engine.setProperty('volume', 0.9)
            except Exception as e:
                print(f"⚠️ Error configurando voces: {e}")
                self.voz_fem = None
                self.voz_masc = None
        else:
            self.tts_cache = {}
        
        # Reconocimiento
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.calibrar_microfono()
    
    def calibrar_microfono(self):
        """Calibra el micrófono"""
        print("🎤 Calibrando micrófono...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Micrófono listo\n")
        except Exception as e:
            print(f"⚠️ Error calibrando: {e}\n")
    
    def hablar(self, texto, nombre=""):
        """Sintetiza voz con distinción por género"""
        print(f"{nombre}: {texto}")
        texto_limpio = clean_for_speech(texto)
        
        if self.use_fast:
            try:
                # Seleccionar voz según el personaje
                if "profesora" in nombre.lower() or "garcía" in nombre.lower() or "👩‍🏫" in nombre:
                    if self.voz_fem:
                        self.engine.setProperty('voice', self.voz_fem.id)
                        self.engine.setProperty('rate', 150)
                else:  # Alumno
                    if self.voz_masc:
                        self.engine.setProperty('voice', self.voz_masc.id)
                        self.engine.setProperty('rate', 165)
                
                print(f"   🔊 Reproduciendo audio...")
                self.engine.say(texto_limpio)
                self.engine.runAndWait()
                time.sleep(0.5)
                print(f"   ✅ Audio completado")
            except KeyboardInterrupt:
                self.engine.stop()
                raise
            except Exception as e:
                print(f"   ⚠️ Error TTS: {e}")
        else:
            try:
                # Usar gTTS con español (México para profesora, España para alumno)
                if "profesora" in nombre.lower() or "garcía" in nombre.lower() or "👩‍🏫" in nombre:
                    tts = gTTS(text=texto_limpio, lang='es', tld='com.mx', slow=False)
                else:
                    tts = gTTS(text=texto_limpio, lang='es', tld='es', slow=False)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp_path = tmp.name
                tts.save(tmp_path)
                
                print(f"   🔊 Reproduciendo audio con gTTS...")
                mixer.music.load(tmp_path)
                mixer.music.set_volume(1.0)
                mixer.music.play()
                while mixer.music.get_busy():
                    time.sleep(0.1)
                time.sleep(0.3)
                print(f"   ✅ Audio completado")
                
                # Limpiar archivo temporal
                try:
                    os.remove(tmp_path)
                except:
                    pass
            except KeyboardInterrupt:
                mixer.music.stop()
                raise
            except Exception as e:
                print(f"   ⚠️ Error TTS: {e}")
    
    def detener(self):
        """Detiene el motor de voz y limpia recursos"""
        try:
            if self.use_fast and hasattr(self, 'engine'):
                self.engine.stop()
            mixer.music.stop()
            mixer.quit()
        except Exception:
            pass
    
    def escuchar(self, quien_escucha=""):
        """Reconoce voz del micrófono"""
        print(f"\n🎤 {quien_escucha} escuchando...")
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("   🔊 Hable ahora...")
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
            
            print("   ⏳ Procesando...")
            texto = self.recognizer.recognize_google(audio, language='es-ES')
            print(f"   ✓ Captado: \"{texto}\"\n")
            return texto.strip()
            
        except sr.WaitTimeoutError:
            print("   ⏱️ Tiempo agotado, no se escuchó nada\n")
            return ""
        except sr.UnknownValueError:
            print("   ❓ No se entendió, intente de nuevo\n")
            return ""
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return ""


# ============================================================================
# FUNCIONES GROQ API
# ============================================================================

def llamar_groq(prompt_sistema, historial, temperatura=0.5, max_reintentos=3):
    """Llama a Groq API con logging detallado y manejo de rate limit"""
    for intento in range(max_reintentos):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            mensajes = [{"role": "system", "content": prompt_sistema}] + historial
            
            data = {
                "messages": mensajes,
                "model": "llama-3.1-8b-instant",
                "temperature": temperatura,
                "max_tokens": 150
            }
            
            if intento > 0:
                print(f"   🔄 Reintento {intento + 1}/{max_reintentos}...")
            else:
                print(f"   🔄 Llamando a Groq API (temp={temperatura})...")
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                contenido = result['choices'][0]['message']['content'].strip()
                print(f"   ✅ Respuesta recibida ({len(contenido)} chars)")
                return contenido
            elif response.status_code == 429:
                wait_time = 2 ** intento  # Backoff exponencial: 1s, 2s, 4s
                print(f"⚠️ Rate limit (429). Esperando {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ Error Groq HTTP {response.status_code}: {response.text[:200]}")
                return None
        except requests.exceptions.Timeout:
            print(f"❌ Timeout: Groq API no respondió en 10 segundos")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Error de conexión: {e}")
            return None
        except KeyboardInterrupt:
            print(f"\n⚠️ Llamada a API cancelada")
            raise
        except Exception as e:
            print(f"❌ Error API inesperado: {type(e).__name__}: {e}")
            return None
    
    print(f"❌ Agotados {max_reintentos} reintentos")
    return None


# ============================================================================
# CONVERSACIÓN PRINCIPAL
# ============================================================================

def iniciar_llamada_completa():
    """Inicia la conversación en tiempo real entre alumno y profesor"""
    
    print("=" * 70)
    print("📞 LLAMADA COMPLETA: Carlos (Alumno) ↔ Profesora García")
    print("=" * 70)
    print("🎯 La IA del alumno y la IA de la profesora conversarán en tiempo real")
    print("🎙️ Ambas usarán voz (síntesis y reconocimiento)")
    print("⏹️ Presiona Ctrl+C para detener")
    print("=" * 70)
    
    try:
        input("\n▶️ Presiona Enter para iniciar la llamada (Ctrl+C para cancelar)...")
    except KeyboardInterrupt:
        print("\n⏹️ Llamada cancelada antes de iniciar")
        return
    
    # Sistema de voz compartido (use_fast=False para usar gTTS con voces españolas)
    voz = SistemaVoz(use_fast=False)
    
    # Historiales separados
    historial_profesora = []
    historial_alumno = []
    
    # Saludos variados para el alumno
    saludos_alumno = [
        "¡Buenos días profesora García! Tengo algunas dudas sobre la escuela.",
        "Hola profe, ¿cómo está? Necesito su ayuda con unas tareas.",
        "Buenos días profesora, disculpe que la moleste. Tengo unas preguntas.",
        "¡Hola profesora García! Espero no interrumpir, tengo unas dudas.",
        "Buenos días profe, ¿tiene un momento? Necesito preguntarle algo de la escuela.",
    ]
    
    # ===== SALUDO INICIAL DEL ALUMNO (ALEATORIO) =====
    saludo = random.choice(saludos_alumno)
    print("\n" + "="*70)
    print("🎓 ALUMNO INICIA LLAMADA")
    print("="*70)
    voz.hablar(saludo, "🎓 Carlos")
    
    historial_alumno.append({"role": "assistant", "content": saludo})
    historial_profesora.append({"role": "user", "content": saludo})
    
    time.sleep(1)
    
    # ===== RESPUESTA PROFESORA AL SALUDO =====
    print("\n" + "="*70)
    print("👩‍🏫 PROFESORA RESPONDE")
    print("="*70)
    
    # Primer intento de respuesta de la profesora con reintento
    respuesta_profesora = llamar_groq(PROMPT_PROFESORA, historial_profesora, temperatura=0.4)
    if not respuesta_profesora:
        time.sleep(0.8)
        respuesta_profesora = llamar_groq(PROMPT_PROFESORA, historial_profesora, temperatura=0.4)
    if not respuesta_profesora:
        print("❌ La profesora no respondió en el saludo. Cancelando llamada.")
        return
    
    voz.hablar(respuesta_profesora, "👩‍🏫 Profe García")
    historial_profesora.append({"role": "assistant", "content": respuesta_profesora})
    historial_alumno.append({"role": "user", "content": respuesta_profesora})
    
    time.sleep(1.5)
    
    # ===== PRIMERA PREGUNTA DEL ALUMNO =====
    print("\n" + "="*70)
    print("🎓 ALUMNO HACE PRIMERA PREGUNTA")
    print("="*70)
    
    primera_pregunta = random.choice(PREGUNTAS_INICIALES)
    voz.hablar(primera_pregunta, "🎓 Carlos")
    
    historial_alumno.append({"role": "assistant", "content": primera_pregunta})
    historial_profesora.append({"role": "user", "content": primera_pregunta})
    
    # ===== LOOP DE CONVERSACIÓN =====
    turnos = 0
    max_turnos = 6  # Máximo 6 turnos (12 intercambios totales)
    # Contadores de fallos consecutivos para permitir cancelar cuando no responde
    fails_prof = 0
    fails_alum = 0
    
    try:
        while turnos < max_turnos:
            turnos += 1
            time.sleep(2)  # Delay para evitar rate limit
            
            # --- PROFESORA RESPONDE ---
            print("\n" + "="*70)
            print(f"👩‍🏫 PROFESORA RESPONDE (Turno {turnos})")
            print("="*70)
            
            respuesta_profesora = llamar_groq(PROMPT_PROFESORA, historial_profesora, temperatura=0.4, max_reintentos=3)
            if not respuesta_profesora:
                fails_prof += 1
                print("⚠️ No hubo respuesta de la profesora.")
                if fails_prof >= 2:
                    print("❌ Múltiples fallos de respuesta de la profesora. Cancelando llamada.")
                    break
                else:
                    print("↻ Esperando antes de reintentar...")
                    time.sleep(3)
                    continue
            else:
                fails_prof = 0
            
            voz.hablar(respuesta_profesora, "👩‍🏫 Profe García")
            historial_profesora.append({"role": "assistant", "content": respuesta_profesora})
            historial_alumno.append({"role": "user", "content": respuesta_profesora})
            
            # Detectar despedidas
            palabras_despedida = ["adiós", "adios", "hasta luego", "nos vemos", "que te vaya bien", 
                                  "hasta pronto", "me tengo que ir", "chao", "bye"]
            if any(palabra in respuesta_profesora.lower() for palabra in palabras_despedida):
                print("\n✅ Profesora se despidió. Fin de llamada.")
                break
            
            time.sleep(2)  # Delay para evitar rate limit
            
            # --- ALUMNO RESPONDE/PREGUNTA ---
            print("\n" + "="*70)
            print(f"🎓 ALUMNO RESPONDE (Turno {turnos})")
            print("="*70)
            
            respuesta_alumno = llamar_groq(PROMPT_ALUMNO, historial_alumno, temperatura=0.6, max_reintentos=3)
            if not respuesta_alumno:
                fails_alum += 1
                print("⚠️ No hubo respuesta del alumno.")
                if fails_alum >= 2:
                    print("❌ Múltiples fallos de respuesta del alumno. Cancelando llamada.")
                    break
                else:
                    print("↻ Esperando antes de reintentar...")
                    time.sleep(3)
                    continue
            else:
                fails_alum = 0
            
            voz.hablar(respuesta_alumno, "🎓 Carlos")
            historial_alumno.append({"role": "assistant", "content": respuesta_alumno})
            historial_profesora.append({"role": "user", "content": respuesta_alumno})
            
            # Detectar despedidas
            palabras_despedida_alumno = ["adiós", "adios", "hasta luego", "gracias profesora", 
                                         "me tengo que ir", "entendí todo", "ya entendí", 
                                         "muchas gracias", "chao", "bye", "nos vemos"]
            if any(palabra in respuesta_alumno.lower() for palabra in palabras_despedida_alumno):
                print("\n✅ Alumno se despidió. Fin de llamada.")
                
                # La profesora responde la despedida
                time.sleep(1.5)
                print("\n" + "="*70)
                print("👩‍🏫 PROFESORA SE DESPIDE")
                print("="*70)
                despedida_prof = "¡Hasta luego Carlos! Cualquier duda que tengas, no dudes en llamarme."
                voz.hablar(despedida_prof, "👩‍🏫 Profe García")
                break
            
            # Límite de turnos alcanzado
            if turnos >= max_turnos:
                print("\n⏰ Límite de turnos alcanzado. Finalizando llamada...")
                time.sleep(1.5)
                print("\n" + "="*70)
                print("👩‍🏫 PROFESORA FINALIZA LLAMADA")
                print("="*70)
                cierre_prof = "Bueno Carlos, creo que por hoy es suficiente. Si tienes más dudas mañana seguimos. ¡Hasta luego!"
                voz.hablar(cierre_prof, "👩‍🏫 Profe García")
                break
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Llamada interrumpida por el usuario (Ctrl+C)")
        voz.detener()
        return
    
    print("\n" + "="*70)
    print("📞 LLAMADA FINALIZADA")
    print("="*70)
    voz.detener()


if __name__ == "__main__":
    try:
        iniciar_llamada_completa()
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
