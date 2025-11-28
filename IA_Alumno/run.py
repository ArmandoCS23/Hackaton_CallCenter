#!/usr/bin/env python3

import os
import sys
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from alumno_escolar import AlumnoEscolar
except ImportError as e:
    print(f"❌ Error importando: {e}")
    print("💡 Asegúrate de tener 'alumno_escolar.py' en la carpeta src/")
    exit(1)

def main():
    print("🏫 ALUMNO ESCOLAR - LLAMADA CON PROFESORA GARCÍA")
    print("=" * 60)
    print("CONTEXTO:")
    print("• 👦 Carlos (alumno) llama a su profesora")
    print("• 👩‍🏫 Profesora García atiende dudas escolares")
    print("• 📚 Solo temas académicos permitidos")
    print("• 🎯 Preguntas apropiadas para primaria/secundaria")
    print("=" * 60)
    
    print("\n🎯 Iniciando llamada en 3 segundos...")
    time.sleep(3)
    
    alumno = AlumnoEscolar()
    alumno.iniciar_clase_escolar()

if __name__ == "__main__":
    main()