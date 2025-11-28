create database talkia;
use talkia;

-- ============================================================================
-- 1) TABLA: alumnos
-- ============================================================================

CREATE TABLE IF NOT EXISTS alumnos (
    alumno_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NULL,
    external_id VARCHAR(100) NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2) TABLA: sesiones_llamada
-- ============================================================================

CREATE TABLE IF NOT EXISTS sesiones_llamada (
    sesion_id CHAR(36) NOT NULL PRIMARY KEY,
    alumno_id BIGINT NULL,
    maestro_id INT NULL,
    iniciada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizada_en TIMESTAMP NULL,
    contexto_inicial LONGTEXT NULL,

    CONSTRAINT fk_sesiones_alumnos FOREIGN KEY (alumno_id)
        REFERENCES alumnos(alumno_id)
);

-- ============================================================================
-- 3) TABLA: turnos_conversacion
-- ============================================================================

CREATE TABLE IF NOT EXISTS turnos_conversacion (
    turno_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    sesion_id CHAR(36) NOT NULL,

    rol_emisor VARCHAR(50) NOT NULL,
    transcripcion LONGTEXT NOT NULL,
    tema VARCHAR(100) NULL,

    duracion_audio DOUBLE NULL,
    modelo_ia_usado VARCHAR(100) NULL,
    tokenes_consumidos INT NULL,
    fecha_turno TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_turnos_sesion FOREIGN KEY (sesion_id)
        REFERENCES sesiones_llamada(sesion_id)
);

-- ============================================================================
-- 4) TABLA: evaluaciones
-- ============================================================================

CREATE TABLE IF NOT EXISTS evaluaciones (
    evaluacion_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    turno_id BIGINT NOT NULL,
    evaluador VARCHAR(100) NULL,
    puntuacion INT NULL,
    comentario LONGTEXT NULL,
    fecha_evaluacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_evaluaciones_turnos FOREIGN KEY (turno_id)
        REFERENCES turnos_conversacion(turno_id)
);

-- ============================================================================
-- 5) ÍNDICES
-- ============================================================================

CREATE INDEX ix_turnos_sesion_id 
    ON turnos_conversacion (sesion_id);

CREATE INDEX ix_turnos_fecha_turno 
    ON turnos_conversacion (fecha_turno);

-- ============================================================================
-- 6) PROCEDIMIENTO almacenado
-- ============================================================================

DELIMITER $$

CREATE PROCEDURE sp_insertar_turno(
    IN p_sesion_id CHAR(36),
    IN p_rol_emisor VARCHAR(50),
    IN p_transcripcion LONGTEXT,
    IN p_tema VARCHAR(100)
)
BEGIN
    -- Crear sesión si no existe
    IF NOT EXISTS (SELECT 1 FROM sesiones_llamada WHERE sesion_id = p_sesion_id) THEN
        INSERT INTO sesiones_llamada (sesion_id)
        VALUES (p_sesion_id);
    END IF;

    -- Insertar turno
    INSERT INTO turnos_conversacion(
        sesion_id, rol_emisor, transcripcion, tema
    ) VALUES (
        p_sesion_id, p_rol_emisor, p_transcripcion, p_tema
    );

    SELECT LAST_INSERT_ID() AS turno_id;
END $$

DELIMITER ;

-- ============================================================================
-- EJEMPLO DE USO (MySQL)
-- ============================================================================
/*
SET @nueva_sesion = UUID();

CALL sp_insertar_turno(
    @nueva_sesion,
    'Alumno',
    'Profesora, ¿me explica cómo funcionan las fracciones?',
    NULL
);

CALL sp_insertar_turno(
    @nueva_sesion,
    'Profesora',
    'Claro, una fracción es una parte de un todo.',
    NULL
);
*/
