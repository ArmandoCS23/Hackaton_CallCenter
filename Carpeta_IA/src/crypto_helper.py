"""
Utilidad para cifrar/descifrar claves de API de forma segura.
Usa XOR simple con clave aleatoria persistente.
"""
import os
import base64


def get_or_create_key() -> bytes:
    """Obtiene o crea la clave de cifrado maestra (32 bytes aleatorios)."""
    key_file = ".cipher_key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        import secrets
        key = secrets.token_bytes(32)
        with open(key_file, "wb") as f:
            f.write(key)
        print(f"[Clave de cifrado creada en {key_file}. ¡NO LA COMPARTAS!]")
        return key


def xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR de bytes con clave (repite clave si es necesario)."""
    return bytes(a ^ key[i % len(key)] for i, a in enumerate(data))


def encrypt_api_key(plain_key: str) -> str:
    """Cifra una API key."""
    cipher_key = get_or_create_key()
    encrypted = xor_bytes(plain_key.encode(), cipher_key)
    return base64.b64encode(encrypted).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Descifra una API key."""
    cipher_key = get_or_create_key()
    encrypted = base64.b64decode(encrypted_key.encode())
    decrypted = xor_bytes(encrypted, cipher_key)
    return decrypted.decode()


if __name__ == "__main__":
    # Script de ayuda para cifrar tu clave
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--encrypt":
            plain = input("Ingresa la API key a cifrar: ").strip()
            encrypted = encrypt_api_key(plain)
            print(f"\nClave cifrada:\n{encrypted}")
            print("\nGuárdala en .env como:")
            print(f"GROQ_API_KEY_ENCRYPTED={encrypted}")
        elif sys.argv[1] == "--decrypt":
            encrypted = input("Ingresa la clave cifrada: ").strip()
            try:
                plain = decrypt_api_key(encrypted)
                print(f"\nClave descifrada:\n{plain}")
            except Exception as e:
                print(f"Error al descifrar: {e}")
    else:
        print("Uso:")
        print("  python src/crypto_helper.py --encrypt  # Cifrar una clave")
        print("  python src/crypto_helper.py --decrypt  # Descifrar una clave")
