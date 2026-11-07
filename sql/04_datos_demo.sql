/* =====================================================================
   Sistema de Registro de Colaboradores - Fundación Beit Shalom
   Script 04 (opcional): datos de demostración para el panel administrativo

   Todas las personas son ficticias y usan correos @example.com (dominio
   reservado para ejemplos). Se puede ejecutar varias veces: no duplica.
   Ejecutar con:  flask --app app cargar-demo

   Para borrar estos datos de demostración, ejecuta en SSMS:
       DELETE h FROM HistorialEstados h INNER JOIN Colaboradores c ON c.id = h.colaborador_id WHERE c.correo LIKE '%@example.com';
       DELETE ca FROM ColaboradorAreas ca INNER JOIN Colaboradores c ON c.id = ca.colaborador_id WHERE c.correo LIKE '%@example.com';
       DELETE FROM Colaboradores WHERE correo LIKE '%@example.com';
   ===================================================================== */

USE BeitShalomDB;
GO

DECLARE @Demo TABLE (
    correo VARCHAR(150) PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    pais VARCHAR(80) NOT NULL,
    telefono VARCHAR(30) NULL,
    modalidad VARCHAR(30) NOT NULL,
    disponibilidad VARCHAR(100) NOT NULL,
    motivacion VARCHAR(1000) NULL,
    estado VARCHAR(20) NOT NULL,
    dias INT NOT NULL,              -- hace cuántos días se registró
    areas VARCHAR(400) NOT NULL,    -- nombres de las áreas separados por |
    comentario VARCHAR(500) NULL    -- motivo de la evaluación
);

INSERT INTO @Demo VALUES
('ana.martinez@example.com', 'Ana Sofía Martínez', 'El Salvador', '+503 7012 3456', 'Presencial', 'Fines de semana',
 'Soy maestra y me encantaría apoyar en actividades educativas y recreativas con los niños.', 'Aprobado', 140,
 'Voluntariado presencial|Apoyo educativo|Organización de actividades', 'Perfil adecuado para el programa de refuerzo escolar.'),
('carlos.hernandez@example.com', 'Carlos Eduardo Hernández', 'El Salvador', '+503 7845 1290', 'Ambas', 'Horarios flexibles',
 'Soy contador y puedo apoyar con la administración y los informes financieros.', 'En revisión', 120,
 'Apoyo profesional o técnico|Apoyo administrativo', 'Se agendó una entrevista.'),
('maria.rivas@example.com', 'María José Rivas', 'Guatemala', '+502 5521 8890', 'Virtual', 'Entre semana',
 'Trabajo en marketing digital y quiero ayudar a difundir el trabajo de la Fundación.', 'Pendiente', 95,
 'Comunicación y difusión', NULL),
('jose.perez@example.com', 'José Antonio Pérez', 'Honduras', NULL, 'Presencial', 'Ocasional',
 'Quiero ayudar en las colectas de víveres de fin de año.', 'Rechazado', 100,
 'Voluntariado presencial|Donaciones y gestión de recursos', 'Por ahora no hay actividades presenciales en su zona.'),
('gabriela.flores@example.com', 'Gabriela Alejandra Flores', 'El Salvador', '+503 6011 7788', 'Presencial', 'Fines de semana',
 'Me gusta organizar eventos y quiero que los niños vivan experiencias bonitas.', 'Aprobado', 80,
 'Voluntariado presencial|Organización de actividades', 'Apoyará en la jornada recreativa de diciembre.'),
('luis.gomez@example.com', 'Luis Fernando Gómez', 'México', '+52 55 1234 5678', 'Virtual', 'Horarios flexibles',
 'Soy diseñador gráfico y puedo apoyar con material visual para campañas.', 'Pendiente', 60,
 'Apoyo profesional o técnico|Comunicación y difusión', NULL),
('daniela.castillo@example.com', 'Daniela Beatriz Castillo', 'El Salvador', '+503 7777 2020', 'Ambas', 'Entre semana',
 'Estudio psicología y deseo apoyar con talleres de refuerzo escolar.', 'En revisión', 45,
 'Apoyo educativo', 'Pendiente de confirmar horarios.'),
('roberto.molina@example.com', 'Roberto Carlos Molina', 'Costa Rica', '+506 8888 1212', 'Virtual', 'Ocasional',
 'Puedo apoyar contactando empresas para conseguir donaciones.', 'Pendiente', 30,
 'Donaciones y gestión de recursos', NULL),
