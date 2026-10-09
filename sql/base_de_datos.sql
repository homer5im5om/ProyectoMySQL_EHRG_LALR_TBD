create database proyecto_tbd;
use proyecto_tbd;

CREATE TABLE usuarios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    fecha_nacimiento DATE NULL,
    rol VARCHAR(20) DEFAULT 'cliente',
    estado_cuenta VARCHAR(20) DEFAULT 'activo',
    rfc_enc VARBINARY(255) NOT NULL,
    telefono_enc VARBINARY(255) NULL,
    tarjeta_credito_enc VARBINARY(255) NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso DATETIME NULL,
    intentos_fallidos TINYINT DEFAULT 0
);