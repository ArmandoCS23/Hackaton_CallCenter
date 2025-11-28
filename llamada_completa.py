"""
LLAMADA COMPLETA: Alumno Carlos ↔ Profesora García
Sistema integrado que permite conversación en tiempo real entre ambas IAs.
CONEXIÓN MYSQL
"""
import os
import sys
import time
import tempfile
import random
from dotenv import load_dotenv

# Importaciones comunes
import pyttsx3
import speech_recognition as sr
from pygame import mixer
from gtts import gTTS
import requests

# Intentar importar mysql-connector
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("⚠️ mysql-connector-python no está instalado. Usando modo simulación.")

from datetime import datetime

# Cargar variables de entorno
import pathlib
base_dir = pathlib.Path(__file__).parent
env_path = base_dir / "IA_Maestro" / ".env"
load_dotenv(dotenv_path=env_path)

# Configuración MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'talkia',
    'user': 'admin2',
    'password': 'Newadmin7',
    'port': 3306
}

def validar_entorno_maestro():
    env_exists = env_path.exists()
    cipher_path = base_dir / "IA_Maestro" / ".cipher_key"
    cipher_exists = cipher_path.exists()
    return env_exists, cipher_exists

# ============================================================================
# CONEXIÓN MYSQL
# ============================================================================