('karla.ramirez@example.com', 'Karla Patricia Ramírez', 'El Salvador', '+503 7123 9876', 'Presencial', 'Fines de semana',
 'Tengo experiencia como voluntaria en otras fundaciones y quiero sumar mi tiempo.', 'Aprobado', 25,
 'Voluntariado presencial|Apoyo educativo|Apoyo administrativo', 'Experiencia comprobada en voluntariado.'),
('diego.torres@example.com', 'Diego Alejandro Torres', 'Colombia', NULL, 'Virtual', 'Horarios flexibles',
 'Quiero aportar ideas y contenido para las redes sociales.', 'Pendiente', 18,
 'Comunicación y difusión|Otro tipo de colaboración', NULL),
('sofia.lopez@example.com', 'Sofía Valentina López', 'El Salvador', '+503 6123 4567', 'Ambas', 'Fines de semana',
 'Me gustaría enseñar música a los niños.', 'Pendiente', 12,
 'Apoyo educativo|Organización de actividades', NULL),
('miguel.rodriguez@example.com', 'Miguel Ángel Rodríguez', 'Estados Unidos', '+1 202 555 0147', 'Virtual', 'Ocasional',
 'Vivo en el extranjero y quiero apoyar con donaciones periódicas.', 'En revisión', 9,
 'Donaciones y gestión de recursos', 'Se le enviará información sobre donaciones.'),
('fernanda.cruz@example.com', 'Fernanda Isabel Cruz', 'Nicaragua', '+505 8765 4321', 'Virtual', 'Entre semana',
 'Soy abogada y puedo asesorar a la Fundación en temas legales.', 'Pendiente', 6,
 'Apoyo profesional o técnico|Apoyo administrativo', NULL),
('andres.morales@example.com', 'Andrés Felipe Morales', 'El Salvador', '+503 7654 3210', 'Presencial', 'Entre semana',
 'Quiero dedicar parte de mi tiempo a los niños de la Fundación.', 'Pendiente', 3,
 'Voluntariado presencial', NULL),
('valeria.aguilar@example.com', 'Valeria Monserrat Aguilar', 'España', NULL, 'Virtual', 'Horarios flexibles',
 'Escribo contenido y puedo apoyar con el boletín informativo.', 'Pendiente', 1,
 'Comunicación y difusión|Otro tipo de colaboración', NULL),
('javier.mejia@example.com', 'Javier Ernesto Mejía', 'El Salvador', '+503 7000 1111', 'Ambas', 'Ocasional',
 'Puedo ayudar con la logística de eventos.', 'Rechazado', 50,
 'Organización de actividades', 'La información de contacto no pudo verificarse.');

-- 1. Colaboradores (solo los que aún no existen)
INSERT INTO Colaboradores (nombre_completo, pais, correo, telefono, modalidad, disponibilidad,
                           motivacion, acepta_privacidad, fecha_registro, estado)
SELECT d.nombre, d.pais, d.correo, d.telefono, d.modalidad, d.disponibilidad,
       d.motivacion, 1, DATEADD(DAY, -d.dias, SYSDATETIME()), d.estado
FROM @Demo d
WHERE NOT EXISTS (SELECT 1 FROM Colaboradores c WHERE c.correo = d.correo);

-- 2. Áreas de cada colaborador (relación muchos a muchos)
INSERT INTO ColaboradorAreas (colaborador_id, area_id)
SELECT c.id, a.id
FROM @Demo d
INNER JOIN Colaboradores c ON c.correo = d.correo
CROSS APPLY STRING_SPLIT(d.areas, '|') s
INNER JOIN AreasColaboracion a ON a.nombre = s.value
WHERE NOT EXISTS (
    SELECT 1 FROM ColaboradorAreas ca WHERE ca.colaborador_id = c.id AND ca.area_id = a.id
);

-- 3. Historial de las solicitudes ya evaluadas
INSERT INTO HistorialEstados (colaborador_id, estado_anterior, estado_nuevo, comentario, usuario_id, fecha)
SELECT c.id, 'Pendiente', d.estado, d.comentario, NULL, DATEADD(DAY, -d.dias + 3, SYSDATETIME())
FROM @Demo d
INNER JOIN Colaboradores c ON c.correo = d.correo
WHERE d.estado <> 'Pendiente'
  AND NOT EXISTS (SELECT 1 FROM HistorialEstados h WHERE h.colaborador_id = c.id);
GO
