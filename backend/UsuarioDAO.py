import os
from threading import currentThread

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

    def obtener_usuarios(self, rol_solicitante):
        conexion = self.db.conectar()

        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                if rol_solicitante == 'administrador':
                    sql = """   
                        select id,username,email,password_hash,nombre,apellido,fecha_nacimiento,rol,estado_cuenta,CAST(AES_DECRYPT(rfc_enc, %s)as CHAR) as rfc, CAST(AES_DECRYPT(telefono_enc, %s)as CHAR) as telefono, CAST(AES_DECRYPT(tarjeta_credito_enc, %s)as CHAR) as tarjeta_credito, fecha_registro, ultimo_acceso, intentos_fallidos from usuarios;
                    """
                    values = (
                        self.aes_key,self.aes_key,self.aes_key
                    )
                    cursor.execute(sql, values)
                else:
                    sql = """   
                            SELECT id, username, email, password_hash, nombre, apellido, fecha_nacimiento, rol, estado_cuenta, 
                            '********' as rfc, 
                            '********' as telefono, 
                            '********' as tarjeta_credito, 
                            fecha_registro, ultimo_acceso, intentos_fallidos 
                            FROM usuarios;
                        """
                    cursor.execute(sql)
                resultado = cursor.fetchall()
                if resultado:
                    return resultado
                else:
                    print("No hay usuarios registrados")
                    return []
            except Exception as e:
                print(e)
            finally:
                cursor.close()
                self.db.desconectar()

    def eliminar_usuario(self, id):
        conexion = self.db.conectar()
        if conexion:
            try:
                cursor = conexion.cursor()
                sql = """
                delete from usuarios where id = %s
                    """
                cursor.execute(sql, (id,))
                conexion.commit()
            except Exception as e:
                print(e)
            finally:
                cursor.close()
                self.db.desconectar()

    def modificar_usuario(self,id, username, email, nombre, apellido, rol,estado_cuenta, rfc, telefono, tarjeta_credito):
        conexion = self.db.conectar()
        if conexion:
            try:
                cursor = conexion.cursor()
                sql = """
                    update usuarios
                    set username = %s,
                        email = %s, 
                        nombre = %s,
                        apellido = %s, 
                        rol = %s,
                        estado_cuenta = %s,
                        rfc_enc = AES_ENCRYPT(%s, %s),
                        telefono_enc = AES_ENCRYPT(%s, %s),
                        tarjeta_credito_enc = AES_ENCRYPT(%s, %s)
                        where id = %s
                """
                values = (username,
                          email,
                          nombre,
                          apellido,
                          rol,
                          estado_cuenta,
                          rfc, self.aes_key,
                          telefono, self.aes_key,
                          tarjeta_credito, self.aes_key,
                          id)
                cursor.execute(sql, values)
                conexion.commit()
            except Exception as e:
                print(e)
            finally:
                cursor.close()
                self.db.desconectar()

    def autenticar_usuario(self, username, password):
        conexion = self.db.conectar()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                sql = """
                    select * from usuarios where username = %s
                    and password_hash = SHA2(%s,256)
                """
                valores = (username, password)
                cursor.execute(sql, valores)

                resultado = cursor.fetchone()
                if resultado:
                    print(f"Usuario {username} autenticado con exito")
                else:
                    print(f"Usuario {username} incorrecto")

                return resultado
            except Exception as e:
                print(e)
            finally:
                cursor.close()
                self.db.desconectar()


if __name__ == '__main__':
    dao = UsuarioDAO()
    """
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
    """

    dao.autenticar_usuario("edu_admin","password123")