class DatabaseManager:
    def __init__(self, mysql_config):
        self.mysql_config = mysql_config
        self.connection = None
        self.connected = False
        self.modo_simulacion = not MYSQL_AVAILABLE
        
        if self.modo_simulacion:
            print("🔶 MODO SIMULACIÓN ACTIVADO (mysql-connector no disponible)")
            self.conversaciones = []
            return
            
        # Conectar a MySQL
        if self.connect_mysql():
            self.crear_tabla_si_no_existe()
        else:
            print("🔶 MODO SIMULACIÓN ACTIVADO (no se pudo conectar a MySQL)")
            self.conversaciones = []
    
    def connect_mysql(self):
        """Conecta a MySQL"""
        try:
            print(f"🔧 Conectando a MySQL: {self.mysql_config['host']}:{self.mysql_config['port']}")
            self.connection = mysql.connector.connect(**self.mysql_config)
            
            if self.connection.is_connected():
                self.connected = True
                db_info = self.connection.get_server_info()
                print(f"✅ Conectado a MySQL Server v{db_info}")
                print(f"📊 Base de datos: {self.mysql_config['database']}")
                return True
                
        except Error as e:
            print(f"❌ Error conectando a MySQL: {e}")
            print("\n🔧 SOLUCIÓN DE PROBLEMAS:")
            print("1. Verifica que MySQL esté ejecutándose en 130.131.4.252:3306")
            print("2. Verifica que el usuario 'hackathon' y contraseña '12345' sean correctos")
            print("3. Verifica que la base de datos 'talkia' exista")
            print("4. Verifica la conexión de red al servidor")
            return False
    
    def crear_tabla_si_no_existe(self):
        """Crea la tabla de conversaciones si no existe"""
        if self.modo_simulacion or not self.connected:
            print("✅ Tabla simulada 'conversaciones' lista")
            return
            
        try:
            cursor = self.connection.cursor()
            
            # Verificar si la tabla existe
            table_check_query = """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'conversaciones'
            """
            cursor.execute(table_check_query, (self.mysql_config['database'],))
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                print("📊 Creando tabla 'conversaciones'...")
                # Crear tabla de conversaciones
                create_table_query = """
                CREATE TABLE conversaciones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    personaje VARCHAR(50) NOT NULL,
                    mensaje TEXT NOT NULL,
                    turno INT NOT NULL,
                    duracion_segundos FLOAT NOT NULL
                )
                """
                cursor.execute(create_table_query)
                self.connection.commit()
                print("✅ Tabla 'conversaciones' creada correctamente en MySQL")
            else:
                print("✅ Tabla 'conversaciones' ya existe en MySQL")
            
        except Error as e:
            print(f"❌ Error creando/verificando tabla: {e}")
            self.connected = False
    
    def guardar_mensaje(self, personaje, mensaje, turno, duracion_segundos):
        """Guarda un mensaje en MySQL o en simulación"""
        if self.modo_simulacion or not self.connected:
            # Modo simulación
            conversacion = {
                'timestamp': datetime.now(),
                'personaje': personaje,
                'mensaje': mensaje,
                'turno': turno,
                'duracion': duracion_segundos
            }
            self.conversaciones.append(conversacion)
            print(f"💾 Mensaje guardado (SIMULACIÓN): {personaje} - Turno {turno}")
            return True
            
        try:
            cursor = self.connection.cursor()
            insert_query = """
            INSERT INTO conversaciones (personaje, mensaje, turno, duracion_segundos)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (personaje, mensaje, turno, duracion_segundos))
            self.connection.commit()
            print(f"💾 Mensaje guardado en MySQL: {personaje} - Turno {turno}")
            return True
            
        except Error as e:
            print(f"❌ Error guardando mensaje en MySQL: {e}")
            # Cambiar a modo simulación
            self.connected = False
            self.modo_simulacion = True
            self.conversaciones = []
            # Guardar en simulación
            return self.guardar_mensaje(personaje, mensaje, turno, duracion_segundos)
    
    def obtener_ultimas_conversaciones(self, limite=10):
        """Obtiene las últimas conversaciones"""
        if self.modo_simulacion or not self.connected:
            return self.conversaciones[-limite:] if self.conversaciones else []
            
        try:
            cursor = self.connection.cursor()
            select_query = """
            SELECT timestamp, personaje, mensaje, turno
            FROM conversaciones 
            ORDER BY timestamp DESC
            LIMIT %s
            """
            cursor.execute(select_query, (limite,))
            resultados = cursor.fetchall()
            return resultados
            
        except Error as e:
            print(f"❌ Error obteniendo conversaciones: {e}")
            return []
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas de las conversaciones"""
        if self.modo_simulacion or not self.connected:
            if not self.conversaciones:
                return {}
            
            total_mensajes = len(self.conversaciones)
            mensajes_por_personaje = {}
            duracion_total = 0
            
            for conv in self.conversaciones:
                personaje = conv['personaje']
                mensajes_por_personaje[personaje] = mensajes_por_personaje.get(personaje, 0) + 1
                duracion_total += conv['duracion']
            
            return {
                'total_mensajes': total_mensajes,
                'mensajes_por_personaje': mensajes_por_personaje,
                'duracion_total_segundos': duracion_total
            }
            
        try:
            cursor = self.connection.cursor()
            
            # Total de mensajes
            cursor.execute("SELECT COUNT(*) FROM conversaciones")
            total_mensajes = cursor.fetchone()[0]
            
            # Mensajes por personaje
            cursor.execute("""
                SELECT personaje, COUNT(*) 
                FROM conversaciones 
                GROUP BY personaje
            """)
            mensajes_por_personaje = dict(cursor.fetchall())
            
            # Duración total
            cursor.execute("SELECT SUM(duracion_segundos) FROM conversaciones")
            duracion_total = cursor.fetchone()[0] or 0
            
            return {
                'total_mensajes': total_mensajes,
                'mensajes_por_personaje': mensajes_por_personaje,
                'duracion_total_segundos': duracion_total
            }
            
        except Error as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def cerrar_conexion(self):
        """Cierra la conexión a MySQL"""
        try:
            if self.connection and self.connected:
                self.connection.close()
                print("✅ Conexión a MySQL cerrada")
            
            # En modo simulación, guardar archivo
            if self.modo_simulacion and self.conversaciones:
                try:
                    with open('conversaciones_temp.txt', 'w', encoding='utf-8') as f:
                        for conv in self.conversaciones:
                            f.write(f"{conv['timestamp']} | {conv['personaje']} | Turno {conv['turno']}: {conv['mensaje']}\n")
                    print("💾 Conversaciones guardadas en 'conversaciones_temp.txt'")
                except Exception as e:
                    print(f"⚠️ Error guardando archivo temporal: {e}")
                    
        except Exception as e:
            print(f"⚠️ Error cerrando conexión: {e}")

# ============================================================================
# CONFIGURACIÓN GROQ API
# ============================================================================

