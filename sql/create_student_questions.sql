-- Script: create_student_questions.sql
-- Propósito: Crear base de datos y tablas para almacenar las preguntas del alumno
-- Diseñado para Microsoft SQL Server

-- 1) Crear la base de datos si no existe
IF DB_ID(N'HackatonCallCenterDB') IS NULL
BEGIN
    CREATE DATABASE HackatonCallCenterDB;
END
GO

USE HackatonCallCenterDB;
GO

-- 2) Tabla: Students (opcional para identificar alumnos)
IF OBJECT_ID('dbo.Students','U') IS NULL
BEGIN
    CREATE TABLE dbo.Students (
        StudentId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ExternalStudentId NVARCHAR(100) NULL, -- id desde la app/sesión (si aplica)
        Name NVARCHAR(200) NULL,
        CreatedAt DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

-- 3) Tabla: Sessions (opcional para agrupar preguntas por sesión)
IF OBJECT_ID('dbo.Sessions','U') IS NULL
BEGIN
    CREATE TABLE dbo.Sessions (
        SessionId UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        StudentId BIGINT NULL,
        StartedAt DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),
        EndedAt DATETIMEOFFSET(7) NULL,
        Source NVARCHAR(50) NULL, -- ej. 'desktop', 'web', 'telefono'
        CONSTRAINT FK_Sessions_Students FOREIGN KEY (StudentId) REFERENCES dbo.Students(StudentId)
    );
END
GO

-- 4) Tabla: Questions (almacena lo que pregunta el alumno)
IF OBJECT_ID('dbo.Questions','U') IS NULL
BEGIN
    CREATE TABLE dbo.Questions (
        QuestionId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        SessionId UNIQUEIDENTIFIER NULL,
        StudentId BIGINT NULL,
        QuestionText NVARCHAR(MAX) NOT NULL,
        QuestionNormalized NVARCHAR(1000) NULL, -- versión corta/normalizada para búsquedas rápidas
        QuestionLanguage NVARCHAR(10) NULL DEFAULT 'es',
        IsSchoolRelated BIT NULL DEFAULT 1, -- booleana evaluada por la IA
        Metadata NVARCHAR(MAX) NULL, -- JSON con metadatos (device, mic settings, raw payload, etc.)
        ReceivedBy NVARCHAR(100) NULL, -- componente que recibió la pregunta (ej. 'alumno_escolar.py')
        CreatedAt DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_Questions_Sessions FOREIGN KEY (SessionId) REFERENCES dbo.Sessions(SessionId),
        CONSTRAINT FK_Questions_Students FOREIGN KEY (StudentId) REFERENCES dbo.Students(StudentId)
    );
END
GO

-- 5) Tabla: Answers (respuestas generadas por la profesora/IA)
IF OBJECT_ID('dbo.Answers','U') IS NULL
BEGIN
    CREATE TABLE dbo.Answers (
        AnswerId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        QuestionId BIGINT NOT NULL,
        Responder NVARCHAR(200) NULL, -- ej. 'Profesora García', 'groq:llama-3.3-70b'
        AnswerText NVARCHAR(MAX) NOT NULL,
        Confidence FLOAT NULL,
        Metadata NVARCHAR(MAX) NULL,
        CreatedAt DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_Answers_Questions FOREIGN KEY (QuestionId) REFERENCES dbo.Questions(QuestionId)
    );
END
GO

-- 6) Tabla: QuestionEvaluations (ej. 'correcta', 'incorrecta', 'no_respondio')
IF OBJECT_ID('dbo.QuestionEvaluations','U') IS NULL
BEGIN
    CREATE TABLE dbo.QuestionEvaluations (
        EvalId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        QuestionId BIGINT NOT NULL,
        Evaluator NVARCHAR(100) NULL, -- ej. 'AlumnoExigente', 'automated_script'
        Evaluation NVARCHAR(50) NOT NULL, -- ej. 'correcta','incorrecta','no_respondio'
        Notes NVARCHAR(MAX) NULL,
        CreatedAt DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_QE_Questions FOREIGN KEY (QuestionId) REFERENCES dbo.Questions(QuestionId)
    );
END
GO

-- 7) Índices recomendados
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Questions_CreatedAt' AND object_id = OBJECT_ID('dbo.Questions'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_Questions_CreatedAt ON dbo.Questions(CreatedAt);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Questions_StudentId' AND object_id = OBJECT_ID('dbo.Questions'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_Questions_StudentId ON dbo.Questions(StudentId);
END
GO

-- 8) (Opcional) Full-Text Search para contenido en QuestionText
-- Nota: la búsqueda full-text requiere que el servicio de Full-Text esté instalado y que el usuario tenga permisos apropiados.
-- Si desea habilitarla, ejecute los siguientes comandos (descomentar si procede):

