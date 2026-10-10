CREATE DATABASE IF NOT EXISTS proyecto_tbd;
USE proyecto_tbd;

CREATE TABLE IF NOT EXISTS usuarios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    fecha_nacimiento DATE NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'cliente',
    estado_cuenta VARCHAR(20) NOT NULL DEFAULT 'activo',
    rfc VARBINARY(255) NOT NULL,
    telefono VARBINARY(255) NULL,
    tarjeta_credito VARBINARY(255) NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso DATETIME NULL,
    intentos_fallidos TINYINT UNSIGNED DEFAULT 0
);
