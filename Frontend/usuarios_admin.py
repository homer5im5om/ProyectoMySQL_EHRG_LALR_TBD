import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

AZUL = "#2563eb"
BLANCO = "#ffffff"
FONDO = "#eef2f7"


class VentanaAdministrador(tk.Toplevel):
    def __init__(self, master, dao, usuario, cerrar_sesion):
        super().__init__(master)
        self.dao = dao
        self.usuario = usuario
        self.cerrar_sesion = cerrar_sesion
        self.usuarios = []
        self.title("Administración de usuarios")
        self.geometry("1250x650")
        self.configure(bg=FONDO)
        self.protocol("WM_DELETE_WINDOW", self.salir)
        self.crear_interfaz()
        self.cargar_usuarios()

    def crear_interfaz(self):
        encabezado = tk.Frame(self, bg=AZUL, padx=18, pady=15)
        encabezado.pack(fill="x")
        tk.Label(encabezado, text="Administración de usuarios", font=("Arial", 18, "bold"),
                 bg=AZUL, fg=BLANCO).pack(side="left")
        tk.Label(encabezado, text="Administrador: " + self.usuario["username"],
                 font=("Arial", 10), bg=AZUL, fg=BLANCO).pack(side="left", padx=20)
        tk.Button(encabezado, text="Cerrar sesión", command=self.salir).pack(side="right")

        botones = tk.Frame(self, bg=FONDO, padx=15, pady=12)
        botones.pack(fill="x")
        tk.Button(botones, text="Crear usuario", command=self.crear_usuario).pack(side="left", padx=4)
        tk.Button(botones, text="Modificar", command=self.modificar_usuario).pack(side="left", padx=4)
        tk.Button(botones, text="Cambiar rol", command=self.cambiar_rol).pack(side="left", padx=4)
        tk.Button(botones, text="Eliminar", command=self.eliminar_usuario).pack(side="left", padx=4)
        tk.Button(botones, text="Actualizar", command=self.cargar_usuarios).pack(side="right", padx=4)

        columnas = ("id", "username", "email", "nombre", "apellido", "fecha_nacimiento",
                    "rol", "estado_cuenta", "rfc", "telefono", "tarjeta_credito",
                    "fecha_registro", "ultimo_acceso", "intentos_fallidos")
        nombres = ("ID", "Usuario", "Correo", "Nombre", "Apellido", "Nacimiento", "Rol",
                   "Estado", "RFC", "Teléfono", "Tarjeta", "Registro", "Último acceso", "Intentos")
        tabla_frame = tk.Frame(self, bg=BLANCO, padx=12, pady=12)
        tabla_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings")
        for columna, nombre in zip(columnas, nombres):
            self.tabla.heading(columna, text=nombre)
            self.tabla.column(columna, width=105, minwidth=80)
        scroll_y = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tabla.yview)
        scroll_x = ttk.Scrollbar(tabla_frame, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        tabla_frame.rowconfigure(0, weight=1)
        tabla_frame.columnconfigure(0, weight=1)

    def cargar_usuarios(self):
        try:
            filas = self.dao.obtener_usuarios("administrador")
            if filas is None:
                messagebox.showerror("Error", "No se pudieron consultar los usuarios. Revisa la terminal.", parent=self)
                return
            self.usuarios = filas
            for item in self.tabla.get_children():
                self.tabla.delete(item)
            for fila in filas:
                valores = [fila.get(campo, "") or "" for campo in self.tabla["columns"]]
                self.tabla.insert("", "end", values=valores)
        except Exception as error:
            messagebox.showerror("Error", str(error), parent=self)

    def usuario_seleccionado(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Selecciona un usuario", "Selecciona una fila de la tabla.", parent=self)
            return None
        usuario_id = int(self.tabla.item(seleccionado[0], "values")[0])
        for usuario in self.usuarios:
            if int(usuario["id"]) == usuario_id:
                return usuario
        return None

    def crear_usuario(self):
        FormularioUsuario(self, self.dao, None, self.cargar_usuarios)

    def modificar_usuario(self):
        usuario = self.usuario_seleccionado()
        if usuario:
            FormularioUsuario(self, self.dao, usuario, self.cargar_usuarios)

    def cambiar_rol(self):
        usuario = self.usuario_seleccionado()
        if not usuario:
            return
        rol = simpledialog.askstring("Cambiar rol", "Escribe administrador o cliente:", parent=self)
        if rol is None:
            return
        rol = rol.strip().lower()
        if rol not in ("administrador", "cliente"):
            messagebox.showwarning("Rol inválido", "Escribe administrador o cliente.", parent=self)
            return
        try:
            self.dao.modificar_usuario(
                usuario["id"], usuario["username"], usuario["email"], usuario["nombre"],
                usuario["apellido"], rol, usuario.get("estado_cuenta") or "activo",
                usuario.get("rfc") or "", usuario.get("telefono") or "",
                usuario.get("tarjeta_credito") or "",
            )
            self.cargar_usuarios()
            nuevo = next((u for u in self.usuarios if int(u["id"]) == int(usuario["id"])), None)
            if nuevo and nuevo.get("rol") == rol:
                messagebox.showinfo("Rol actualizado", "Se cambió el rol del usuario.", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo confirmar el cambio. Revisa la terminal.", parent=self)
        except Exception as error:
            messagebox.showerror("Error", str(error), parent=self)

    def eliminar_usuario(self):
        usuario = self.usuario_seleccionado()
        if not usuario:
            return
        if int(usuario["id"]) == int(self.usuario["id"]):
            messagebox.showwarning("Acción no permitida", "No elimines la cuenta con la que iniciaste sesión.", parent=self)
            return
        if not messagebox.askyesno("Confirmar", "¿Quieres eliminar este usuario?", parent=self):
            return
        try:
            self.dao.eliminar_usuario(usuario["id"])
            self.cargar_usuarios()
            if not any(int(u["id"]) == int(usuario["id"]) for u in self.usuarios):
                messagebox.showinfo("Usuario eliminado", "El usuario ya no aparece en la tabla.", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo confirmar la eliminación. Revisa la terminal.", parent=self)
        except Exception as error:
            messagebox.showerror("Error", str(error), parent=self)

    def salir(self):
        self.destroy()
        self.cerrar_sesion()


class FormularioUsuario(tk.Toplevel):
    def __init__(self, master, dao, usuario, actualizar_tabla):
        super().__init__(master)
        self.dao = dao
        self.usuario = usuario
        self.actualizar_tabla = actualizar_tabla
        self.campos = {}
        self.title("Crear usuario" if usuario is None else "Modificar usuario")
        self.configure(bg=BLANCO)
        self.resizable(False, False)
        self.crear_interfaz()
        self.grab_set()

    def crear_interfaz(self):
        formulario = tk.Frame(self, bg=BLANCO, padx=22, pady=18)
        formulario.pack(fill="both", expand=True)
        campos = [("username", "Usuario"), ("email", "Correo"), ("nombre", "Nombre"),
                  ("apellido", "Apellido")]
        if self.usuario is None:
            campos.append(("fecha_nacimiento", "Nacimiento AAAA-MM-DD"))
        campos.append(("rfc", "RFC"))
        campos.append(("telefono", "Teléfono"))
        campos.append(("tarjeta_credito", "Tarjeta de crédito"))
        if self.usuario is None:
            campos.append(("password", "Contraseña"))
        for fila, (campo, etiqueta) in enumerate(campos):
            tk.Label(formulario, text=etiqueta, bg=BLANCO, anchor="w").grid(row=fila, column=0, sticky="w", padx=(0, 12), pady=5)
            valor = "" if self.usuario is None else str(self.usuario.get(campo) or "")
            variable = tk.StringVar(value=valor)
            if campo == "password":
                entrada = tk.Entry(formulario, textvariable=variable, show="*", width=32)
            else:
                entrada = tk.Entry(formulario, textvariable=variable, width=32)
            entrada.grid(row=fila, column=1, sticky="ew", pady=5)
            self.campos[campo] = variable
        fila = len(campos)
        for campo, etiqueta, opciones, defecto in [
            ("rol", "Rol", ("administrador", "cliente"), "cliente")
        ]:
            tk.Label(formulario, text=etiqueta, bg=BLANCO, anchor="w").grid(row=fila, column=0, sticky="w", padx=(0, 12), pady=5)
            valor = defecto if self.usuario is None else self.usuario.get(campo, defecto)
            variable = tk.StringVar(value=str(valor or defecto))
            ttk.Combobox(formulario, textvariable=variable, values=opciones, state="readonly", width=29).grid(row=fila, column=1, sticky="ew", pady=5)
            self.campos[campo] = variable
            fila += 1
        if self.usuario is not None:
            tk.Label(formulario, text="Estado", bg=BLANCO, anchor="w").grid(row=fila, column=0, sticky="w", padx=(0, 12), pady=5)
            variable = tk.StringVar(value=str(self.usuario.get("estado_cuenta") or "activo"))
            ttk.Combobox(formulario, textvariable=variable, values=("activo", "inactivo"), state="readonly", width=29).grid(row=fila, column=1, sticky="ew", pady=5)
            self.campos["estado_cuenta"] = variable
            fila += 1
        tk.Button(formulario, text="Guardar", bg=AZUL, fg=BLANCO, command=self.guardar).grid(row=fila, column=1, sticky="e", pady=(14, 0))

    def guardar(self):
        datos = {campo: variable.get().strip() for campo, variable in self.campos.items()}
        for campo in ("username", "email", "nombre", "apellido", "rfc"):
            if not datos.get(campo):
                messagebox.showwarning("Validación", "Completa el campo " + campo + ".", parent=self)
                return
        if "@" not in datos["email"] or "." not in datos["email"].split("@")[-1]:
            messagebox.showwarning("Validación", "Escribe un correo válido.", parent=self)
            return
        if len(datos["rfc"]) not in (12, 13):
            messagebox.showwarning("Validación", "El RFC debe tener 12 o 13 caracteres.", parent=self)
            return
        if self.usuario is None and len(datos.get("password", "")) < 8:
            messagebox.showwarning("Validación", "La contraseña debe tener al menos 8 caracteres.", parent=self)
            return
        if self.usuario is None:
            fecha = datos.get("fecha_nacimiento", "") or None
            try:
                if fecha:
                    from datetime import date
                    date.fromisoformat(fecha)
            except ValueError:
                messagebox.showwarning("Validación", "La fecha debe tener el formato AAAA-MM-DD.", parent=self)
                return
            antes = self.dao.obtener_usuarios("administrador") or []
            if any(u.get("username") == datos["username"] or u.get("email") == datos["email"] for u in antes):
                messagebox.showwarning("Usuario duplicado", "El usuario o correo ya existe.", parent=self)
                return
            self.dao.registrar_usuario(
                datos["username"], datos["email"], datos["password"], datos["nombre"],
                datos["apellido"], fecha, datos["rol"], datos["rfc"],
                datos.get("telefono", ""), datos.get("tarjeta_credito", ""),
            )
            despues = self.dao.obtener_usuarios("administrador") or []
            guardado = any(u.get("username") == datos["username"] for u in despues)
        else:
            self.dao.modificar_usuario(
                self.usuario["id"], datos["username"], datos["email"], datos["nombre"],
                datos["apellido"], datos["rol"], datos["estado_cuenta"], datos["rfc"],
                datos.get("telefono", ""), datos.get("tarjeta_credito", ""),
            )
            despues = self.dao.obtener_usuarios("administrador") or []
            guardado = any(int(u["id"]) == int(self.usuario["id"]) and u.get("username") == datos["username"] for u in despues)
        self.actualizar_tabla()
        if guardado:
            messagebox.showinfo("Correcto", "Los datos se guardaron.", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo confirmar el cambio. Revisa los mensajes de la terminal.", parent=self)
