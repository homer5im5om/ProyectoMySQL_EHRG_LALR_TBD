import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
BACKEND_DIR = PROJECT_ROOT / "backend"
# Hace posible ejecutar `python Frontend/login.py` desde cualquier carpeta.
for carpeta in (SQL_DIR, BACKEND_DIR):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

from UsuarioDAO import UsuarioDAO
from security import es_administrador
from usuarios import AdministradorWindow, UsuarioNormalWindow

AZUL = "#2563eb"
AZUL_OSCURO = "#1d4ed8"
BLANCO = "#ffffff"
FONDO = "#eef2f7"
TEXTO = "#111827"
GRIS = "#6b7280"


class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inicio de sesión | Sistema de usuarios")
        self.geometry("920x590")
        self.minsize(820, 540)
        self.configure(bg=FONDO)
        self.ventana_usuarios = None
        self.dao = UsuarioDAO()
        self._estilos()
        self._construir()

    def _estilos(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("Primary.TButton", font=("Segoe UI", 11, "bold"),
                         foreground=BLANCO, background=AZUL, padding=(14, 10), borderwidth=0)
        estilo.map("Primary.TButton", background=[("active", AZUL_OSCURO)])
        estilo.configure("TEntry", font=("Segoe UI", 11), padding=10)

    def _construir(self):
        contenedor = tk.Frame(self, bg=BLANCO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=20)

        panel_azul = tk.Frame(contenedor, bg=AZUL, width=350)
        panel_azul.pack(side="left", fill="y")
        panel_azul.pack_propagate(False)
        tk.Label(panel_azul, text="US", font=("Segoe UI", 35, "bold"),
                 bg=AZUL_OSCURO, fg=BLANCO, width=3, height=1).pack(pady=(105, 24))
        tk.Label(panel_azul, text="SISTEMA DE\nUSUARIOS", font=("Segoe UI", 22, "bold"),
                 bg=AZUL, fg=BLANCO, justify="center").pack()
        tk.Label(panel_azul, text="Acceso seguro\nAdministración de usuarios",
                 font=("Segoe UI", 11), bg=AZUL, fg="#dbeafe", justify="center").pack(pady=18)
        tk.Label(panel_azul, text="Práctica 3.3 · Python + Azure MySQL",
                 font=("Segoe UI", 9), bg=AZUL, fg="#bfdbfe").pack(side="bottom", pady=24)

        derecha = tk.Frame(contenedor, bg=BLANCO)
        derecha.pack(side="left", fill="both", expand=True)
        formulario = tk.Frame(derecha, bg=BLANCO, width=390)
        formulario.place(relx=0.5, rely=0.5, anchor="center", width=380)

        tk.Label(formulario, text="Bienvenido", font=("Segoe UI", 25, "bold"),
                 bg=BLANCO, fg=TEXTO).pack(anchor="w")
        tk.Label(formulario, text="Inicia sesión para consultar los usuarios.",
                 font=("Segoe UI", 10), bg=BLANCO, fg=GRIS).pack(anchor="w", pady=(5, 26))

        tk.Label(formulario, text="Usuario o correo electrónico", font=("Segoe UI", 10, "bold"),
                 bg=BLANCO, fg="#374151").pack(anchor="w", pady=(0, 7))
        self.entrada_usuario = ttk.Entry(formulario)
        self.entrada_usuario.pack(fill="x", ipady=2)

        tk.Label(formulario, text="Contraseña", font=("Segoe UI", 10, "bold"),
                 bg=BLANCO, fg="#374151").pack(anchor="w", pady=(18, 7))
        fila_password = tk.Frame(formulario, bg=BLANCO)
        fila_password.pack(fill="x")
        self.entrada_password = ttk.Entry(fila_password, show="•")
        self.entrada_password.pack(fill="x", expand=True, ipady=2)

        self.mostrar_var = tk.BooleanVar(value=False)
        tk.Checkbutton(formulario, text="Mostrar contraseña", variable=self.mostrar_var,
                       command=self.alternar_password, font=("Segoe UI", 9), bg=BLANCO,
                       fg=GRIS, activebackground=BLANCO, selectcolor=BLANCO,
                       bd=0).pack(anchor="w", pady=(8, 22))

        ttk.Button(formulario, text="INICIAR SESIÓN", style="Primary.TButton",
                   command=self.iniciar_sesion).pack(fill="x")
        tk.Label(formulario, text="El registro de usuarios se administra desde la cuenta administrador.",
                 font=("Segoe UI", 9), wraplength=350, justify="left",
                 bg=BLANCO, fg=GRIS).pack(anchor="w", pady=(20, 0))

        self.entrada_usuario.bind("<Return>", lambda _e: self.entrada_password.focus_set())
        self.entrada_password.bind("<Return>", lambda _e: self.iniciar_sesion())
        self.entrada_usuario.focus_set()

    def alternar_password(self):
        self.entrada_password.configure(show="" if self.mostrar_var.get() else "•")

    def iniciar_sesion(self):
        identificador = self.entrada_usuario.get().strip()
        password = self.entrada_password.get()
        if not identificador:
            messagebox.showwarning("Validación", "Escribe el usuario o correo.", parent=self)
            self.entrada_usuario.focus_set()
            return
        if not password:
            messagebox.showwarning("Validación", "Escribe la contraseña.", parent=self)
            self.entrada_password.focus_set()
            return
        try:
            usuario = self.dao.autenticar(identificador, password)
            if not usuario:
                messagebox.showerror("Acceso denegado", "Credenciales incorrectas o cuenta inactiva.", parent=self)
                self.entrada_password.delete(0, tk.END)
                self.entrada_password.focus_set()
                return
            self.withdraw()
            ventana = AdministradorWindow if es_administrador(usuario.get("rol")) else UsuarioNormalWindow
            try:
                self.ventana_usuarios = ventana(self, usuario, self.mostrar_login)
            except Exception:
                self.deiconify()
                raise
        except Exception as exc:
            messagebox.showerror(
                "No se pudo iniciar sesión",
                "No fue posible conectar o completar la autenticación.\n\n"
                f"Detalle: {exc}\n\nRevisa el archivo .env, la conexión de Azure y los permisos de red.",
                parent=self,
            )

    def mostrar_login(self):
        self.entrada_password.delete(0, tk.END)
        self.deiconify()
        self.lift()
        self.entrada_usuario.focus_set()

if __name__ == "__main__":
    LoginApp().mainloop()
