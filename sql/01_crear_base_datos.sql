/* =====================================================================
   Sistema de Registro de Colaboradores - Fundación Beit Shalom
   Script 01: base de datos, tablas del registro público y áreas iniciales
   Motor: SQL Server 2017 o superior

   Se puede ejecutar varias veces: cada objeto se crea solo si no existe.
   Ejecutar en SQL Server Management Studio (SSMS) o con:
       flask --app app crear-bd
   ===================================================================== */

IF DB_ID(N'BeitShalomDB') IS NULL
BEGIN
    CREATE DATABASE BeitShalomDB;
END
GO

USE BeitShalomDB;
GO

/* ---------------------------------------------------------------------
   5.1 Tabla Colaboradores
   Almacena la información personal de cada persona inscrita.
   --------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.Colaboradores', N'U') IS NULL
BEGIN
    CREATE TABLE Colaboradores (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre_completo VARCHAR(150) NOT NULL,
        pais VARCHAR(80) NOT NULL,
        correo VARCHAR(150) NOT NULL,
        telefono VARCHAR(30),
        modalidad VARCHAR(30) NOT NULL,
        disponibilidad VARCHAR(100) NOT NULL,
        motivacion VARCHAR(1000),
        acepta_privacidad BIT NOT NULL,
        fecha_registro DATETIME2 DEFAULT SYSDATETIME(),
        estado VARCHAR(20) DEFAULT 'Pendiente',

        -- Evita registrar dos veces la misma dirección electrónica
        CONSTRAINT UQ_Colaboradores_Correo
            UNIQUE (correo),

        CONSTRAINT CK_Colaboradores_Estado
            CHECK (estado IN (
                'Pendiente',
                'En revisión',
                'Aprobado',
                'Rechazado'
            )),

        -- No se puede guardar una solicitud sin aceptar la política de privacidad
        CONSTRAINT CK_Colaboradores_Privacidad
            CHECK (acepta_privacidad = 1)
    );
END
GO

/* ---------------------------------------------------------------------
   5.2 Tabla AreasColaboracion
   Contiene las diferentes áreas en las que una persona puede participar.
   --------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.AreasColaboracion', N'U') IS NULL
BEGIN
    CREATE TABLE AreasColaboracion (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE,
        activa BIT DEFAULT 1
    );
END
GO

-- Las áreas se insertan una sola vez y en este orden (id 1 al 8)
IF NOT EXISTS (SELECT 1 FROM AreasColaboracion)
BEGIN
    INSERT INTO AreasColaboracion (nombre)
    VALUES
    ('Voluntariado presencial'),
    ('Apoyo profesional o técnico'),
    ('Apoyo educativo'),
    ('Organización de actividades'),
    ('Comunicación y difusión'),
    ('Apoyo administrativo'),
    ('Donaciones y gestión de recursos'),
    ('Otro tipo de colaboración');
END
GO

/* ---------------------------------------------------------------------
   5.3 Tabla ColaboradorAreas
   Relación muchos a muchos: una persona puede seleccionar varias áreas
   y una misma área puede tener muchos colaboradores.
   --------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.ColaboradorAreas', N'U') IS NULL
BEGIN
    CREATE TABLE ColaboradorAreas (
        id INT IDENTITY(1,1) PRIMARY KEY,
        colaborador_id INT NOT NULL,
        area_id INT NOT NULL,

        CONSTRAINT FK_ColaboradorAreas_Colaborador
            FOREIGN KEY (colaborador_id)
            REFERENCES Colaboradores(id),

        CONSTRAINT FK_ColaboradorAreas_Area
            FOREIGN KEY (area_id)
            REFERENCES AreasColaboracion(id),

        CONSTRAINT UQ_Colaborador_Area
            UNIQUE (colaborador_id, area_id)
    );
END
GO
