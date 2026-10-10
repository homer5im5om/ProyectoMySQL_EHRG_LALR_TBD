import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "Frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

from security import es_administrador, generar_hash, verificar_hash

# Los tests de reglas de base de datos se importan con un conector ficticio si
# mysql-connector-python no está instalado en el entorno de pruebas.
try:
    import mysql.connector  # noqa: F401
except ModuleNotFoundError:
    import types
    mysql_stub = types.ModuleType("mysql")
    connector_stub = types.ModuleType("mysql.connector")
    connector_stub.connect = lambda **_kwargs: None
    mysql_stub.connector = connector_stub
    sys.modules.setdefault("mysql", mysql_stub)
    sys.modules.setdefault("mysql.connector", connector_stub)

sys.path.insert(0, str(PROJECT_ROOT / "sql"))
import database


class SeguridadTests(unittest.TestCase):
    def test_hash_verifica_contrasena_correcta(self):
        hash_guardado = generar_hash("MiClaveSegura_2026")
        self.assertTrue(verificar_hash("MiClaveSegura_2026", hash_guardado))
        self.assertFalse(verificar_hash("otra-clave", hash_guardado))

    def test_hash_usa_salt_diferente(self):
        hash_uno = generar_hash("MiClaveSegura_2026")
        hash_dos = generar_hash("MiClaveSegura_2026")
        self.assertNotEqual(hash_uno, hash_dos)
        self.assertTrue(verificar_hash("MiClaveSegura_2026", hash_uno))
        self.assertTrue(verificar_hash("MiClaveSegura_2026", hash_dos))

    def test_rechaza_contrasena_corta(self):
        with self.assertRaises(ValueError):
            generar_hash("1234567")

    def test_roles(self):
        self.assertTrue(es_administrador("administrador"))
        self.assertTrue(es_administrador("ADMIN"))
        self.assertFalse(es_administrador("cliente"))
        self.assertFalse(es_administrador("empleado"))

    def test_hash_malformado_no_falla(self):
        self.assertFalse(verificar_hash("cualquier-clave", "hash-incorrecto"))

    def test_rol_y_estado_validos(self):
        database._validar_rol_y_estado("administrador", "activo")
        database._validar_rol_y_estado("cliente", "inactivo")

    def test_rol_invalido_se_rechaza(self):
        with self.assertRaises(ValueError):
            database._validar_rol_y_estado("superusuario", "activo")

    def test_estado_invalido_se_rechaza(self):
        with self.assertRaises(ValueError):
            database._validar_rol_y_estado("cliente", "suspendido")


if __name__ == "__main__":
    unittest.main()
