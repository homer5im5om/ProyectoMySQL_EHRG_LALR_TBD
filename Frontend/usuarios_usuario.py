import tkinter as tk
from tkinter import messagebox, ttk

AZUL = "#2563eb"
BLANCO = "#ffffff"
FONDO = "#eef2f7"


class VentanaUsuario(tk.Toplevel):
    def __init__(self, master, dao, usuario, cerrar_sesion):
        super().__init__(master)
        self.dao = dao
        self.usuario = usuario
        self.cerrar_sesion = cerrar_sesion
        self.title("Usuarios registrados")
        self.geometry("1000x600")
        self.configure(bg=FONDO)
        self.protocol("WM_DELETE_WINDOW", self.salir)
        self.crear_interfaz()
        self.cargar_usuarios()

    def crear_interfaz(self):
        encabezado = tk.Frame(self, bg=AZUL, padx=20, pady=18)
        encabezado.pack(fill="x")
        tk.Label(encabezado, text="Usuarios registrados", font=("Arial", 18, "bold"),
                 bg=AZUL, fg=BLANCO).pack(side="left")
        tk.Label(encabezado, text="Usuario: " + self.usuario["username"], font=("Arial", 10),
                 bg=AZUL, fg=BLANCO).pack(side="left", padx=20)
        tk.Button(encabezado, text="Cerrar sesión", command=self.salir).pack(side="right")
        tk.Button(encabezado, text="Actualizar", command=self.cargar_usuarios).pack(side="right", padx=8)

        columnas = ("id", "username", "email", "nombre", "apellido", "fecha_nacimiento",
                    "rol", "estado_cuenta", "fecha_registro", "ultimo_acceso")
        nombres = ("ID", "Usuario", "Correo", "Nombre", "Apellido", "Nacimiento",
                   "Rol", "Estado", "Registro", "Último acceso")
        tabla_frame = tk.Frame(self, bg=BLANCO, padx=15, pady=15)
        tabla_frame.pack(fill="both", expand=True, padx=18, pady=18)
        self.tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings")
        for columna, nombre in zip(columnas, nombres):
            self.tabla.heading(columna, text=nombre)
            self.tabla.column(columna, width=110, minwidth=80)
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
            filas = self.dao.obtener_usuarios("cliente")
            for item in self.tabla.get_children():
                self.tabla.delete(item)
            if filas is None:
                messagebox.showerror("Error", "No se pudieron consultar los usuarios. Revisa la terminal.", parent=self)
                return
            for fila in filas:
                valores = [fila.get(campo, "") or "" for campo in self.tabla["columns"]]
                self.tabla.insert("", "end", values=valores)
        except Exception as error:
            messagebox.showerror("Error", str(error), parent=self)

    def salir(self):
        self.destroy()
        self.cerrar_sesion()
