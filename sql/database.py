import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for carpeta in (PROJECT_ROOT / "backend", PROJECT_ROOT / "Frontend"):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

# La configuración canónica está en la raíz. Se admite Frontend/.env por compatibilidad.
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / "Frontend" / ".env", override=False)

from Conexion import Conexion
from security import es_administrador, generar_hash, verificar_hash


def obtener_clave_aes() -> str:
    clave = os.getenv("AZURE_MYSQL_AES_KEY", "")
    if len(clave) < 16:
        raise RuntimeError(
            "Configura AZURE_MYSQL_AES_KEY en el archivo .env con una clave de "
            "al menos 16 caracteres."
        )
    return clave


def conectar():
    return Conexion().conectar()


def _rol_actor(cursor, actor_id: int) -> str:
    cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (actor_id,))
    fila = cursor.fetchone()
    if not fila:
        raise PermissionError("La sesión ya no corresponde a un usuario válido.")
    return fila["rol"] or "cliente"


def _exigir_admin(cursor, actor_id: int) -> None:
    if not es_administrador(_rol_actor(cursor, actor_id)):
        raise PermissionError("Esta operación requiere permisos de administrador.")


def autenticar(identificador: str, contrasena: str) -> dict[str, Any] | None:
    conn = conectar()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT id, username, email, password_hash, rol, estado_cuenta
               FROM usuarios WHERE username = %s LIMIT 1""",
            (identificador.strip(),),
        )
        fila = cur.fetchone()
        if not fila:
            cur.execute(
                """SELECT id, username, email, password_hash, rol, estado_cuenta
                   FROM usuarios WHERE email = %s LIMIT 1""",
                (identificador.strip(),),
            )
            fila = cur.fetchone()

        if not fila:
            conn.commit()
            return None

        estado = (fila.get("estado_cuenta") or "activo").strip().casefold()
        hash_guardado = fila.get("password_hash") or ""
        if estado != "activo" or not verificar_hash(contrasena, hash_guardado):
            cur.execute(
                """UPDATE usuarios
                   SET intentos_fallidos = LEAST(COALESCE(intentos_fallidos, 0) + 1, 255)
                   WHERE id = %s""",
                (fila["id"],),
            )
            conn.commit()
            return None

        cur.execute(
            """UPDATE usuarios
               SET ultimo_acceso = NOW(), intentos_fallidos = 0
               WHERE id = %s""",
            (fila["id"],),
        )
        conn.commit()
        return {
            "id": fila["id"],
            "username": fila["username"],
            "email": fila["email"],
            "rol": fila.get("rol") or "cliente",
        }
    finally:
        conn.close()


def listar_usuarios(actor_id: int) -> tuple[list[dict[str, Any]], bool]:
    conn = conectar()
    try:
        cur = conn.cursor(dictionary=True)
        rol = _rol_actor(cur, actor_id)
        admin = es_administrador(rol)

        if admin:
            clave = obtener_clave_aes()
            cur.execute(
                """SELECT id, username, email, nombre, apellido, fecha_nacimiento,
                          rol, estado_cuenta,
                          CAST(AES_DECRYPT(rfc, %s) AS CHAR CHARACTER SET utf8mb4) AS rfc,
                          CAST(AES_DECRYPT(telefono, %s) AS CHAR CHARACTER SET utf8mb4) AS telefono,
                          CAST(AES_DECRYPT(tarjeta_credito, %s) AS CHAR CHARACTER SET utf8mb4) AS tarjeta_credito,
                          fecha_registro, ultimo_acceso, intentos_fallidos
                   FROM usuarios ORDER BY id""",
                (clave, clave, clave),
            )
        else:
            cur.execute(
                """SELECT id, username, email, nombre, apellido, fecha_nacimiento,
                          rol, estado_cuenta, fecha_registro, ultimo_acceso
                   FROM usuarios ORDER BY id"""
            )
        return cur.fetchall(), admin
    finally:
        conn.close()


def obtener_usuario(actor_id: int, usuario_id: int) -> dict[str, Any]:
    """Obtiene datos de edición; solo administradores pueden consultarlos."""
    conn = conectar()
    try:
        cur = conn.cursor(dictionary=True)
        _exigir_admin(cur, actor_id)
        clave = obtener_clave_aes()
        cur.execute(
            """SELECT id, username, email, nombre, apellido, fecha_nacimiento,
                      rol, estado_cuenta,
                      CAST(AES_DECRYPT(rfc, %s) AS CHAR CHARACTER SET utf8mb4) AS rfc,
                      CAST(AES_DECRYPT(telefono, %s) AS CHAR CHARACTER SET utf8mb4) AS telefono,
                      CAST(AES_DECRYPT(tarjeta_credito, %s) AS CHAR CHARACTER SET utf8mb4) AS tarjeta_credito
               FROM usuarios WHERE id = %s""",
            (clave, clave, clave, usuario_id),
        )
        fila = cur.fetchone()
        if not fila:
            raise ValueError("No se encontró el usuario seleccionado.")
        return fila
    finally:
        conn.close()



def _validar_rol_y_estado(rol: str, estado_cuenta: str = "activo") -> None:
    roles_validos = {"administrador", "cliente"}
    estados_validos = {"activo", "inactivo"}
    if (rol or "").strip().casefold() not in roles_validos:
        raise ValueError("El rol debe ser 'administrador' o 'cliente'.")
    if (estado_cuenta or "").strip().casefold() not in estados_validos:
        raise ValueError("El estado de cuenta debe ser 'activo' o 'inactivo'.")


def crear_usuario(actor_id: int, datos: dict[str, Any]) -> None:
    _validar_rol_y_estado(datos.get("rol", ""), datos.get("estado_cuenta", ""))
    conn = conectar()
    try:
        cur = conn.cursor(dictionary=True)
        _exigir_admin(cur, actor_id)
        clave = obtener_clave_aes()
        hash_password = generar_hash(datos["password"])
        cur.execute(
            """INSERT INTO usuarios
                 (username, email, password_hash, nombre, apellido, fecha_nacimiento,
                  rol, estado_cuenta, rfc, telefono, tarjeta_credito)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                       AES_ENCRYPT(%s, %s), AES_ENCRYPT(%s, %s), AES_ENCRYPT(%s, %s))""",
            (
                datos["username"], datos["email"], hash_password,
                datos["nombre"], datos["apellido"], datos.get("fecha_nacimiento") or None,
                datos["rol"], datos["estado_cuenta"],
                datos["rfc"], clave,
                datos.get("telefono") or None, clave,
                datos.get("tarjeta_credito") or None, clave,
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def actualizar_usuario(actor_id: int, usuario_id: int, datos: dict[str, Any]) -> None:
    _validar_rol_y_estado(datos.get("rol", ""), datos.get("estado_cuenta", ""))
    conn = conectar()
    try:
        cur = conn.cursor(dictionary=True)
        _exigir_admin(cur, actor_id)
        _evitar_quedarse_sin_admin(cur, usuario_id, datos["rol"])
        clave = obtener_clave_aes()
        asignaciones = [
            "username = %s", "email = %s", "nombre = %s", "apellido = %s",
            "fecha_nacimiento = %s", "rol = %s", "estado_cuenta = %s",
            "rfc = AES_ENCRYPT(%s, %s)",
            "telefono = AES_ENCRYPT(%s, %s)",
            "tarjeta_credito = AES_ENCRYPT(%s, %s)",
        ]
        valores = [
            datos["username"], datos["email"], datos["nombre"], datos["apellido"],
            datos.get("fecha_nacimiento") or None, datos["rol"], datos["estado_cuenta"],
            datos["rfc"], clave, datos.get("telefono") or None, clave,
            datos.get("tarjeta_credito") or None, clave,
        ]
        if datos.get("password"):
            asignaciones.append("password_hash = %s")
            valores.append(generar_hash(datos["password"]))
        valores.append(usuario_id)
        cur.execute(
            f"UPDATE usuarios SET {', '.join(asignaciones)} WHERE id = %s",
            tuple(valores),
        )
        if cur.rowcount == 0:
            cur.execute("SELECT id FROM usuarios WHERE id = %s", (usuario_id,))
            if not cur.fetchone():
                raise ValueError("No se encontró el usuario seleccionado.")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def cambiar_rol(actor_id: int, usuario_id: int, nuevo_rol: str) -> None:
    if (nuevo_rol or "").strip().casefold() not in {"administrador", "cliente"}:
        raise ValueError("El rol debe ser 'administrador' o 'cliente'.")
    conn = conectar()
    try:
        cur = conn.cursor(dictionary=True)
        _exigir_admin(cur, actor_id)
        _evitar_quedarse_sin_admin(cur, usuario_id, nuevo_rol)
        cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, usuario_id))
        if cur.rowcount == 0:
            cur.execute("SELECT id FROM usuarios WHERE id = %s", (usuario_id,))
            if not cur.fetchone():
                raise ValueError("No se encontró el usuario seleccionado.")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _evitar_quedarse_sin_admin(cur, usuario_id: int, nuevo_rol: str) -> None:
    cur.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
    fila = cur.fetchone()
    if not fila:
        raise ValueError("No se encontró el usuario seleccionado.")
    if es_administrador(fila.get("rol")) and not es_administrador(nuevo_rol):
        cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE LOWER(rol) IN ('admin', 'administrador')")
        total = cur.fetchone()["total"]
        if total <= 1:
            raise ValueError("No puedes quitar el rol al último administrador.")


def eliminar_usuario(actor_id: int, usuario_id: int) -> None:
    conn = conectar()
    try:
        cur = conn.cursor(dictionary=True)
        _exigir_admin(cur, actor_id)
        if int(actor_id) == int(usuario_id):
            raise ValueError("No puedes eliminar la cuenta con la que has iniciado sesión.")
        cur.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
        fila = cur.fetchone()
        if not fila:
            raise ValueError("No se encontró el usuario seleccionado.")
        if es_administrador(fila.get("rol")):
            cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE LOWER(rol) IN ('admin', 'administrador')")
            if cur.fetchone()["total"] <= 1:
                raise ValueError("No puedes eliminar al último administrador.")
        cur.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