/*
IF NOT EXISTS(SELECT * FROM sys.fulltext_catalogs WHERE name = 'FTCatalog_Questions')
BEGIN
    CREATE FULLTEXT CATALOG FTCatalog_Questions AS DEFAULT;
END
GO

-- Asegúrese de que exista un índice único (PRIMARY KEY crea uno). Aquí usamos la PK como clave.
-- Crear índice full-text sobre QuestionText (solo si Full-Text está instalado)
IF NOT EXISTS (SELECT 1 FROM sys.fulltext_indexes fi JOIN sys.objects o ON fi.object_id = o.object_id WHERE o.name = 'Questions')
BEGIN
    CREATE FULLTEXT INDEX ON dbo.Questions(QuestionText LANGUAGE 1034) KEY INDEX PK__Questions__ -- REEMPLAZAR CON NOMBRE DEL ÍNDICE PK SI ES NECESARIO
    WITH STOPLIST = SYSTEM;
END
GO
*/

-- 9) Procedimiento almacenado para insertar una pregunta (crea sesión opcionalmente y devuelve QuestionId)
IF OBJECT_ID('dbo.sp_InsertQuestion','P') IS NOT NULL
    DROP PROCEDURE dbo.sp_InsertQuestion;
GO

CREATE PROCEDURE dbo.sp_InsertQuestion
    @StudentId BIGINT = NULL,
    @SessionId UNIQUEIDENTIFIER = NULL,
    @ExternalStudentId NVARCHAR(100) = NULL,
    @QuestionText NVARCHAR(MAX),
    @Language NVARCHAR(10) = 'es',
    @IsSchoolRelated BIT = 1,
    @Metadata NVARCHAR(MAX) = NULL,
    @ReceivedBy NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Now DATETIMEOFFSET(7) = SYSUTCDATETIME();

    -- Si no hay StudentId pero hay ExternalStudentId, intentar usarlo o crearlo
    IF @StudentId IS NULL AND @ExternalStudentId IS NOT NULL
    BEGIN
        SELECT TOP(1) @StudentId = StudentId FROM dbo.Students WHERE ExternalStudentId = @ExternalStudentId;
        IF @StudentId IS NULL
        BEGIN
            INSERT INTO dbo.Students(ExternalStudentId, CreatedAt)
            VALUES(@ExternalStudentId, @Now);
            SET @StudentId = SCOPE_IDENTITY();
        END
    END

    -- Si no hay SessionId, crear una nueva
    IF @SessionId IS NULL
        SET @SessionId = NEWSEQUENTIALID();

    -- Asegurar que la sesión exista
    IF NOT EXISTS (SELECT 1 FROM dbo.Sessions WHERE SessionId = @SessionId)
    BEGIN
        INSERT INTO dbo.Sessions(SessionId, StudentId, StartedAt)
        VALUES(@SessionId, @StudentId, @Now);
    END

    -- Insertar pregunta
    INSERT INTO dbo.Questions(SessionId, StudentId, QuestionText, QuestionLanguage, IsSchoolRelated, Metadata, ReceivedBy, CreatedAt)
    VALUES(@SessionId, @StudentId, @QuestionText, @Language, @IsSchoolRelated, @Metadata, @ReceivedBy, @Now);

    -- Devolver el id insertado
    SELECT CAST(SCOPE_IDENTITY() AS BIGINT) AS QuestionId, @SessionId AS SessionId;
END
GO

-- 10) Ejemplo de uso (INSERT simple)
-- Ejemplo 1: Insertar pregunta sin estudiante conocido
-- EXEC dbo.sp_InsertQuestion @QuestionText = N'¿Cómo se calcula el área de un triángulo?', @ReceivedBy = N'alumno_escolar.py';

-- Ejemplo 2: Insertar pregunta con ExternalStudentId
-- EXEC dbo.sp_InsertQuestion @ExternalStudentId = N'user123', @QuestionText = N'¿Qué es la fotosíntesis?', @ReceivedBy = N'alumno_escolar.py';

-- Ejemplo 3: Insertar y obtener QuestionId manualmente
-- DECLARE @qid TABLE (QuestionId BIGINT, SessionId UNIQUEIDENTIFIER);
-- INSERT INTO @qid EXEC dbo.sp_InsertQuestion @QuestionText = N'¿Qué son los números primos?';
-- SELECT * FROM @qid;

-- FIN DEL SCRIPT