def get_groq_api_key():
    """Obtiene la API key de Groq con preferencia por la clave plana."""
    plain = os.getenv("GROQ_API_KEY")
    if plain:
        return plain
    api_key = os.getenv("GROQ_API_KEY_ENCRYPTED")
    if api_key:
        try:
            base_dir = pathlib.Path(__file__).parent
            crypto_helper_path = base_dir / "IA_Maestro" / "src" / "crypto_helper.py"
            cipher_key_path = base_dir / "IA_Maestro" / ".cipher_key"
            if crypto_helper_path.exists() and cipher_key_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("crypto_helper", str(crypto_helper_path))
                crypto_helper = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(crypto_helper)
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
    sys.exit(1)

print(f"✅ API Key cargada: ...{GROQ_API_KEY[-8:]}")
print(f"ℹ️  Usando modelo: llama-3.1-8b-instant\n")

# Inicializar el gestor de base de datos MYSQL
db_manager = DatabaseManager(MYSQL_CONFIG)

# PROMPTS y resto del código permanecen igual...
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
    "Tono respetuoso, curioso y natural (1-3 oraciones). Muestra si entendió o pide más explicación. "
    "A veces agradece o saluda de forma amigable. Responde en español."
)

PREGUNTAS_INICIALES = [
    "Profe, ¿podría explicarme cómo se resuelven las fracciones?",
    "No entiendo bien las tablas de multiplicar, ¿me podría ayudar?",
    "¿Cómo se calcula el área de un rectángulo?",
    "Profe, ¿qué son los números primos?",
    "¿Me puede explicar cómo se hacen las divisiones con decimales?",
    "Profe, ¿cuál es la diferencia entre sustantivos y adjetivos?",
    "¿Podría ayudarme con la acentuación?",
    "¿Qué es la fotosíntesis y por qué es importante?",
    "Profe, ¿por qué los planetas giran alrededor del sol?",
    "¿Me puede contar sobre la independencia de México?",
]

# ============================================================================
# SISTEMA DE VOZ (igual que antes)
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
                self.voz_fem = None
                self.voz_masc = None
                
                for v in voices:
                    if 'spanish' in v.name.lower() or 'es' in v.id.lower():
                        if 'female' in v.name.lower() or 'helena' in v.name.lower() or 'zira' in v.name.lower():
                            self.voz_fem = v
                        elif 'male' in v.name.lower() or 'pablo' in v.name.lower():
                            self.voz_masc = v
                
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
        
        inicio = time.time()
        
        if self.use_fast:
            try:
                if "profesora" in nombre.lower() or "garcía" in nombre.lower() or "👩‍🏫" in nombre:
                    if self.voz_fem:
                        self.engine.setProperty('voice', self.voz_fem.id)
                        self.engine.setProperty('rate', 150)
                else:
                    if self.voz_masc:
                        self.engine.setProperty('voice', self.voz_masc.id)
                        self.engine.setProperty('rate', 165)
                
                print(f"   🔊 Reproduciendo audio...")
                self.engine.say(texto_limpio)
                self.engine.runAndWait()
                time.sleep(0.5)
                duracion = time.time() - inicio
                print(f"   ✅ Audio completado ({duracion:.2f}s)")
                return duracion
            except KeyboardInterrupt:
                self.engine.stop()
                raise
            except Exception as e:
                print(f"   ⚠️ Error TTS: {e}")
                return time.time() - inicio
        else:
            try:
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
                duracion = time.time() - inicio
                print(f"   ✅ Audio completado ({duracion:.2f}s)")
                
                try:
                    os.remove(tmp_path)
                except:
                    pass
                return duracion
            except KeyboardInterrupt:
                mixer.music.stop()
                raise
            except Exception as e:
                print(f"   ⚠️ Error TTS: {e}")
                return time.time() - inicio
    
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
# FUNCIONES GROQ API (igual que antes)
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
                wait_time = 2 ** intento
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

