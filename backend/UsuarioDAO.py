import os
from Conexion import Conexion
from dotenv import load_dotenv

load_dotenv()

class UsuarioDAO:
    def __init__(self):
        self.db = Conexion()
        self.aes_key = os.getenv('AES_KEY')

    def registrar_usuario(self, username, email, password, nombre, apellido, fecha_nacimiento, rol, rfc, telefono,tarjeta_credito):
        conexion = self.db.conectar()
        if conexion:
            try:
                cursor = conexion.cursor()

                sql = """
                    insert into usuarios ( username, email, password_hash, nombre, apellido, fecha_nacimiento, rol, rfc_enc, telefono_enc,tarjeta_credito_enc)
                    values( %s, %s, SHA2(%s,256) , %s, %s, %s, %s, AES_ENCRYPT(%s,%s),AES_ENCRYPT(%s,%s), AES_ENCRYPT(%s,%s))
                """

                valores = (
                    username,
                    email,
                    password,
                    nombre,
                    apellido,
                    fecha_nacimiento,
                    rol,
                    rfc, self.aes_key,
                    telefono, self.aes_key,
                    tarjeta_credito, self.aes_key,
                )

                cursor.execute(sql, valores)
                conexion.commit()

                print(f"Usuario {username} registrado con exito")

            except Exception as e:
                print(e)
            finally:
                cursor.close()
                self.db.desconectar()

if __name__ == '__main__':
    dao = UsuarioDAO()
    dao.registrar_usuario(username="edu_admin",
        email="edu@correo.com",
        password="password123",
        nombre="Edu Humberto",
        apellido="Rosiles",
        fecha_nacimiento="2005-07-04",
        rol="administrador",
        rfc="ROGE050704XXX",
        telefono="4451234567",
        tarjeta_credito="4152313456789012")


