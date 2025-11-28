import os
import random
import sqlite3
import mysql.connector
import subprocess
import sys
import threading
import uuid
import queue
import time
import json
from flask import Response
from mysql.connector import Error as MySQLError
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Cargar .env en IA_Maestro (si existe)
base_dir = os.path.dirname(__file__)
load_dotenv(os.path.join(base_dir, '..', '.env'))

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(base_dir, '..', 'users_api.db')

# Intento de usar MySQL para usuarios (lee variables desde .env si existen)
MYSQL_USERS_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'admin2'),
    'password': os.getenv('MYSQL_PASSWORD', 'Newadmin7'),
    'database': os.getenv('MYSQL_DATABASE', 'talkia'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
}

USE_MYSQL_FOR_USERS = False
try:
    # prueba de conexión simple
    conn_test = mysql.connector.connect(
        host=MYSQL_USERS_CONFIG['host'],
        user=MYSQL_USERS_CONFIG['user'],
        password=MYSQL_USERS_CONFIG['password'],
        database=MYSQL_USERS_CONFIG['database'],
        port=MYSQL_USERS_CONFIG['port'],
        connection_timeout=3,
    )
    if conn_test.is_connected():
        USE_MYSQL_FOR_USERS = True
        conn_test.close()
except Exception:
    USE_MYSQL_FOR_USERS = False

# Preguntas de ejemplo
SAMPLE_QUESTIONS = [
    "Profe, ¿cómo se calculan las fracciones?",
    "No entiendo las tablas de multiplicar, ¿me ayuda?",
    "¿Cómo se calcula el área de un rectángulo?",
    "Profe, ¿qué son los números primos?",
    "¿Qué es la fotosíntesis?"
]

# Intento simple de usar Groq si está instalado y hay API key
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

CANDIDATE_MODELS = [
    os.getenv('GROQ_MODEL'),
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]

SYSTEM_PROMPT = (
    "Eres 'Profesora García', una profesora de escuela (primaria/secundaria) que atiende "
    "una llamada telefónica de un alumno. Responde únicamente sobre temas escolares: materias, "
    "tareas, horarios, exámenes, normas y orientación académica básica. Tono amable, claro y breve."
    "\nResponde en español."
)

PROMPT_ALUMNO = (
    "Eres 'Carlos', un alumno de primaria/secundaria con dudas escolares. "
    "Haz preguntas cortas y naturales en español."
)


def init_users_db():
    if USE_MYSQL_FOR_USERS:
        try:
            conn = mysql.connector.connect(**MYSQL_USERS_CONFIG)
            cur = conn.cursor()
            # Si la BD ya contiene la tabla `usuarios` (esquema canonical), la usaremos.
            cur.execute("SHOW TABLES")
            tables = [t[0] for t in cur.fetchall()]
            if 'usuarios' in tables:
                print('INFO: tabla `usuarios` encontrada en MySQL; se usará para autenticación')
                cur.close()
                conn.close()
                print('INFO: usando MySQL para usuarios (tabla usuarios)')
                return

            # Si no existe `usuarios`, crear una tabla `users` de compatibilidad y agregar un user de prueba
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            try:
                cur.execute("SELECT id FROM users WHERE username = %s", ('alumno',))
                if not cur.fetchone():
                    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", ('alumno', 'pass123'))
                    conn.commit()
            except Exception:
                pass
            cur.close()
            conn.close()
            print('INFO: usando MySQL para usuarios')
            return
        except MySQLError as e:
            print('WARN: No fue posible usar MySQL para users, fallback a SQLite:', e)

    # Fallback a SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('alumno', 'pass123'))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()


init_users_db()
print('DEBUG: users DB path ->', os.path.abspath(DB_PATH))
try:
    conn_debug = sqlite3.connect(DB_PATH)
    cur_debug = conn_debug.cursor()
    cur_debug.execute("SELECT id, username FROM users")
    print('DEBUG: users in DB ->', cur_debug.fetchall())
    conn_debug.close()
