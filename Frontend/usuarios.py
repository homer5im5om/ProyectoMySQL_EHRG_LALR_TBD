from __future__ import annotations

import re
import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
BACKEND_DIR = PROJECT_ROOT / "backend"
for carpeta in (SQL_DIR, BACKEND_DIR):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

from UsuarioDAO import UsuarioDAO
from security import es_administrador

AZUL = "#2563eb"
AZUL_OSCURO = "#1d4ed8"
FONDO = "#eef2f7"
TEXTO = "#111827"
GRIS = "#6b7280"
BLANCO = "#ffffff"


class UsuariosWindow(tk.Toplevel):

    modo_administrador: bool | None = None

    def __init__(self, master: tk.Tk, usuario: dict[str, Any], on_logout: Callable[[], None]):
        super().__init__(master)
        self.usuario = usuario
        self.on_logout = on_logout
        self.dao = UsuarioDAO()
        self.es_admin = es_administrador(usuario.get("rol", ""))
        if self.modo_administrador is not None and self.modo_administrador != self.es_admin:
            self.destroy()
            raise PermissionError("La ventana solicitada no corresponde al rol de la sesión.")
        self.registros: list[dict[str, Any]] = []
        self.columnas: list[str] = []

        self.title(
            "Administración de usuarios" if self.es_admin
            else "Consulta de usuarios | Solo lectura"
        )
        self.geometry("1280x730")
        self.minsize(940, 580)
        self.configure(bg=FONDO)
        self.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        self._estilos()
        self._construir_interfaz()
        self.cargar_usuarios()

    def _estilos(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("Treeview", font=("Segoe UI", 10), rowheight=30,
                         background=BLANCO, fieldbackground=BLANCO, foreground=TEXTO)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                         background="#e5e7eb", foreground=TEXTO, padding=8)
        estilo.map("Treeview", background=[("selected", "#dbeafe")],
                   foreground=[("selected", TEXTO)])
        estilo.configure("Primary.TButton", font=("Segoe UI", 10, "bold"),
                         foreground=BLANCO, background=AZUL, padding=(12, 8), borderwidth=0)
        estilo.map("Primary.TButton", background=[("active", AZUL_OSCURO)])
        estilo.configure("Secondary.TButton", font=("Segoe UI", 10),
                         foreground=TEXTO, background="#e5e7eb", padding=(12, 8), borderwidth=0)
        estilo.map("Secondary.TButton", background=[("active", "#d1d5db")])
        estilo.configure("Danger.TButton", font=("Segoe UI", 10, "bold"),
                         foreground=BLANCO, background="#dc2626", padding=(12, 8), borderwidth=0)
        estilo.map("Danger.TButton", background=[("active", "#b91c1c")])

    def _construir_interfaz(self):
        encabezado = tk.Frame(self, bg=BLANCO, height=90)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(encabezado, text="US", font=("Segoe UI", 18, "bold"),
                 bg=AZUL, fg=BLANCO, width=4, height=2).pack(side="left", padx=(22, 14), pady=12)
        bloque = tk.Frame(encabezado, bg=BLANCO)
        bloque.pack(side="left", fill="y", pady=16)
        titulo = "Panel de administración" if self.es_admin else "Consulta de usuarios"
        tk.Label(bloque, text=titulo, font=("Segoe UI", 19, "bold"),
                 bg=BLANCO, fg=TEXTO).pack(anchor="w")
        detalle = (
            "Gestiona cuentas, permisos y datos protegidos."
            if self.es_admin
            else "Modo de solo lectura · Los datos cifrados permanecen ocultos."
        )
        tk.Label(bloque, text=detalle, font=("Segoe UI", 9),
                 bg=BLANCO, fg=GRIS).pack(anchor="w", pady=(2, 0))
        tk.Label(encabezado, text=f"{self.usuario.get('username')}  ·  {self.usuario.get('rol')}",
                 font=("Segoe UI", 10, "bold"), bg=BLANCO,
                 fg=AZUL if self.es_admin else GRIS).pack(side="right", padx=(0, 18), pady=25)

        ttk.Button(encabezado, text="Cerrar sesión", style="Secondary.TButton",
                   command=self.cerrar_ventana).pack(side="right", padx=22, pady=25)
        ttk.Button(encabezado, text="Actualizar", style="Secondary.TButton",
                   command=self.cargar_usuarios).pack(side="right", padx=(0, 10), pady=25)

        cuerpo = tk.Frame(self, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=22, pady=20)

        barra = tk.Frame(cuerpo, bg=FONDO)
        barra.pack(fill="x", pady=(0, 14))
        tk.Label(barra, text="Buscar", font=("Segoe UI", 10, "bold"),
                 bg=FONDO, fg=TEXTO).pack(side="left", padx=(0, 8))
        self.buscar_var = tk.StringVar()
        self.buscar_entry = ttk.Entry(barra, textvariable=self.buscar_var, width=32)
        self.buscar_entry.pack(side="left", ipady=4)
        self.buscar_entry.bind("<KeyRelease>", lambda _e: self.aplicar_filtro())

        if self.es_admin:
            texto_permiso = "Modo administrador: puedes crear, editar, eliminar usuarios y cambiar roles."
        else:
            texto_permiso = "Modo de solo lectura: puedes consultar la tabla, sin modificar usuarios."
        tk.Label(barra, text=texto_permiso, font=("Segoe UI", 9), bg=FONDO,
                 fg=AZUL if self.es_admin else GRIS).pack(side="right", padx=8)

        tarjeta = tk.Frame(cuerpo, bg=BLANCO, highlightbackground="#dbe1ea", highlightthickness=1)
        tarjeta.pack(fill="both", expand=True)
        tabla_frame = tk.Frame(tarjeta, bg=BLANCO)
        tabla_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tabla_frame, show="headings", selectmode="browse")
        scroll_y = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tabla_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        tabla_frame.rowconfigure(0, weight=1)
        tabla_frame.columnconfigure(0, weight=1)

        self.pie = tk.Label(cuerpo, text="", bg=FONDO, fg=GRIS, font=("Segoe UI", 9))
        self.pie.pack(anchor="w", pady=(10, 0))

        self.botones = tk.Frame(cuerpo, bg=FONDO)
        self.botones.pack(fill="x", pady=(14, 0))
        if self.es_admin:
            ttk.Button(self.botones, text="+ Crear usuario", style="Primary.TButton",
                       command=self.crear).pack(side="left", padx=(0, 8))
            ttk.Button(self.botones, text="Modificar", style="Secondary.TButton",
                       command=self.modificar).pack(side="left", padx=4)
            ttk.Button(self.botones, text="Cambiar rol", style="Secondary.TButton",
                       command=self.abrir_cambiar_rol).pack(side="left", padx=4)
            ttk.Button(self.botones, text="Eliminar", style="Danger.TButton",
                       command=self.eliminar).pack(side="left", padx=4)

    def cargar_usuarios(self):
        try:
            self.registros, admin_real = self.dao.listar_usuarios(self.usuario["id"])
            if self.es_admin != admin_real:
                messagebox.showwarning("Sesión", "Tus permisos cambiaron. Inicia sesión nuevamente.", parent=self)
                self.cerrar_ventana()
                return
            self.es_admin = admin_real
            self._configurar_columnas()
            self.aplicar_filtro()
        except Exception as exc:
            messagebox.showerror("Error al cargar usuarios", str(exc), parent=self)

    def _configurar_columnas(self):
        if self.es_admin:
            self.columnas = [
                "id", "username", "email", "nombre", "apellido", "fecha_nacimiento",
                "rol", "estado_cuenta", "rfc", "telefono", "tarjeta_credito",
                "fecha_registro", "ultimo_acceso", "intentos_fallidos"
            ]
            titulos = {
                "id": "ID", "username": "Usuario", "email": "Correo", "nombre": "Nombre",
                "apellido": "Apellido", "fecha_nacimiento": "Nacimiento", "rol": "Rol",
                "estado_cuenta": "Estado", "rfc": "RFC (descifrado)",
                "telefono": "Teléfono (descifrado)", "tarjeta_credito": "Tarjeta (descifrada)",
                "fecha_registro": "Registro", "ultimo_acceso": "Último acceso",
                "intentos_fallidos": "Intentos fallidos"
            }
        else:
            self.columnas = [
                "id", "username", "email", "nombre", "apellido", "fecha_nacimiento",
                "rol", "estado_cuenta", "fecha_registro", "ultimo_acceso"
            ]
            titulos = {
                "id": "ID", "username": "Usuario", "email": "Correo", "nombre": "Nombre",
                "apellido": "Apellido", "fecha_nacimiento": "Nacimiento", "rol": "Rol",
                "estado_cuenta": "Estado", "fecha_registro": "Registro", "ultimo_acceso": "Último acceso"
            }
        self.tree.configure(columns=self.columnas)
        anchos = {
            "id": 55, "username": 120, "email": 190, "nombre": 120, "apellido": 120,
            "fecha_nacimiento": 105, "rol": 105, "estado_cuenta": 95, "rfc": 130,
            "telefono": 130, "tarjeta_credito": 160, "fecha_registro": 145,
            "ultimo_acceso": 145, "intentos_fallidos": 100
        }
        for col in self.columnas:
            self.tree.heading(col, text=titulos.get(col, col))
            self.tree.column(col, width=anchos.get(col, 120), minwidth=70, stretch=False, anchor="w")

    def aplicar_filtro(self):
        if not hasattr(self, "tree"):
            return
        texto = self.buscar_var.get().strip().casefold()
        for item in self.tree.get_children():
            self.tree.delete(item)
        visibles = 0
        for registro in self.registros:
            busqueda = " ".join(str(registro.get(k) or "") for k in ("id", "username", "email", "nombre", "apellido")).casefold()
            if texto and texto not in busqueda:
                continue
            valores = [self._mostrar(registro.get(col)) for col in self.columnas]
            self.tree.insert("", "end", iid=str(registro["id"]), values=valores)
            visibles += 1
        self.pie.configure(text=f"Registros visibles: {visibles}  |  Total: {len(self.registros)}")

    @staticmethod
    def _mostrar(valor):
        if valor is None:
            return "—"
        if hasattr(valor, "strftime"):
            try:
                return valor.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return str(valor)
        texto = str(valor)
        # Evita que un valor nulo o una cadena vacía confundan visualmente la tabla.
        return texto if texto else "—"

    def _id_seleccionado(self) -> int | None:
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un usuario", "Selecciona una fila de la tabla.", parent=self)
            return None
        return int(seleccion[0])

    def crear(self):
        UsuarioDialog(self, actor_id=self.usuario["id"], registro=None, al_guardar=self.cargar_usuarios)

    def modificar(self):
        usuario_id = self._id_seleccionado()
        if usuario_id is None:
            return
        try:
            registro = self.dao.obtener_usuario(self.usuario["id"], usuario_id)
            UsuarioDialog(self, actor_id=self.usuario["id"], registro=registro, al_guardar=self.cargar_usuarios)
        except Exception as exc:
            messagebox.showerror("No se pudo abrir el usuario", str(exc), parent=self)

    def abrir_cambiar_rol(self):
        usuario_id = self._id_seleccionado()
        if usuario_id is None:
            return
        registro = next((r for r in self.registros if int(r["id"]) == usuario_id), None)
        if not registro:
            return
        dialogo = tk.Toplevel(self)
        dialogo.title("Cambiar rol")
        dialogo.geometry("380x210")
        dialogo.resizable(False, False)
        dialogo.configure(bg=BLANCO)
        dialogo.transient(self)
        dialogo.grab_set()
        tk.Label(dialogo, text=f"Cambiar rol de {registro.get('username')}",
                 font=("Segoe UI", 12, "bold"), bg=BLANCO, fg=TEXTO).pack(pady=(24, 12))
        rol_var = tk.StringVar(value=registro.get("rol") or "cliente")
        combo = ttk.Combobox(dialogo, textvariable=rol_var, state="readonly",
                             values=["administrador", "cliente"], width=25)
        combo.pack(pady=5)

        def guardar_rol():
            if not messagebox.askyesno("Confirmar", "¿Guardar el nuevo rol?", parent=dialogo):
                return
            try:
                self.dao.cambiar_rol(self.usuario["id"], usuario_id, rol_var.get())
                dialogo.destroy()
                self.cargar_usuarios()
            except Exception as exc:
                messagebox.showerror("No se pudo cambiar el rol", str(exc), parent=dialogo)

        ttk.Button(dialogo, text="Guardar rol", style="Primary.TButton", command=guardar_rol).pack(pady=18)

    def eliminar(self):
        usuario_id = self._id_seleccionado()
        if usuario_id is None:
            return
        if not messagebox.askyesno("Confirmar eliminación",
                                   f"¿Seguro que deseas eliminar el usuario con ID {usuario_id}?",
                                   parent=self):
            return
        try:
            self.dao.eliminar_usuario(self.usuario["id"], usuario_id)
            self.cargar_usuarios()
        except Exception as exc:
            messagebox.showerror("No se pudo eliminar", str(exc), parent=self)

    def cerrar_ventana(self):
        self.destroy()
        self.on_logout()


