import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

class Conexion:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.conexion = None

    def conectar(self):
        try:
            if self.conexion is None or not self.conexion.is_connected():
                self.conexion = mysql.connector.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                print("Conexion exitosa")
            return self.conexion
        except Error as e:
            print(e)
            return None

    def desconectar(self):
        try:
            if self.conexion is not None and self.conexion.is_connected():
                self.conexion.close()
                print("Conexion cerrada")
        except Error as e:
            print(e)