except Exception as _e:
    print('DEBUG: could not read users DB at startup:', _e)


def groq_chat(messages: list[dict]) -> str:
    """Intenta llamar a Groq si está disponible, sino devuelve un fallback."""
    if not GROQ_AVAILABLE:
        # Fallback simple: eco o respuesta estática
        user_msg = ''
        for m in reversed(messages):
            if m.get('role') == 'user':
                user_msg = m.get('content')
                break
        return f"(Respuesta simulada) Entiendo: {user_msg[:200]}"

    api_key = os.getenv('GROQ_API_KEY') or os.getenv('GROQ_API_KEY_ENCRYPTED')
    if not api_key:
        return "(Respuesta simulada) No hay API key configurada."

    client = Groq(api_key=api_key)
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
    return "(Respuesta simulada) Error generando respuesta."


@app.post('/api/generate_question')
def api_generate_question():
    q = random.choice(SAMPLE_QUESTIONS)
    return jsonify({"question": q})


@app.post('/api/login')
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    # Intentar consultar en MySQL si está disponible
    if USE_MYSQL_FOR_USERS:
        try:
            print(f"DEBUG: login attempt for user '{username}' using MySQL")
            conn = mysql.connector.connect(**MYSQL_USERS_CONFIG)
            cur = conn.cursor()
            # Primero intentar con la tabla `usuarios` (esquema del dump mysql_base.sql)
            try:
                cur.execute("SELECT usuario_id, password FROM usuarios WHERE username = %s", (username,))
                row = cur.fetchone()
                if row:
                    user_id, pw = row
                else:
                    # Si no existe, intentar tabla legacy `users`
                    cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
                    row = cur.fetchone()
            except Exception:
                # En caso de que `usuarios` no exista o haya error, intentar `users`
                try:
                    cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
                    row = cur.fetchone()
                except Exception:
                    row = None
            # Si row fue encontrada y aún no hemos asignado pw/user_id, hazlo ahora (para casos donde usuarios returned)
            if row:
                # row puede ser (usuario_id, password) o (id, password)
                user_id, pw = row
            cur.close()
            conn.close()
            if not row:
                return jsonify({"ok": False, "error": "user not found"}), 401
            if pw != password:
                return jsonify({"ok": False, "error": "invalid credentials"}), 401
            return jsonify({"ok": True, "user_id": user_id, "username": username})
        except Exception as e:
            print(f"ERROR: MySQL login error: {e}")
            # Caer a SQLite si hay problema inesperado

    # Fallback: SQLite local
    try:
        print(f"DEBUG: login attempt for user '{username}' using SQLite DB: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"ok": False, "error": "user not found"}), 401
        user_id, pw = row
        if pw != password:
            return jsonify({"ok": False, "error": "invalid credentials"}), 401
        return jsonify({"ok": True, "user_id": user_id, "username": username})
    except Exception as e:
        print(f"ERROR: SQLite login error: {e}")
        return jsonify({"ok": False, "error": "internal error"}), 500


@app.post('/api/chat')
def api_chat():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    role = (data.get('role') or 'student')
    if not text:
        return jsonify({"error": "text is required"}), 400

    if role == 'student':
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]
    else:
        messages = [
            {"role": "system", "content": PROMPT_ALUMNO},
            {"role": "user", "content": text},
        ]

    try:
        reply = groq_chat(messages)
    except Exception:
        reply = "(Respuesta simulada) Hubo un problema generando la respuesta."

    return jsonify({"reply": reply})


