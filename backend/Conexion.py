from __future__ import annotations

import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / "Frontend" / ".env", override=False)


class Conexion:

    def __init__(self) -> None:
        self.conexion = None

    def conectar(self):
        host = os.getenv("AZURE_MYSQL_HOST", "").strip()
        database = os.getenv("AZURE_MYSQL_DATABASE", "").strip()
        user = os.getenv("AZURE_MYSQL_USER", "").strip()
        password = os.getenv("AZURE_MYSQL_PASSWORD", "")

        if not all((host, database, user, password)):
            raise RuntimeError(
                "Configura AZURE_MYSQL_HOST, AZURE_MYSQL_DATABASE, "
                "AZURE_MYSQL_USER y AZURE_MYSQL_PASSWORD en el archivo .env."
            )

        opciones = {
            "host": host,
            "port": int(os.getenv("AZURE_MYSQL_PORT", "3306")),
            "database": database,
            "user": user,
            "password": password,
            "connection_timeout": 10,
            "ssl_disabled": False,
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
        }
        certificado = os.getenv("AZURE_MYSQL_SSL_CA", "").strip()
        if certificado:
            ruta_certificado = Path(certificado)
            if not ruta_certificado.is_file():
                raise RuntimeError(f"No se encontró el certificado TLS: {certificado}")
            opciones["ssl_ca"] = str(ruta_certificado)

        self.conexion = mysql.connector.connect(**opciones)
        return self.conexion

    def desconectar(self) -> None:
        if self.conexion is not None and self.conexion.is_connected():
            self.conexion.close()
            self.conexion = None