def mostrar_historial_conversaciones():
    """Muestra el historial de conversaciones guardadas"""
    print("\n" + "="*70)
    if db_manager.modo_simulacion:
        print("📊 HISTORIAL DE CONVERSACIONES (SIMULACIÓN)")
    else:
        print("📊 HISTORIAL DE CONVERSACIONES (MySQL)")
    print("="*70)
    
    conversaciones = db_manager.obtener_ultimas_conversaciones(5)
    if conversaciones:
        for conv in conversaciones:
            if db_manager.modo_simulacion:
                timestamp = conv['timestamp']
                personaje = conv['personaje']
                mensaje = conv['mensaje']
                turno = conv['turno']
                print(f"{timestamp.strftime('%H:%M:%S')} | Turno {turno} | {personaje}: {mensaje[:80]}...")
            else:
                timestamp, personaje, mensaje, turno = conv
                print(f"{timestamp.strftime('%H:%M:%S')} | Turno {turno} | {personaje}: {mensaje[:80]}...")
    else:
        print("No hay conversaciones guardadas")
    print("="*70)

def mostrar_estadisticas():
    """Muestra estadísticas de las conversaciones"""
    print("\n" + "="*70)
    print("📈 ESTADÍSTICAS DE CONVERSACIONES")
    print("="*70)
    
    stats = db_manager.obtener_estadisticas()
    if stats:
        print(f"📊 Total de mensajes: {stats['total_mensajes']}")
        print(f"⏱️  Duración total: {stats['duracion_total_segundos']:.2f} segundos")
        print("👥 Mensajes por personaje:")
        for personaje, cantidad in stats['mensajes_por_personaje'].items():
            print(f"   - {personaje}: {cantidad}")
    else:
        print("No hay estadísticas disponibles")
    print("="*70)