def insert_conversacion_mysql(personaje: str, mensaje: str, turno: int, duracion_segundos: float):
    try:
        conn = mysql.connector.connect(**MYSQL_USERS_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO conversaciones (personaje, mensaje, turno, duracion_segundos) VALUES (%s, %s, %s, %s)",
            (personaje, mensaje, turno, duracion_segundos),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print('WARN: could not insert into MySQL conversaciones:', e)
        return False


def fetch_conversaciones_mysql(limit: int = 50):
    try:
        conn = mysql.connector.connect(**MYSQL_USERS_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT id, timestamp, personaje, mensaje, turno, duracion_segundos FROM conversaciones ORDER BY id DESC LIMIT %s", (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        result = []
        for r in rows:
            result.append({
                'id': r[0],
                'timestamp': r[1].isoformat() if hasattr(r[1], 'isoformat') else str(r[1]),
                'personaje': r[2],
                'mensaje': r[3],
                'turno': r[4],
                'duracion_segundos': float(r[5]) if r[5] is not None else 0.0,
            })
        return result
    except Exception as e:
        print('WARN: could not fetch MySQL conversaciones:', e)
        return []


@app.get('/api/conversaciones')
def api_get_conversaciones():
    # Intentar MySQL primero
    convs = fetch_conversaciones_mysql(50)
    return jsonify({'conversaciones': convs})


@app.post('/api/simulate_call')
def api_simulate_call():
    # Simula un pequeño intercambio alumno <-> profesora, guarda en la tabla `conversaciones`
    try:
        # Generar pregunta inicial
        q = random.choice(SAMPLE_QUESTIONS)
        inserted = []

        # Turno 0: alumno pregunta
        dur = round(random.uniform(2.0, 8.0), 5)
        ok = insert_conversacion_mysql('Carlos', q, 0, dur)
        inserted.append({'personaje': 'Carlos', 'mensaje': q, 'turno': 0, 'duracion_segundos': dur, 'saved': ok})

        # Turno 1: profesora responde
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q},
        ]
        reply = groq_chat(messages)
        dur2 = round(random.uniform(4.0, 40.0), 5)
        ok2 = insert_conversacion_mysql('Profesora García', reply, 1, dur2)
        inserted.append({'personaje': 'Profesora García', 'mensaje': reply, 'turno': 1, 'duracion_segundos': dur2, 'saved': ok2})

        # Opcional: un breve intercambio de seguimiento (uno más)
        follow_q = groq_chat([{"role": "system", "content": PROMPT_ALUMNO}, {"role": "user", "content": reply}])
        dur3 = round(random.uniform(2.0, 10.0), 5)
        ok3 = insert_conversacion_mysql('Carlos', follow_q, 2, dur3)
        inserted.append({'personaje': 'Carlos', 'mensaje': follow_q, 'turno': 2, 'duracion_segundos': dur3, 'saved': ok3})

        # Profesora finaliza
        final_reply = groq_chat([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": follow_q}])
        dur4 = round(random.uniform(3.0, 20.0), 5)
        ok4 = insert_conversacion_mysql('Profesora García', final_reply, 3, dur4)
        inserted.append({'personaje': 'Profesora García', 'mensaje': final_reply, 'turno': 3, 'duracion_segundos': dur4, 'saved': ok4})

        return jsonify({'ok': True, 'inserted': inserted})
    except Exception as e:
        print('ERROR simulate_call:', e)
        return jsonify({'ok': False, 'error': str(e)}), 500


# Ejecutar el script `llamada_completa.py` en segundo plano y devolver respuesta inmediata
RUNNING_JOBS: dict = {}
# Colas de eventos por job (Server-Sent Events)
RUNNING_EVENT_QUEUES: dict = {}

def _run_llamada_script(job_id: str):
    script_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'llamada_completa.py'))
    try:
        print(f"INFO: starting llamada_completa.py for job {job_id} -> {script_path}")
        env = os.environ.copy()
        env.setdefault('PYTHONIOENCODING', 'utf-8')

        # Preparar cola de eventos
        q = queue.Queue()
        RUNNING_EVENT_QUEUES[job_id] = q
        RUNNING_JOBS[job_id] = {'status': 'running'}

        # Usar Popen para leer stdout en tiempo real
        p = subprocess.Popen(
            [sys.executable, script_path, '--auto'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            bufsize=1,
        )

        stdout_lines = []

        # Leer stdout en tiempo real
        try:
            if p.stdout:
                for raw_line in p.stdout:
                    line = raw_line.rstrip('\n')
                    stdout_lines.append(line + '\n')
                    # Eventos emitidos por el script vienen prefijados con `EVENT:` y JSON
                    if line.startswith('EVENT:'):
                        payload = line[len('EVENT:'):].strip()
                        try:
                            obj = json.loads(payload)
                            q.put(obj)
                        except Exception:
                            q.put({'type': 'raw', 'line': line})

        except Exception as e:
            print(f"WARN: error leyendo stdout del proceso {job_id}: {e}")

        # Esperar a que termine y leer stderr
        p.wait()
        stderr_text = ''
        try:
            if p.stderr:
                stderr_text = p.stderr.read()
        except Exception:
            stderr_text = ''

        RUNNING_JOBS[job_id] = {'status': 'done', 'stdout': ''.join(stdout_lines), 'stderr': stderr_text}
        # Señalar fin del job por la cola de eventos
        try:
            q.put({'type': 'job_done', 'status': 'done'})
        except Exception:
            pass

        # dejar la cola un tiempo antes de limpiarla para que el frontend pueda leer
        time.sleep(0.5)
        # no eliminamos inmediatamente la cola; la API de stream consumirá hasta job_done
        print(f"INFO: job {job_id} finished. stderr:\n{stderr_text}")
    except Exception as e:
        RUNNING_JOBS[job_id] = {'status': 'error', 'error': str(e)}
        try:
            RUNNING_EVENT_QUEUES.get(job_id, queue.Queue()).put({'type': 'job_done', 'status': 'error', 'error': str(e)})
        except Exception:
            pass
        print(f"ERROR running llamada_completa.py for job {job_id}: {e}")


@app.post('/api/run_llamada')
def api_run_llamada():
    # Crea un job, ejecuta el script en background y devuelve job id
    job_id = str(uuid.uuid4())
    RUNNING_JOBS[job_id] = {'status': 'running'}
    # crear cola de eventos vacía para este job
    RUNNING_EVENT_QUEUES[job_id] = queue.Queue()
    t = threading.Thread(target=_run_llamada_script, args=(job_id,), daemon=True)
    t.start()
    return jsonify({'ok': True, 'job_id': job_id})


@app.get('/api/run_llamada/stream/<job_id>')
def api_run_llamada_stream(job_id: str):
    # Stream SSE: envía eventos generados por el script en tiempo real
    if job_id not in RUNNING_EVENT_QUEUES:
        return jsonify({'ok': False, 'error': 'stream not found'}), 404

    q = RUNNING_EVENT_QUEUES[job_id]

    def event_stream():
        # mientras haya eventos o el job no termine, emitimos
        finished = False
        while True:
            try:
                ev = q.get(timeout=1.0)
                # enviar como JSON
                try:
                    data = json.dumps(ev, ensure_ascii=False)
                except Exception:
                    data = json.dumps({'type': 'raw', 'payload': str(ev)})
                yield f"data: {data}\n\n"
                if isinstance(ev, dict) and ev.get('type') == 'job_done':
                    break
            except queue.Empty:
                # revisar estado del job
                info = RUNNING_JOBS.get(job_id)
                if info and info.get('status') in ('done', 'error'):
                    yield f"data: {json.dumps({'type':'job_status','status': info.get('status')})}\n\n"
                    break
                continue

    return Response(event_stream(), mimetype='text/event-stream')


@app.get('/api/run_llamada/status/<job_id>')
def api_run_llamada_status(job_id: str):
    info = RUNNING_JOBS.get(job_id)
    if not info:
        return jsonify({'ok': False, 'error': 'job not found'}), 404
    return jsonify({'ok': True, 'job': info})


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', '5001'))
    print(f"API (simulación) escuchando en http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)