class AdministradorWindow(UsuariosWindow):
    modo_administrador = True


class UsuarioNormalWindow(UsuariosWindow):
    modo_administrador = False


class UsuarioDialog(tk.Toplevel):
    def __init__(self, master: UsuariosWindow, actor_id: int,
                 registro: dict[str, Any] | None, al_guardar: Callable[[], None]):
        super().__init__(master)
        self.actor_id = actor_id
        self.dao = master.dao
        self.registro = registro
        self.al_guardar = al_guardar
        self.es_nuevo = registro is None
        self.variables: dict[str, tk.StringVar] = {}
        self.entradas: dict[str, ttk.Entry] = {}

        self.title("Crear usuario" if self.es_nuevo else "Modificar usuario")
        self.geometry("620x720")
        self.minsize(570, 600)
        self.configure(bg=BLANCO)
        self.transient(master)
        self.grab_set()
        self._construir()

    def _construir(self):
        tk.Label(self, text="Crear usuario" if self.es_nuevo else "Modificar usuario",
                 font=("Segoe UI", 19, "bold"), bg=BLANCO, fg=TEXTO).pack(anchor="w", padx=25, pady=(20, 2))
        texto = "Completa los datos requeridos." if self.es_nuevo else "Actualiza los campos y guarda los cambios."
        tk.Label(self, text=texto, font=("Segoe UI", 10), bg=BLANCO, fg=GRIS).pack(anchor="w", padx=25, pady=(0, 12))

        contenedor = tk.Frame(self, bg=BLANCO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        canvas = tk.Canvas(contenedor, bg=BLANCO, highlightthickness=0)
        scroll = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg=BLANCO)
        id_canvas = canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(id_canvas, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        campos = [
            ("username", "Nombre de usuario *"), ("email", "Correo electrónico *"),
            ("nombre", "Nombre *"), ("apellido", "Apellido *"),
            ("fecha_nacimiento", "Fecha nacimiento (AAAA-MM-DD, opcional)"),
            ("rfc", "RFC *"), ("telefono", "Teléfono (opcional)"),
            ("tarjeta_credito", "Tarjeta (opcional; usa datos de prueba)"),
        ]
        for fila, (clave, etiqueta) in enumerate(campos):
            tk.Label(form, text=etiqueta, font=("Segoe UI", 10, "bold"),
                     bg=BLANCO, fg="#374151").grid(row=fila, column=0, sticky="w", padx=(5, 14), pady=7)
            valor = "" if self.registro is None else self.registro.get(clave)
            if valor is None:
                valor = ""
            var = tk.StringVar(value=str(valor))
            entrada = ttk.Entry(form, textvariable=var, width=37)
            entrada.grid(row=fila, column=1, sticky="ew", padx=(0, 5), pady=7, ipady=3)
            self.variables[clave] = var
            self.entradas[clave] = entrada

        fila = len(campos)
        for clave, etiqueta, opciones, defecto in [
            ("rol", "Rol *", ["administrador", "cliente"], "cliente"),
            ("estado_cuenta", "Estado de cuenta *", ["activo", "inactivo"], "activo"),
        ]:
            tk.Label(form, text=etiqueta, font=("Segoe UI", 10, "bold"),
                     bg=BLANCO, fg="#374151").grid(row=fila, column=0, sticky="w", padx=(5, 14), pady=7)
            valor = defecto if self.registro is None else (self.registro.get(clave) or defecto)
            var = tk.StringVar(value=str(valor))
            combo = ttk.Combobox(form, textvariable=var, values=opciones, state="readonly", width=34)
            combo.grid(row=fila, column=1, sticky="ew", padx=(0, 5), pady=7, ipady=3)
            self.variables[clave] = var
            fila += 1

        password_label = "Contraseña *" if self.es_nuevo else "Nueva contraseña (dejar vacía para conservarla)"
        for clave, etiqueta in [("password", password_label), ("confirmar_password", "Confirmar contraseña *" if self.es_nuevo else "Confirmar nueva contraseña")]:
            tk.Label(form, text=etiqueta, font=("Segoe UI", 10, "bold"),
                     bg=BLANCO, fg="#374151").grid(row=fila, column=0, sticky="w", padx=(5, 14), pady=7)
            var = tk.StringVar()
            entrada = ttk.Entry(form, textvariable=var, show="•", width=37)
            entrada.grid(row=fila, column=1, sticky="ew", padx=(0, 5), pady=7, ipady=3)
            self.variables[clave] = var
            self.entradas[clave] = entrada
            fila += 1

        tk.Label(form, text="La contraseña se guarda como hash PBKDF2-SHA256; RFC, teléfono y tarjeta se cifran con AES_ENCRYPT.",
                 font=("Segoe UI", 9), wraplength=500, justify="left", bg=BLANCO, fg=GRIS).grid(
                     row=fila, column=0, columnspan=2, sticky="w", padx=5, pady=(12, 8))
        form.columnconfigure(1, weight=1)

        botones = tk.Frame(self, bg=BLANCO)
        botones.pack(fill="x", padx=25, pady=(4, 20))
        ttk.Button(botones, text="Cancelar", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botones, text="Guardar", style="Primary.TButton", command=self.guardar).pack(side="right")

    def guardar(self):
        datos = {k: var.get().strip() for k, var in self.variables.items()}
        requeridos = ["username", "email", "nombre", "apellido", "rfc"]
        for clave in requeridos:
            if not datos.get(clave):
                messagebox.showwarning("Validación", f"El campo {clave} es obligatorio.", parent=self)
                self.entradas[clave].focus_set()
                return

        limites = {"username": 50, "email": 100, "nombre": 50, "apellido": 50}
        for clave, limite in limites.items():
            if len(datos[clave]) > limite:
                messagebox.showwarning("Validación", f"{clave} admite hasta {limite} caracteres.", parent=self)
                self.entradas[clave].focus_set()
                return

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", datos["email"]):
            messagebox.showwarning("Validación", "Escribe un correo electrónico válido.", parent=self)
            self.entradas["email"].focus_set()
            return
        if len(datos["rfc"]) not in (12, 13):
            messagebox.showwarning("Validación", "El RFC debe tener 12 o 13 caracteres.", parent=self)
            self.entradas["rfc"].focus_set()
            return
        if datos["telefono"] and not re.fullmatch(r"[0-9+() -]{7,20}", datos["telefono"]):
            messagebox.showwarning("Validación", "Revisa el formato del teléfono.", parent=self)
            self.entradas["telefono"].focus_set()
            return
        if datos["tarjeta_credito"] and not re.fullmatch(r"[0-9 -]{13,25}", datos["tarjeta_credito"]):
            messagebox.showwarning("Validación", "La tarjeta de prueba debe contener entre 13 y 19 dígitos (se permiten espacios o guiones).", parent=self)
            self.entradas["tarjeta_credito"].focus_set()
            return

        nacimiento = datos.get("fecha_nacimiento", "")
        if nacimiento:
            try:
                date.fromisoformat(nacimiento)
            except ValueError:
                messagebox.showwarning("Validación", "La fecha debe usar el formato AAAA-MM-DD.", parent=self)
                self.entradas["fecha_nacimiento"].focus_set()
                return

        password = datos.get("password", "")
        confirmacion = datos.get("confirmar_password", "")
        if self.es_nuevo and len(password) < 8:
            messagebox.showwarning("Validación", "La contraseña debe tener al menos 8 caracteres.", parent=self)
            return
        if password or confirmacion:
            if len(password) < 8:
                messagebox.showwarning("Validación", "La nueva contraseña debe tener al menos 8 caracteres.", parent=self)
                return
            if password != confirmacion:
                messagebox.showwarning("Validación", "Las contraseñas no coinciden.", parent=self)
                return
        elif self.es_nuevo:
            messagebox.showwarning("Validación", "Escribe una contraseña.", parent=self)
            return

        datos["password"] = password
        datos.pop("confirmar_password", None)
        try:
            if self.es_nuevo:
                self.dao.crear_usuario(self.actor_id, datos)
                mensaje = "El usuario se creó correctamente."
            else:
                self.dao.actualizar_usuario(self.actor_id, int(self.registro["id"]), datos)
                mensaje = "Los datos del usuario se actualizaron correctamente."
            messagebox.showinfo("Operación completada", mensaje, parent=self)
            self.destroy()
            self.al_guardar()
        except Exception as exc:
            messagebox.showerror("No se pudo guardar", str(exc), parent=self)
