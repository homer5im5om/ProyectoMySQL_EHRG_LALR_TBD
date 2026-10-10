import getpass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
BACKEND_DIR = PROJECT_ROOT / "backend"
for carpeta in (SQL_DIR, BACKEND_DIR):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

from database import conectar, obtener_clave_aes
from security import generar_hash


def main():
    print("=== Crear administrador inicial ===")
    username = input("Nombre de usuario: ").strip()
    email = input("Correo electrónico: ").strip()
    nombre = input("Nombre: ").strip()
    apellido = input("Apellido: ").strip()
    rfc = input("RFC de prueba (12 o 13 caracteres): ").strip().upper()
    password = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
    confirmar = getpass.getpass("Confirmar contraseña: ")

    if not all((username, email, nombre, apellido, rfc)):
        raise SystemExit("Todos los campos son obligatorios.")
    if len(username) > 50 or len(email) > 100 or len(nombre) > 50 or len(apellido) > 50:
        raise SystemExit("Uno de los campos supera la longitud permitida por la tabla.")
    if len(rfc) not in (12, 13):
        raise SystemExit("El RFC debe tener 12 o 13 caracteres.")
    if password != confirmar:
        raise SystemExit("Las contraseñas no coinciden.")

    conn = conectar()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE LOWER(rol) IN ('admin', 'administrador')")
        if cur.fetchone()["total"]:
            raise SystemExit("Ya existe un administrador. Por seguridad, no se creó otro automáticamente.")
        key = obtener_clave_aes()
        cur.execute(
            """INSERT INTO usuarios
                 (username, email, password_hash, nombre, apellido, rol, estado_cuenta,
                  rfc, telefono, tarjeta_credito)
               VALUES (%s, %s, %s, %s, %s, 'administrador', 'activo',
                       AES_ENCRYPT(%s, %s), AES_ENCRYPT(NULL, %s), AES_ENCRYPT(NULL, %s))""",
            (username, email, generar_hash(password), nombre, apellido, rfc, key, key, key),
        )
        conn.commit()
        print("Administrador creado. Ya puedes iniciar sesión en login.py.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
