from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for carpeta in (PROJECT_ROOT / "sql", PROJECT_ROOT / "Frontend", PROJECT_ROOT / "backend"):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

import database as persistencia


class UsuarioDAO:
    def autenticar(self, identificador: str, contrasena: str) -> dict[str, Any] | None:
        return persistencia.autenticar(identificador, contrasena)

    def listar_usuarios(self, actor_id: int) -> tuple[list[dict[str, Any]], bool]:
        return persistencia.listar_usuarios(actor_id)

    def obtener_usuario(self, actor_id: int, usuario_id: int) -> dict[str, Any]:
        return persistencia.obtener_usuario(actor_id, usuario_id)

    def crear_usuario(self, actor_id: int, datos: dict[str, Any]) -> None:
        persistencia.crear_usuario(actor_id, datos)

    def actualizar_usuario(self, actor_id: int, usuario_id: int, datos: dict[str, Any]) -> None:
        persistencia.actualizar_usuario(actor_id, usuario_id, datos)

    def cambiar_rol(self, actor_id: int, usuario_id: int, nuevo_rol: str) -> None:
        persistencia.cambiar_rol(actor_id, usuario_id, nuevo_rol)

    def eliminar_usuario(self, actor_id: int, usuario_id: int) -> None:
        persistencia.eliminar_usuario(actor_id, usuario_id)