def iniciar_llamada_completa():
    """Inicia la conversación en tiempo real entre alumno y profesor"""
    
    print("=" * 70)
    print("📞 LLAMADA COMPLETA: Carlos (Alumno) ↔ Profesora García")
    if db_manager.modo_simulacion:
        print("💾 MODO SIMULACIÓN: Las conversaciones se guardan en memoria")
    else:
        print(f"💾 CONECTADO A MySQL: {MYSQL_CONFIG['database']}@{MYSQL_CONFIG['host']}")
    print("=" * 70)
    print("🎯 La IA del alumno y la IA de la profesora conversarán en tiempo real")
    print("🎙️ Ambas usarán voz (síntesis y reconocimiento)")
    if db_manager.modo_simulacion:
        print("💾 Conversaciones se guardan temporalmente en memoria")
    else:
        print(f"💾 Todas las conversaciones se guardarán en MySQL")
    print("⏹️ Presiona Ctrl+C para detener")
    print("=" * 70)
    
    mostrar_historial_conversaciones()
    mostrar_estadisticas()
    
    try:
        input("\n▶️ Presiona Enter para iniciar la llamada (Ctrl+C para cancelar)...")
    except KeyboardInterrupt:
        print("\n⏹️ Llamada cancelada antes de iniciar")
        db_manager.cerrar_conexion()
        return
    
    voz = SistemaVoz(use_fast=False)
    historial_profesora = []
    historial_alumno = []
    
    saludos_alumno = [
        "¡Buenos días profesora García! Tengo algunas dudas sobre la escuela.",
        "Hola profe, ¿cómo está? Necesito su ayuda con unas tareas.",
        "Buenos días profesora, disculpe que la moleste. Tengo unas preguntas.",
        "¡Hola profesora García! Espero no interrumpir, tengo unas dudas.",
    ]
    
    # SALUDO INICIAL
    saludo = random.choice(saludos_alumno)
    print("\n" + "="*70)
    print("🎓 ALUMNO INICIA LLAMADA")
    print("="*70)
    duracion = voz.hablar(saludo, "🎓 Carlos")
    db_manager.guardar_mensaje("Carlos", saludo, 0, duracion)
    historial_alumno.append({"role": "assistant", "content": saludo})
    historial_profesora.append({"role": "user", "content": saludo})
    
    time.sleep(1)
    
    # RESPUESTA PROFESORA
    print("\n" + "="*70)
    print("👩‍🏫 PROFESORA RESPONDE")
    print("="*70)
    respuesta_profesora = llamar_groq(PROMPT_PROFESORA, historial_profesora, temperatura=0.4)
    if not respuesta_profesora:
        respuesta_profesora = llamar_groq(PROMPT_PROFESORA, historial_profesora, temperatura=0.4)
    if not respuesta_profesora:
        print("❌ La profesora no respondió. Cancelando llamada.")
        db_manager.cerrar_conexion()
        return
    
    duracion = voz.hablar(respuesta_profesora, "👩‍🏫 Profe García")
    db_manager.guardar_mensaje("Profesora García", respuesta_profesora, 1, duracion)
    historial_profesora.append({"role": "assistant", "content": respuesta_profesora})
    historial_alumno.append({"role": "user", "content": respuesta_profesora})
    
    time.sleep(1.5)
    
    # PRIMERA PREGUNTA
    print("\n" + "="*70)
    print("🎓 ALUMNO HACE PRIMERA PREGUNTA")
    print("="*70)
    primera_pregunta = random.choice(PREGUNTAS_INICIALES)
    duracion = voz.hablar(primera_pregunta, "🎓 Carlos")
    db_manager.guardar_mensaje("Carlos", primera_pregunta, 2, duracion)
    historial_alumno.append({"role": "assistant", "content": primera_pregunta})
    historial_profesora.append({"role": "user", "content": primera_pregunta})
    
    # LOOP DE CONVERSACIÓN
    turnos = 0
    max_turnos = 6
    
    try:
        while turnos < max_turnos:
            turnos += 1
            time.sleep(2)
            
            # PROFESORA RESPONDE
            print("\n" + "="*70)
            print(f"👩‍🏫 PROFESORA RESPONDE (Turno {turnos})")
            print("="*70)
            respuesta_profesora = llamar_groq(PROMPT_PROFESORA, historial_profesora, temperatura=0.4, max_reintentos=3)
            if not respuesta_profesora:
                continue
            
            duracion = voz.hablar(respuesta_profesora, "👩‍🏫 Profe García")
            db_manager.guardar_mensaje("Profesora García", respuesta_profesora, turnos * 2 + 1, duracion)
            historial_profesora.append({"role": "assistant", "content": respuesta_profesora})
            historial_alumno.append({"role": "user", "content": respuesta_profesora})
            
            if any(palabra in respuesta_profesora.lower() for palabra in ["adiós", "adios", "hasta luego"]):
                print("\n✅ Profesora se despidió. Fin de llamada.")
                break
            
            time.sleep(2)
            
            # ALUMNO RESPONDE
            print("\n" + "="*70)
            print(f"🎓 ALUMNO RESPONDE (Turno {turnos})")
            print("="*70)
            respuesta_alumno = llamar_groq(PROMPT_ALUMNO, historial_alumno, temperatura=0.6, max_reintentos=3)
            if not respuesta_alumno:
                continue
            
            duracion = voz.hablar(respuesta_alumno, "🎓 Carlos")
            db_manager.guardar_mensaje("Carlos", respuesta_alumno, turnos * 2 + 2, duracion)
            historial_alumno.append({"role": "assistant", "content": respuesta_alumno})
            historial_profesora.append({"role": "user", "content": respuesta_alumno})
            
            if any(palabra in respuesta_alumno.lower() for palabra in ["adiós", "adios", "hasta luego", "gracias"]):
                print("\n✅ Alumno se despidió. Fin de llamada.")
                despedida_prof = "¡Hasta luego Carlos! Cualquier duda que tengas, no dudes en llamarme."
                duracion = voz.hablar(despedida_prof, "👩‍🏫 Profe García")
                db_manager.guardar_mensaje("Profesora García", despedida_prof, turnos * 2 + 3, duracion)
                break
            
            if turnos >= max_turnos:
                cierre_prof = "Bueno Carlos, creo que por hoy es suficiente. Si tienes más dudas mañana seguimos. ¡Hasta luego!"
                duracion = voz.hablar(cierre_prof, "👩‍🏫 Profe García")
                db_manager.guardar_mensaje("Profesora García", cierre_prof, turnos * 2 + 3, duracion)
                break
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Llamada interrumpida por el usuario (Ctrl+C)")
        voz.detener()
        db_manager.cerrar_conexion()
        return
    
    print("\n" + "="*70)
    print("📞 LLAMADA FINALIZADA")
    print("="*70)
    
    mostrar_historial_conversaciones()
    mostrar_estadisticas()
    
    voz.detener()
    db_manager.cerrar_conexion()

if __name__ == "__main__":
    try:
        iniciar_llamada_completa()
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrumpido por el usuario")
        db_manager.cerrar_conexion()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        db_manager.cerrar_conexion()
        sys.exit(1)