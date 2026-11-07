/* =====================================================================
   Sistema de Registro de Colaboradores - Fundación Beit Shalom
   Script 03: consultas para comprobar el sistema (sección 19 de la guía)

   Ejecutar en SSMS después de enviar solicitudes desde el formulario.
   No modifica datos: solo consulta.
   ===================================================================== */

USE BeitShalomDB;
GO

/* Prueba "Consultar la base de datos" -> visualizar el colaborador */
SELECT id, nombre_completo, pais, correo, telefono, modalidad,
       disponibilidad, estado, fecha_registro
FROM Colaboradores
ORDER BY fecha_registro DESC;

/* Prueba "Consultar sus áreas" -> mostrar todas las áreas seleccionadas
   (una fila por cada relación colaborador-área) */
SELECT c.id, c.nombre_completo, a.id AS area_id, a.nombre AS area
FROM Colaboradores c
INNER JOIN ColaboradorAreas ca ON ca.colaborador_id = c.id
INNER JOIN AreasColaboracion a ON a.id = ca.area_id
ORDER BY c.id, a.id;

/* Las mismas áreas agrupadas en una sola fila por colaborador */
SELECT c.id, c.nombre_completo,
       STRING_AGG(a.nombre, ', ') WITHIN GROUP (ORDER BY a.id) AS areas
FROM Colaboradores c
INNER JOIN ColaboradorAreas ca ON ca.colaborador_id = c.id
INNER JOIN AreasColaboracion a ON a.id = ca.area_id
GROUP BY c.id, c.nombre_completo
ORDER BY c.id;

/* Prueba "Simular error SQL" -> no deben existir colaboradores sin áreas.
   Si la transacción se revierte correctamente, esta consulta no devuelve filas. */
SELECT c.id, c.correo
FROM Colaboradores c
WHERE NOT EXISTS (
    SELECT 1 FROM ColaboradorAreas ca WHERE ca.colaborador_id = c.id
);

/* Totales por estado (base del dashboard) */
SELECT estado, COUNT(*) AS total
FROM Colaboradores
GROUP BY estado;

/* Totales por área de colaboración */
SELECT a.nombre, COUNT(ca.colaborador_id) AS total
FROM AreasColaboracion a
LEFT JOIN ColaboradorAreas ca ON ca.area_id = a.id
GROUP BY a.id, a.nombre
ORDER BY total DESC;

/* Historial de evaluaciones (quién cambió cada estado y por qué) */
SELECT h.fecha, c.nombre_completo, h.estado_anterior, h.estado_nuevo,
       h.comentario, u.usuario AS evaluado_por
FROM HistorialEstados h
INNER JOIN Colaboradores c ON c.id = h.colaborador_id
LEFT JOIN Usuarios u ON u.id = h.usuario_id
ORDER BY h.fecha DESC;

/* Usuarios del panel: la contraseña solo existe como hash */
SELECT id, usuario, nombre_completo, rol, activo, fecha_creacion,
       ultimo_acceso, LEFT(password_hash, 20) + '...' AS inicio_del_hash
FROM Usuarios;
