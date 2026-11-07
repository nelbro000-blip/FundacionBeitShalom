/* =====================================================================
   Sistema de Registro de Colaboradores - Fundación Beit Shalom
   Script 02: tablas del módulo administrativo (sección 16 de la guía)

   - Usuarios: personal autorizado. La contraseña se guarda como hash,
     nunca en texto plano.
   - HistorialEstados: registra quién aprobó o rechazó cada solicitud,
     cuándo y por qué motivo.
   - Índices para que las búsquedas y filtros del panel sean rápidos.
   - MensajesContacto: mensajes de la página de contacto del sitio.

   Requiere haber ejecutado antes 01_crear_base_datos.sql
   ===================================================================== */

USE BeitShalomDB;
GO

IF OBJECT_ID(N'dbo.Usuarios', N'U') IS NULL
BEGIN
    CREATE TABLE Usuarios (
        id INT IDENTITY(1,1) PRIMARY KEY,
        usuario VARCHAR(50) NOT NULL,
        nombre_completo VARCHAR(150) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        rol VARCHAR(20) NOT NULL DEFAULT 'Consulta',
        activo BIT NOT NULL DEFAULT 1,
        fecha_creacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        ultimo_acceso DATETIME2 NULL,

        CONSTRAINT UQ_Usuarios_Usuario
            UNIQUE (usuario),

        -- Administrador: consulta y evalúa solicitudes.
        -- Consulta: solo puede ver la información y exportar reportes.
        CONSTRAINT CK_Usuarios_Rol
            CHECK (rol IN ('Administrador', 'Consulta'))
    );
END
GO

IF OBJECT_ID(N'dbo.HistorialEstados', N'U') IS NULL
BEGIN
    CREATE TABLE HistorialEstados (
        id INT IDENTITY(1,1) PRIMARY KEY,
        colaborador_id INT NOT NULL,
        estado_anterior VARCHAR(20) NOT NULL,
        estado_nuevo VARCHAR(20) NOT NULL,
        comentario VARCHAR(500) NULL,
        usuario_id INT NULL,
        fecha DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

        CONSTRAINT FK_HistorialEstados_Colaborador
            FOREIGN KEY (colaborador_id)
            REFERENCES Colaboradores(id),

        CONSTRAINT FK_HistorialEstados_Usuario
            FOREIGN KEY (usuario_id)
            REFERENCES Usuarios(id),

        CONSTRAINT CK_HistorialEstados_Estado
            CHECK (estado_nuevo IN (
                'Pendiente',
                'En revisión',
                'Aprobado',
                'Rechazado'
            ))
    );
END
GO

/* Índices de apoyo para el listado, los filtros y el dashboard */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ColaboradorAreas_Area')
    CREATE INDEX IX_ColaboradorAreas_Area ON ColaboradorAreas (area_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Colaboradores_Estado')
    CREATE INDEX IX_Colaboradores_Estado ON Colaboradores (estado);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Colaboradores_FechaRegistro')
    CREATE INDEX IX_Colaboradores_FechaRegistro ON Colaboradores (fecha_registro DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_HistorialEstados_Colaborador')
    CREATE INDEX IX_HistorialEstados_Colaborador ON HistorialEstados (colaborador_id);
GO

/* ---------------------------------------------------------------------
   MensajesContacto: mensajes enviados desde la página de contacto del
   sitio. El personal los lee desde el panel administrativo.
   --------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.MensajesContacto', N'U') IS NULL
BEGIN
    CREATE TABLE MensajesContacto (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        correo VARCHAR(150) NOT NULL,
        telefono VARCHAR(30) NULL,
        asunto VARCHAR(30) NOT NULL,
        mensaje VARCHAR(2000) NOT NULL,
        fecha DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        leido BIT NOT NULL DEFAULT 0,

        CONSTRAINT CK_MensajesContacto_Asunto
            CHECK (asunto IN ('informacion', 'voluntariado', 'donacion', 'inscripcion', 'otro'))
    );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_MensajesContacto_Fecha')
    CREATE INDEX IX_MensajesContacto_Fecha ON MensajesContacto (fecha DESC);
GO
