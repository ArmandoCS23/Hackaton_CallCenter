import pyttsx3
import speech_recognition as sr
import time
import random
import re

class AlumnoExigente:
    def __init__(self):
        self.nombre_alumno = "Carlos"
        self.materia = "Matemáticas"
        
        # Configurar síntesis de voz
        self.engine = pyttsx3.init()
        self.configurar_voz()
        
        # Configurar reconocimiento de voz
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.configurar_microfono()
        
        # Preguntas específicas con respuestas esperadas
        self.preguntas_respuestas = {
            "¿Cuánto es 5 por 8?": {
                "respuesta_correcta": "40",
                "palabras_clave": ["cuarenta", "40"],
                "explicacion": "5 multiplicado por 8 es 40"
            },
            "¿Qué es una derivada en cálculo?": {
                "respuesta_correcta": "razón de cambio",
                "palabras_clave": ["razón de cambio", "tasa de cambio", "pendiente", "derivada es la pendiente"],
                "explicacion": "La derivada representa la razón de cambio instantánea"
            },
            "¿Cuál es la fórmula del área de un triángulo?": {
                "respuesta_correcta": "base por altura sobre 2",
                "palabras_clave": ["base por altura dividido 2", "base por altura entre 2", "b*h/2", "medio base por altura"],
                "explicacion": "El área es base por altura dividido 2"
            },
            "¿Qué es el teorema de Pitágoras?": {
                "respuesta_correcta": "a cuadrado más b cuadrado igual c cuadrado",
                "palabras_clave": ["a² + b² = c²", "hipotenusa al cuadrado", "catetos al cuadrado", "suma de cuadrados"],
                "explicacion": "En un triángulo rectángulo, la hipotenusa al cuadrado es igual a la suma de los cuadrados de los catetos"
            },
            "¿Cómo se resuelve una ecuación de primer grado?": {
                "respuesta_correcta": "despejar la incógnita",
                "palabras_clave": ["despejar", "aislar la variable", "pasar términos", "operaciones inversas"],
                "explicacion": "Se despeja la incógnita usando operaciones inversas"
            },
            "¿Qué es un número primo?": {
                "respuesta_correcta": "solo divisible entre 1 y sí mismo",
                "palabras_clave": ["divisible solo por 1", "sí mismo", "dos divisores", "números primos"],
                "explicacion": "Un número primo solo es divisible entre 1 y él mismo"
            },
            "¿Cuál es la derivada de x al cuadrado?": {
                "respuesta_correcta": "2x",
                "palabras_clave": ["2x", "dos x", "2 por x"],
                "explicacion": "La derivada de x² es 2x"
            },
            "¿Qué es la pendiente de una recta?": {
                "respuesta_correcta": "cambio en y sobre cambio en x",
                "palabras_clave": ["cambio vertical", "cambio horizontal", "dy/dx", "incremento"],
                "explicacion": "La pendiente es el cambio en y dividido por el cambio en x"
            }
        }
        
        self.preguntas_disponibles = list(self.preguntas_respuestas.keys())
        random.shuffle(self.preguntas_disponibles)
        self.pregunta_actual_index = 0

    def configurar_voz(self):
        """Configura la voz del alumno"""
        try:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    print(f"✅ Voz del alumno: {voice.name}")
                    break
            self.engine.setProperty('rate', 160)
            self.engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"⚠️  Error configurando voz: {e}")

    def configurar_microfono(self):
        """Configura el micrófono"""
        try:
            print("🎤 Calibrando micrófono...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Micrófono calibrado")
        except Exception as e:
            print(f"❌ Error con el micrófono: {e}")

    def sintetizar_voz(self, texto):
        """El alumno habla"""
        print(f"🎓 {self.nombre_alumno}: {texto}")
        try:
            self.engine.say(texto)
            self.engine.runAndWait()
        except Exception as e:
            print(f"❌ Error en síntesis de voz: {e}")

    def escuchar_profesor(self, tiempo_maximo=8):
        """Escucha la respuesta del profesor"""
        print(f"\n🎤 Escuchando al profesor... ({tiempo_maximo}s)")
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=tiempo_maximo, phrase_time_limit=tiempo_maximo)
            
            texto = self.recognizer.recognize_google(audio, language='es-ES')
            print(f"👨‍🏫 Profesor: {texto}")
            return texto.lower()
            
        except sr.WaitTimeoutError:
            print("⏰ Tiempo de escucha agotado")
            return ""
        except sr.UnknownValueError:
            print("❌ No se pudo entender la respuesta")
            return ""
        except Exception as e:
            print(f"❌ Error en reconocimiento: {e}")
            return ""

    def evaluar_respuesta(self, respuesta_profesor, pregunta_actual):
        """Evalúa si la respuesta del profesor es correcta"""
        if not respuesta_profesor:
            return "no_respondio"
        
        datos_pregunta = self.preguntas_respuestas[pregunta_actual]
        palabras_clave = datos_pregunta["palabras_clave"]
        respuesta_correcta = datos_pregunta["respuesta_correcta"]
        
        # Verificar si alguna palabra clave está en la respuesta
        for palabra in palabras_clave:
            if palabra.lower() in respuesta_profesor:
                return "correcta"
        
        # Verificar coincidencia numérica para preguntas matemáticas
        if "cuánto es" in pregunta_actual.lower() or "cuál es" in pregunta_actual.lower():
            numeros_respuesta = re.findall(r'\d+', respuesta_profesor)
            numeros_correctos = re.findall(r'\d+', respuesta_correcta)
            
            if numeros_respuesta and numeros_correctos:
                if numeros_respuesta[0] == numeros_correctos[0]:
                    return "correcta"
        
        return "incorrecta"

    def generar_respuesta_alumno(self, evaluacion, pregunta_actual):
        """Genera respuesta basada en si la respuesta fue correcta o no"""
        datos_pregunta = self.preguntas_respuestas[pregunta_actual]
        
        if evaluacion == "correcta":
            respuestas = [
                "¡Correcto! Muy bien profesor.",
                "¡Exacto! Esa es la respuesta.",
                "¡Perfecto! Lo entendió muy bien.",
                "¡Sí! Eso es lo que quería escuchar.",
                "¡Bien! Esa es la respuesta correcta."
            ]
            return random.choice(respuestas)
        
        elif evaluacion == "incorrecta":
            respuestas = [
                f"Eso no es correcto. La respuesta es: {datos_pregunta['explicacion']}",
                f"No, eso no es lo que pregunté. La respuesta correcta es: {datos_pregunta['explicacion']}",
                f"Creo que se confundió profesor. {datos_pregunta['explicacion']}",
                f"Esa no es la respuesta que esperaba. {datos_pregunta['explicacion']}",
                f"Me temo que no es correcto. {datos_pregunta['explicacion']}"
            ]
            return random.choice(respuestas)
        
        else:  # no_respondio
            respuestas = [
                "¿Profesor? No escuché su respuesta.",
                "No le escuché, ¿podría repetir?",
                "¿Tiene alguna duda con la pregunta?",
                "¿No sabe la respuesta profesor?",
                "Voy a darle la respuesta: " + datos_pregunta['explicacion']
            ]
            return random.choice(respuestas)

    def obtener_siguiente_pregunta(self):
        """Obtiene la siguiente pregunta del listado"""
        if self.pregunta_actual_index >= len(self.preguntas_disponibles):
            # Reinicar preguntas si se acabaron
            random.shuffle(self.preguntas_disponibles)
            self.pregunta_actual_index = 0
        
        pregunta = self.preguntas_disponibles[self.pregunta_actual_index]
        self.pregunta_actual_index += 1
        return pregunta

    def iniciar_examen(self):
        """Inicia el modo examen donde el alumno evalúa al profesor"""
        print("=" * 60)
        print("🎓 MODO EXAMEN - ALUMNO EVALUA AL PROFESOR")
        print("=" * 60)
        print(f"Alumno: {self.nombre_alumno}")
        print(f"Materia: {self.materia}")
        print("\n💡 El alumno hará preguntas DIRECTAS y evaluará tus respuestas.")
        print("💡 Responde claramente después de cada pregunta.")
        print("💡 Presiona Ctrl+C para finalizar.")
        print("=" * 60)
        
        input("\n🎯 Presiona Enter para comenzar el examen...")
        
        self.sintetizar_voz("Buenos días profesor. Voy a hacerle algunas preguntas directas de matemáticas.")
        time.sleep(2)
        
        contador = 1
        respuestas_correctas = 0
        respuestas_totales = 0
        
        try:
            while contador <= len(self.preguntas_respuestas):
                print(f"\n{'='*40}")
                print(f"❓ PREGUNTA #{contador}")
                print(f"{'='*40}")
                
                # Obtener pregunta
                pregunta_actual = self.obtener_siguiente_pregunta()
                
                # Alumno hace pregunta
                self.sintetizar_voz(pregunta_actual)
                time.sleep(1)
                
                # Escuchar respuesta del profesor
                print("\n🔊 Habla ahora tu respuesta...")
                respuesta_profesor = self.escuchar_profesor(10)
                
                # Evaluar respuesta
                evaluacion = self.evaluar_respuesta(respuesta_profesor, pregunta_actual)
                
                # Contar estadísticas
                respuestas_totales += 1
                if evaluacion == "correcta":
                    respuestas_correctas += 1
                
                # Alumno da feedback
                feedback = self.generar_respuesta_alumno(evaluacion, pregunta_actual)
                time.sleep(1)
                self.sintetizar_voz(feedback)
                
                # Mostrar estadística temporal
                porcentaje = (respuestas_correctas / respuestas_totales) * 100
                print(f"\n📊 Estadística: {respuestas_correctas}/{respuestas_totales} correctas ({porcentaje:.1f}%)")
                
                contador += 1
                print(f"\n⏳ Siguiente pregunta en 5 segundos...")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print(f"\n\n📊 EXAMEN TERMINADO - Resultado final:")
            print(f"Respuestas correctas: {respuestas_correctas}/{respuestas_totales}")
            
            if respuestas_totales > 0:
                porcentaje_final = (respuestas_correctas / respuestas_totales) * 100
                print(f"Porcentaje: {porcentaje_final:.1f}%")
                
                if porcentaje_final >= 80:
                    mensaje = "¡Excelente trabajo profesor! Es un experto en matemáticas."
                elif porcentaje_final >= 60:
                    mensaje = "Buen trabajo profesor, pero puede mejorar."
                else:
                    mensaje = "Profesor, necesita repasar más los conceptos de matemáticas."
                
                self.sintetizar_voz(mensaje)
            
            self.sintetizar_voz("¡Gracias por participar en el examen!")

    def iniciar_modo_practica(self):
        """Modo práctica con preguntas continuas"""
        print("🔄 MODO PRÁCTICA - Preguntas continuas")
        
        contador = 1
        try:
            while True:
                print(f"\n--- Pregunta #{contador} ---")
                pregunta_actual = self.obtener_siguiente_pregunta()
                self.sintetizar_voz(pregunta_actual)
                
                respuesta = self.escuchar_profesor(8)
                evaluacion = self.evaluar_respuesta(respuesta, pregunta_actual)
                
                feedback = self.generar_respuesta_alumno(evaluacion, pregunta_actual)
                time.sleep(1)
                self.sintetizar_voz(feedback)
                
                contador += 1
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n👋 Modo práctica terminado")

def main():
    print("🤖 ALUMNO EXIGENTE - EVALUADOR DE PROFESORES")
    print("1. 🎓 Modo Examen (preguntas específicas con evaluación)")
    print("2. 🔄 Modo Práctica (preguntas continuas)")
    
    opcion = input("\nSelecciona modo (1-2): ").strip()
    
    alumno = AlumnoExigente()
    
    if opcion == "1":
        alumno.iniciar_examen()
    else:
        alumno.iniciar_modo_practica()

if __name__ == "__main__":
    main()