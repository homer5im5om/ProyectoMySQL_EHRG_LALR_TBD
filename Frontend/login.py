import os
import sys
import tkinter as tk
from tkinter import messagebox

carpeta = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, carpeta)
sys.path.insert(0, os.path.join(carpeta, "backend"))

from backend.UsuarioDAO import UsuarioDAO
from frontend.usuarios_admin import VentanaAdministrador
from frontend.usuarios_usuario import VentanaUsuario


class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Iniciar sesión")
        self.geometry("330x230")
        self.resizable(False, False)
        self.configure(bg="white")
        self.dao = UsuarioDAO()

        tk.Label(self, text="Iniciar sesión", font=("Arial", 16, "bold"),
                 bg="white", fg="#2563eb").pack(pady=(15, 10))

        tk.Label(self, text="Usuario", bg="white").pack()
        self.usuario = tk.Entry(self, width=30)
        self.usuario.pack(pady=(3, 8))

        tk.Label(self, text="Contraseña", bg="white").pack()
        self.contrasena = tk.Entry(self, width=30, show="*")
        self.contrasena.pack(pady=(3, 12))

        tk.Button(self, text="Iniciar sesión", bg="#2563eb", fg="white",
                  command=self.iniciar_sesion).pack()

        self.usuario.bind("<Return>", lambda evento: self.contrasena.focus_set())
        self.contrasena.bind("<Return>", lambda evento: self.iniciar_sesion())
        self.usuario.focus_set()

    def iniciar_sesion(self):
        username = self.usuario.get().strip()
        password = self.contrasena.get()

        if not username or not password:
            messagebox.showwarning("Aviso", "Escribe el usuario y la contraseña.", parent=self)
            return

        try:
            datos = self.dao.autenticar_usuario(username, password)

            if not datos:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos.", parent=self)
                self.contrasena.delete(0, tk.END)
                return

            estado = str(datos.get("estado_cuenta") or "activo").lower()
            if estado != "activo":
                messagebox.showerror("Error", "La cuenta está inactiva.", parent=self)
                self.contrasena.delete(0, tk.END)
                return

            rol = str(datos.get("rol") or "cliente").lower()
            self.withdraw()

            if rol in ("admin", "administrador"):
                VentanaAdministrador(self, self.dao, datos, self.volver)
            else:
                VentanaUsuario(self, self.dao, datos, self.volver)

        except Exception as error:
            messagebox.showerror("Error", str(error), parent=self)

    def volver(self):
        self.contrasena.delete(0, tk.END)
        self.deiconify()
        self.usuario.focus_set()


if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()
