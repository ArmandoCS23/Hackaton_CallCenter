# Hackaton_CallCenter

##📞 Hackathon CallCenter – Documentación del Proyecto
##📘 Descripción General

Este proyecto integra múltiples módulos de inteligencia artificial diseñados para simular la interacción entre un Alumno y un Maestro mediante llamadas o mensajes.
Ambas IAs pueden ejecutarse en computadoras distintas y comunicarse entre sí usando servidores HTTP, modelos de voz y cifrado.

##El sistema también incluye:

Procesamiento de voz a texto y texto a voz.

Comunicación bidireccional entre IAs.

Scripts SQL para la base de datos.

Interfaz web con HTML.

##Versiones separadas y fusionadas de la IA del alumno y maestro.

##📁 Estructura del Proyecto
Hackaton_CallCenter/
│── main.py
│── requirements.txt
│── runtime.txt
│── templates/               # Interfaz HTML
│── sql/                     # Scripts de base de datos
│── Carpeta_IA/              # IA del Maestro
│── IA_Alumno/               # IA del Alumno
│── IA_fucionada/            # Versión combinada (Alumno + Maestro)

##📂 Carpetas Principales
Carpeta_IA/

Contiene la lógica del Maestro, incluyendo:

server.py – Servidor HTTP que recibe y envía mensajes.

profesor_llamada.py – Lógica de la IA del maestro.

crypto_helper.py – Cifrado y descifrado de mensajes.

IA_Alumno/

Contiene la lógica del Alumno, con estructura similar:

run.py

Modelos de respuesta del alumno.

Comunicación con el servidor del maestro.

IA_fucionada/

Implementa una versión donde Alumno y Maestro están integrados en una sola estructura más ordenada.

##⚙️ Instalación y Configuración
##1️⃣ Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

##2️⃣ Instalar dependencias
pip install -r requirements.txt

##3️⃣ Configurar variables de entorno

En cada carpeta de IA se incluye un archivo .env.example.
Cópialo y renómbralo a .env:
cp .env.example .env
Completa tus claves y URLs necesarias.

##4️⃣ Ejecutar el proyecto

Desde la raíz:

python main.py O desde cada IA:
python server.py O python run.py

##🔄 Comunicación entre IAs (Alumno ↔ Maestro)

Las inteligencias artificiales se conectan entre sí mediante:

Endpoints HTTP definidos en server.py.

Envío de mensajes de texto o audio.

Cifrado usando crypto_helper.py.

Procesamiento de voz para generar interacción más natural.

Cada IA puede correr en computadoras diferentes.
Solo debes configurar la IP o URL del servidor opuesto.

🗄️ Base de Datos

En la carpeta sql/ encontrarás scripts como:

base_de_datos_mysql.sql

create_student_questions.sql

Estos scripts permiten crear tablas para:

Registro de preguntas.

Historial de interacción.

Logs del entrenamiento y respuestas.

##🖥️ Interfaz Web

En la carpeta templates/ encontrarás páginas HTML donde el usuario puede interactuar:

index.html

page_2.html

page_3.html

page_4.html

page_5.html

Estas sirven para pruebas de interfaz o dashboards simples.

##🎯 Objetivo del Proyecto

Crear un sistema funcional donde:

El Alumno pueda hablar o escribir.

El Maestro responda de forma guiada.

Ambas IAs colaboren para simular llamadas reales.

El sistema pueda escalar para call centers, escuelas o simuladores.

##🧰 Tecnologías Utilizadas

Python 3

FastAPI / Flask (dependiendo del módulo)

OpenAI / IA conversacional

MySQL

HTML + JS

Librerías de grabación y reproducción de audio

Criptografía para comunicación segura
