# 📞 **Hackaton CallCenter – Aplicación Web con IA**

## 📝 **Descripción General del Proyecto**
Este proyecto es una solución completa desarrollada para la **Hackatón CallCenter**, donde se creó una **aplicación web funcional** que integra **Inteligencia Artificial** para asistir en la gestión de llamadas, resolver consultas, apoyar a los agentes y automatizar procesos.

El proyecto combina:
- Frontend web completo con componentes reutilizables.
- Backend en Python para la lógica e integración.
- Modelos de IA (GPT) para generación de respuestas y análisis.
- Bases de datos y datasets para entrenamiento y pruebas.

---

# 🤖 **Justificación del Uso de Inteligencia Artificial**
La IA apoyó en distintas fases del desarrollo del sistema:

## 🔹 **1. Creación y Diseño de Interfaces Web**
**Prompts utilizados:**
- "Genera un panel de gestión de un Call Center con un diseño moderno"
- "Crea un formulario responsivo para registrar llamadas"

**Resultados generados:**
- Estructuras HTML optimizadas
- CSS y estilos responsivos
- Mejoras visuales y de usabilidad

---

## 🔹 **2. Corrección y Optimización de Código**
**Prompts utilizados:**
- "Corrige este error en JavaScript"
- "Optimiza este código Python y explícame la razón"

**Resultados generados:**
- Código corregido y funcionando
- Funciones más limpias y legibles
- Mejor estructura modular

---

## 🔹 **3. Documentación y Estructura del Proyecto**
**Prompts utilizados:**
- "Genera un README profesional para mi repositorio"

**Resultados generados:**
- Estructura completa del README
- Información clara y presentable

---

# 📂 **Estructura Completa del Proyecto**
A continuación se presenta la estructura fusionada del proyecto final:

```
Hackaton_CallCenter/
│
├── public/
│   ├── components/
│   ├── css/
│   ├── img/
│   ├── js/
│   └── video/
│
├── datasets/
│   ├── base_de_datos_mongo.json
│   ├── base_de_datos_students.xlsx
│   └── student_questions_base.xlsx
│
├── IA_fucionada/
│   ├── IA_Maestro/
│   │   ├── models/
│   │   ├── src/
│   │   │   ├── gpt_model.py
│   │   │   ├── llm.py
│   │   │   └── server.py
│   └── llamada_completa.py
│
├── sql/
│   ├── base_de_datos_mysql.sql
│   └── create_student_questions.sql
│
├── templates/
│   ├── index.html
│   ├── page_2.html
│   ├── page_3.html
│   ├── page_4.html
│   └── page_5.html
│
├── main.py
├── requirements.txt
└── README.md
```

---

# 🛠️ **Tecnologías Utilizadas**
### **Frontend**
- HTML5
- CSS3 / TailwindCSS
- JavaScript

### **Backend**
- Python
- FastAPI / Flask (dependiendo de la versión del proyecto)

### **Inteligencia Artificial**
- Modelos GPT para análisis de texto y respuestas
- Scripts internos de NLP

### **Bases de Datos**
- MySQL
- MongoDB

---

# 📥 **Cómo Clonar el Repositorio**
Ejecuta en tu terminal:
```bash
git clone https://github.com/tu_usuario/Hackaton_CallCenter.git
```

Ingresa al proyecto:
```bash
cd Hackaton_CallCenter
```

---

# ⚙️ **Instalación y Ejecución del Proyecto**
### 🔧 **1. Instalar dependencias**
Asegúrate de tener Python 3.10+ instalado.

```bash
pip install -r requirements.txt
```

### ▶️ **2. Ejecutar el servidor principal**
```bash
python main.py
```

### 🌐 **3. Abrir la aplicación en el navegador**
Dirígete a:
```
http://localhost:8000
```
(o el puerto configurado en tu servidor)

---

# 🧪 **Pruebas del Sistema**
Si agregaste pruebas, ejecútalas con:
```bash
pytest
```

---

# 📸 **Capturas de Pantalla** (Opcional)
_Añade aquí imágenes del dashboard, formularios o funciones importantes._

---

# 📄 **Licencia**
Este proyecto se distribuye bajo los términos definidos por los autores de la hackatón.

---

# 👤 **Autor(es)**
- Nombre del desarrollador
- Contacto
- GitHub del proyecto
