import hashlib
import hmac
import secrets

ALGORITMO = "pbkdf2_sha256"
ITERACIONES = 600_000


def generar_hash(contrasena: str) -> str:
    if not isinstance(contrasena, str) or len(contrasena) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", contrasena.encode("utf-8"), salt, ITERACIONES
    )
    return f"{ALGORITMO}${ITERACIONES}${salt.hex()}${digest.hex()}"


def verificar_hash(contrasena: str, valor_guardado: str) -> bool:
    try:
        algoritmo, iteraciones, salt_hex, digest_hex = valor_guardado.split("$", 3)
        if algoritmo != ALGORITMO:
            return False
        salt = bytes.fromhex(salt_hex)
        esperado = bytes.fromhex(digest_hex)
        obtenido = hashlib.pbkdf2_hmac(
            "sha256", contrasena.encode("utf-8"), salt, int(iteraciones)
        )
        return hmac.compare_digest(obtenido, esperado)
    except (AttributeError, TypeError, ValueError):
        return False


def es_administrador(rol: str) -> bool:
    return (rol or "").strip().casefold() in {"administrador", "admin"}
