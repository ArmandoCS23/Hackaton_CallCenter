# Profesora IA (Simulación de llamada)

Aplicación de línea de comandos que simula a una profesora de escuela atendiendo una llamada de un alumno y respondiendo exclusivamente sobre temas escolares.

Usa la API de Groq para generar respuestas rápidas y seguras. **Incluye reconocimiento de voz por micrófono** para una experiencia más realista.

## Requisitos

- Python 3.9+
- Cuenta y API key de Groq

## Configuración

1. Crea un entorno virtual (opcional pero recomendado).
2. Instala dependencias:

```powershell
pip install -r requirements.txt
```

3. Configura tu API key de Groq:

Opción rápida (sin cifrado, para desarrollo local):
```powershell
$env:GROQ_API_KEY = "TU_API_KEY_REAL"
```
Alternativa con archivo `.env` (no se sube al repo):
```
GROQ_API_KEY=TU_API_KEY_REAL
```

Opción recomendada (cifrada) usando el helper incluido:

```powershell
python .\src\crypto_helper.py --encrypt
```
Ingresa tu clave cuando lo pida. El script generará:

```
Clave cifrada:
<VALOR_CIFRADO>

Guárdala en .env como:
GROQ_API_KEY_ENCRYPTED=<VALOR_CIFRADO>
```

Luego en tu `.env` coloca solo:
```
GROQ_API_KEY_ENCRYPTED=<VALOR_CIFRADO>
```

El archivo `.cipher_key` se crea automáticamente y está ignorado por Git. NO lo compartas. Si se pierde, las claves cifradas ya guardadas no podrán descifrarse.

Si expusiste alguna vez tu clave (como en un commit o chat), ROTARLA en el panel de Groq y actualizar el valor cifrado.

NOTA: El esquema actual usa XOR + key local (seguridad básica para evitar exposición accidental). Para mayor robustez en producción considera reemplazarlo por `cryptography.Fernet` o un gestor de secretos (Azure Key Vault, AWS Secrets Manager, etc.).

## Uso

Inicia la simulación de llamada con micrófono:

```powershell
python src\profesor_llamada.py
```

Habla por el micrófono para interactuar. El sistema transcribirá tu voz automáticamente.

**Modo texto** (entrada por teclado):

```powershell
python src\profesor_llamada.py --text
## Llamada telefónica real (Twilio)

Configura un número telefónico que enruta a tu servidor Flask usando Twilio.

1. Crea cuenta en Twilio y compra un número con voz.
2. En `.env`, añade:

```
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

3. Ejecuta el servidor Flask:

```powershell
python .\src\server.py
```

4. Expón tu servidor con `ngrok` (o similar) y usa la URL pública en el webhook de voz del número:

```
ngrok http 5000
```

5. En Twilio Console, en Voice Webhook del número, pon:
- Request URL (POST): `https://TU_URL_PUBLICA/voice`

6. Llama al número. Twilio transcribe tu voz y enviará las peticiones a `/respond`, que responderá con Groq + TTS.

Para terminar la llamada, di “adiós” o “hasta luego”.
```

### Voz (TTS)

El asistente usa **gTTS** (Google Text-to-Speech) con voz en español. Es gratis, de buena calidad y compatible con Python 3.9.

#### Acentos disponibles

Puedes cambiar el acento configurando `GTTS_TLD` en `.env`:
- `es` — Español de España - **predeterminado**
- `com.mx` — Español de México
- `com.ar` — Español de Argentina

Ejemplo en `.env`:
```
GTTS_TLD=com.mx
```

#### Controles de voz

- Flags al iniciar:
  - `--mute`: inicia con voz desactivada
  - `--rate <entero>`: velocidad de voz (palabras/min)
  - `--volume <0.0-1.0>`: volumen inicial
  - `--text`: usa entrada de texto en lugar de micrófono

- Comandos durante la llamada (solo en modo `--text`):
  - `/mute` o `/silencio` — desactiva voz
  - `/unmute` o `/voz` — activa voz
  - `/rate 180` — ajusta velocidad
  - `/volume 0.7` — ajusta volumen

- Para salir: di "adiós" o "salir" (micrófono) o presiona Ctrl+CEjemplos:

```powershell
python .\src\profesor_llamada.py --rate 180 --volume 0.8
```

En ejecución:

```
Alumno: /mute
Alumno: /rate 160
Alumno: /volume 0.6
```

## Nota de seguridad

- El asistente está limitado a contenidos escolares. Preguntas fuera de ese ámbito serán rechazadas educadamente.
- Se siguen políticas para evitar contenido dañino, odioso, sexualmente explícito o violento.
 - No subas tu `.env` ni `.cipher_key`. La clave cifrada por sí sola no sirve sin la clave local.
