# Historial de versiones

## 1.0.0 — 2026-10-09

- Se integró el inicio de sesión por usuario o correo.
- Se incorporaron vistas separadas por clase para administrador y usuario normal.
- La tabla administrativa incluye controles de alta, modificación, eliminación y cambio de rol.
- La tabla del usuario normal es de solo lectura y no consulta columnas cifradas.
- Se incorporó `UsuarioDAO` como capa entre la interfaz y el módulo de persistencia.
- Se centralizó la conexión TLS y se unificaron las variables de configuración de Azure.
- Se añadieron instrucciones de instalación y pruebas unitarias de seguridad.
