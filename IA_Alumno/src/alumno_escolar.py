import pyttsx3
import speech_recognition as sr
import time
import random
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class AlumnoEscolar:
    def __init__(self):
        self.nombre_alumno = "Carlos"
        # Leer la API key de Groq desde la variable de entorno. NO dejar un valor por defecto aquí.
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            print("⚠️ Aviso: no se encontró la variable de entorno 'GROQ_API_KEY'. Configurela como secreto en GitHub o en su entorno local.")

        # Leer la API key de OpenAI desde la variable de entorno (si se usa OpenAI)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            print("⚠️ Aviso: no se encontró la variable de entorno 'OPENAI_API_KEY'. Si usa OpenAI, añádala como secreto o en su .env local.")
        
        # Inicializar motor de voz
        self.configurar_voz()
        
        # Configurar reconocimiento de voz
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.configurar_microfono()
        
        # Preguntas escolares apropiadas para primaria/secundaria
        self.preguntas_escolares = [
            # Matemáticas básicas
            "Profe, ¿podría explicarme cómo se resuelven las fracciones?",
            "No entiendo bien las tablas de multiplicar, ¿me podría ayudar?",
            "¿Cómo se calcula el área de un cuadrado y un rectángulo?",
            "Profe, tengo duda con los números decimales, ¿podría explicarlos?",
            "¿Qué son los números primos y para qué sirven?",
            
            # Lengua y literatura
            "Profe, ¿cuál es la diferencia entre sustantivos y adjetivos?",
            "No entiendo bien los verbos, ¿me los podría explicar?",
            "¿Cómo se hace un resumen de un texto?",
            "Profe, ¿qué es una metáfora y un símil?",
            "¿Podría ayudarme con la acentuación de las palabras?",
            
            # Ciencias
            "Profe, ¿qué es la fotosíntesis y por qué es importante?",
            "No entiendo los estados de la materia, ¿me los explica?",
            "¿Qué son los ecosistemas y cómo funcionan?",
            "Profe, ¿podría explicar el sistema solar?",
            "¿Cómo funciona el ciclo del agua?",
            
            # Historia y geografía
            "Profe, ¿quiénes fueron los aztecas y los mayas?",
            "¿Qué fue la Revolución Mexicana?",
            "No entiendo los puntos cardinales, ¿me ayuda?",
            "Profe, ¿qué son los continentes y océanos?",
            "¿Podría explicar qué son los mapas y para qué sirven?",
            
            # Tareas y organización
            "Profe, ¿cómo puedo organizar mejor mi tiempo para estudiar?",
            "¿Qué debo hacer si no entiendo una tarea?",
            "Profe, ¿podría explicar otra vez el trabajo que dejó?",
            "¿Cómo prepararme mejor para un examen?",
            "Profe, ¿a qué hora es la clase de mañana?",
            
            # Conceptos básicos
            "¿Qué significa hacer una buena presentación?",
            "Profe, ¿cómo puedo mejorar mi letra?",
            "¿Por qué es importante hacer la tarea?",
            "Profe, ¿qué materiales necesito para la clase de ciencias?",
            "¿Cómo funciona la biblioteca de la escuela?"
        ]

    def crear_motor_voz_fresco(self):
        """Crea un NUEVO motor de voz fresco para cada mensaje"""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.setProperty('volume', 1.0)
            
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            return engine
        except Exception as e:
            print(f"❌ Error creando motor de voz: {e}")
            return None

    def configurar_voz(self):
        """Configuración inicial de voz"""
        print("🔊 CONFIGURANDO AUDIO...")

    def configurar_microfono(self):
        """Configura el micrófono"""
        try:
            print("🎤 Calibrando micrófono...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Micrófono calibrado")
        except Exception as e:
            print(f"Error con el micrófono: {e}")

    def hablar(self, texto):
        """El alumno habla - CREANDO MOTOR NUEVO cada vez"""
        print(f"🎓 Alumno: {texto}")
        
        try:
            engine = self.crear_motor_voz_fresco()
            if engine:
                engine.say(texto)
                engine.runAndWait()
                engine.stop()
                print("✅ Audio entregado")
                return
        except Exception as e:
            print(f"❌ Error en audio: {e}")

    def escuchar_profesor_sin_limites(self):
        """Escucha al profesor SIN LÍMITES"""
        print(f"\n🎤 ESCUCHANDO... Hable cuando guste profesora")
        
        while True:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    print("🔊 Hable ahora...")
                    audio = self.recognizer.listen(source)
                
                texto = self.recognizer.recognize_google(audio, language='es-ES')
                print(f"👩‍🏫 Profesora: {texto}")
                
                if texto.strip():
                    return texto.lower()
                else:
                    self.hablar("Le escuché pero no entendí. ¿Podría repetir?")
                    
            except sr.UnknownValueError:
                self.hablar("No logré entenderle. ¿Podría repetir más claro?")
            except Exception as e:
                print(f"❌ Error: {e}")
                self.hablar("Hubo un error. ¿Podría repetir?")

    def llamar_groq_api(self, mensaje):
        """Llama a la API de Groq"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [{"role": "user", "content": mensaje}],
                "model": "llama-3.1-8b-instant",
                "temperature": 0.7,
                "max_tokens": 150
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"❌ Error Groq API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error llamando a Groq: {e}")
            return None

    def generar_pregunta(self):
        """Genera una pregunta escolar apropiada"""
        return random.choice(self.preguntas_escolares)

    def evaluar_respuesta(self, pregunta, respuesta_profesora):
        """Evalúa la respuesta de la profesora"""
        if not respuesta_profesora:
            return "No logré escuchar su respuesta. ¿Podría intentarlo de nuevo?"
        
        try:
            prompt = f"""
            Eres Carlos, un alumno de escuela primaria/secundaria. La profesora acaba de responder tu pregunta.
            
            Tu pregunta: "{pregunta}"
            Respuesta de la profesora: "{respuesta_profesora}"
            
            Como alumno, responde naturalmente mostrando si entendiste o necesitas más ayuda.
            Responde en máximo 2 frases, de manera respetuosa y apropiada para un alumno.
            
            Ejemplos de respuestas apropiadas:
            - "¡Ah, ya entiendo! Gracias profesora."
            - "Todavía no me queda claro, ¿podría explicarlo con un ejemplo?"
            - "Interesante, ¿podría decirme más sobre eso?"
            - "Perfecto, ahora comprendo mejor. Gracias."
            """
            
            resultado = self.llamar_groq_api(prompt)
            return resultado if resultado else "Gracias por la explicación profesora."
                
        except Exception as e:
            return "Interesante, ¿podría profundizar un poco más?"

    def iniciar_clase_escolar(self):
        """Inicia la clase con preguntas escolares apropiadas"""
        print("=" * 70)
        print("🏫 CLASE ESCOLAR - ALUMNO CON DUDAS ACADÉMICAS")
        print("=" * 70)
        print("TEMAS PERMITIDOS:")
        print("• 📚 Matemáticas, lengua, ciencias, historia")
        print("• 📝 Tareas, proyectos, trabajos")
        print("• ⏰ Horarios, exámenes, evaluaciones")
        print("• 🏫 Normas escolares y orientación académica")
        print("=" * 70)
        
        input("\n🎯 Presiona Enter para comenzar...")
        
        # Saludo inicial apropiado
        print("\n🔊 SALUDO INICIAL...")
        self.hablar("¡Buenos días profesora García! Tengo algunas dudas de la escuela.")
        
        # Esperar respuesta inicial
        print("\n🎤 RESPONDA AL SALUDO...")
        respuesta_inicial = self.escuchar_profesor_sin_limites()
        
        if respuesta_inicial:
            self.hablar("¡Gracias profesora! Comencemos con mis preguntas.")
        else:
            self.hablar("Bien, comenzemos con las preguntas entonces.")
        
        contador = 1
        
        try:
            while True:
                print(f"\n" + "="*50)
                print(f"📖 PREGUNTA #{contador}")
                print("="*50)
                
                # Hacer pregunta escolar
                pregunta = self.generar_pregunta()
                self.hablar(pregunta)
                
                # Esperar respuesta
                respuesta_profesora = self.escuchar_profesor_sin_limites()
                
                # Evaluar y responder
                respuesta_alumno = self.evaluar_respuesta(pregunta, respuesta_profesora)
                self.hablar(respuesta_alumno)
                
                contador += 1
                print(f"\n⏳ Siguiente pregunta en 4 segundos...")
                time.sleep(4)
                
        except KeyboardInterrupt:
            self.hablar("¡Muchas gracias por su ayuda profesora García!")
            print("\n🎓 Llamada terminada")

# Ejecución directa
if __name__ == "__main__":
    print("🏫 INICIANDO ALUMNO ESCOLAR...")
    alumno = AlumnoEscolar()
    alumno.iniciar_clase_escolar()