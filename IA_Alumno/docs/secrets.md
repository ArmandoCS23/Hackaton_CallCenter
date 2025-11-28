# Manejo seguro de la API key de Groq

Estas son opciones seguras para no subir claves en texto plano a GitHub. Las mismas recomendaciones aplican para otras claves como `OPENAI_API_KEY`.

1) Recomendado: usar GitHub Secrets (no versionar la clave)
- Desde la interfaz web: Repo → Settings → Secrets and variables → Actions → New repository secret. Ponga `GROQ_API_KEY` como nombre y su valor.
- Con `gh` (GitHub CLI):

  ```powershell
  gh auth login
  gh secret set GROQ_API_KEY --body "<TU_API_KEY_AQUI>"
  gh secret set OPENAI_API_KEY --body "<TU_OPENAI_API_KEY_AQUI>"
  ```

- En GitHub Actions, use la clave directamente:
  - Como variable de entorno en un job:
    ```yaml
    env:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
    ```
  - O escribirla en un `.env` temporal en el runner:
    ```yaml
    - name: Crear .env
      run: |
        echo "GROQ_API_KEY=${{ secrets.GROQ_API_KEY }}" > .env
        echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> .env
    ```

2) Alternativa: mantener un archivo cifrado en el repo
- Cree un archivo con la clave (por ejemplo `groq.key` o `.env`) y cifre con GPG simétrico:

  Linux/macOS:
  ```bash
  gpg --symmetric --cipher-algo AES256 -o groq.key.gpg groq.key
  ```

  Windows PowerShell (si tiene GPG instalado):
  ```powershell
  gpg --symmetric --cipher-algo AES256 -o groq.key.gpg groq.key
  ```

- Añada `groq.key.gpg` al repo y no añada el archivo plano.
- Para desencriptar en CI, guarde la PASSPHRASE en GitHub Secrets (por ejemplo `GPG_PASSPHRASE`) y en el workflow:

  ```yaml
  - name: Desencriptar claves
    env:
      GPG_PASSPHRASE: ${{ secrets.GPG_PASSPHRASE }}
    run: |
      gpg --batch --yes --passphrase "$GPG_PASSPHRASE" -o groq.key -d groq.key.gpg
      gpg --batch --yes --passphrase "$GPG_PASSPHRASE" -o openai.key -d openai.key.gpg
      echo "GROQ_API_KEY=$(cat groq.key)" > .env
      echo "OPENAI_API_KEY=$(cat openai.key)" >> .env
  ```

- Nota: pasar la passphrase por línea de comandos tiene riesgos; la alternativa es usar una clave pública/privada o herramientas como `sops` con `age`/KMS para flujos más seguros.

3) Para el repositorio local (no subir claves):
- Cree un archivo `.env` y agréguelo a `.gitignore` (ya está en `.gitignore` del proyecto).
- Ejemplo de `.env` (no lo suba):
  ```text
  GROQ_API_KEY=sk_...tu_clave_aqui...
  OPENAI_API_KEY=sk-...tu_clave_aqui...
  ```

4) Resumen de acciones recomendadas ahora que se ha eliminado la clave hardcodeada de `src/alumno_escolar.py`:
- Añada `GROQ_API_KEY` como GitHub Secret si quiere que CI lo use.
- Localmente, cree `.env` con la clave y no lo suba.
- Si realmente necesita subir una versión cifrada al repo, use GPG o `sops` y configure el desencriptado en CI usando un secreto que contenga la passphrase o clave necesaria.

Si quieres, puedo:
- Configurar un pequeño workflow de GitHub Actions que inyecte `GROQ_API_KEY` desde `secrets` y ejecute tus tests/run.
- Cifrar el valor por ti si pegas la API key aquí (nota: pegar la clave en el chat guarda la clave en el historial; por seguridad, prefiero que la pegues localmente y yo te doy el comando exacto para cifrarla en tu máquina).
