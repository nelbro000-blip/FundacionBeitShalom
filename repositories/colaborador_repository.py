"""Repositorio de colaboradores: todas las consultas SQL del sistema de registro.

El controlador nunca escribe SQL; solo llama a los métodos de esta clase.
Todas las consultas son parametrizadas: los valores viajan por separado
(marcadores ?) y nunca se concatenan al texto SQL, lo que evita la
inyección SQL.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from math import ceil

from models.area import AreaColaboracion
from models.colaborador import Colaborador
from models.errores import ReglaNegocioError
from repositories.base_repository import BaseRepository, ResultadoPaginado

MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


@dataclass
class FiltrosBusqueda:
    """Criterios del listado administrativo: búsqueda y filtros."""

    texto: str = ""
    pais: str = ""
    area_id: int | None = None
    estado: str = ""

    @classmethod
    def desde_argumentos(cls, argumentos: Mapping) -> FiltrosBusqueda:
        """Crea los filtros desde la URL (?q=...&pais=...) descartando valores no válidos."""
        texto = " ".join(str(argumentos.get("q", "")).split())[:100]
        pais = str(argumentos.get("pais", "")).strip()[:80]
        estado = str(argumentos.get("estado", "")).strip()
        if estado not in Colaborador.ESTADOS:
            estado = ""
        try:
            area_id = int(argumentos.get("area", "") or 0)
        except (TypeError, ValueError):
            area_id = 0
        return cls(texto=texto, pais=pais, area_id=area_id if area_id > 0 else None, estado=estado)

    @property
    def activos(self) -> bool:
        return bool(self.texto or self.pais or self.area_id or self.estado)

    def como_parametros(self) -> dict:
        """Parámetros para reconstruir la URL (paginación y exportación)."""
        parametros: dict = {}
        if self.texto:
            parametros["q"] = self.texto
        if self.pais:
            parametros["pais"] = self.pais
        if self.area_id:
            parametros["area"] = self.area_id
        if self.estado:
            parametros["estado"] = self.estado
        return parametros


@dataclass
class CambioEstado:
    """Un registro de la tabla HistorialEstados."""

    fecha: datetime
    estado_anterior: str
    estado_nuevo: str
    comentario: str
    usuario: str


@dataclass
class Estadisticas:
    """Datos que muestra el dashboard."""

    total: int = 0
    ultimos_7_dias: int = 0
    por_estado: dict[str, int] = field(default_factory=dict)
    por_area: list[tuple[str, int]] = field(default_factory=list)
    por_pais: list[tuple[str, int]] = field(default_factory=list)
    por_modalidad: list[tuple[str, int]] = field(default_factory=list)
    por_disponibilidad: list[tuple[str, int]] = field(default_factory=list)
    por_mes: list[tuple[str, int]] = field(default_factory=list)
    recientes: list[Colaborador] = field(default_factory=list)


class ColaboradorRepository(BaseRepository):
    """Guarda y consulta colaboradores en SQL Server."""

    RESTRICCIONES_UNICAS = {
        "UQ_Colaboradores_Correo": "Ya existe una solicitud registrada con este correo electrónico.",
    }

    _COLUMNAS = (
        "c.id, c.nombre_completo, c.pais, c.correo, c.telefono, c.modalidad, "
        "c.disponibilidad, c.motivacion, c.acepta_privacidad, c.fecha_registro, c.estado"
    )
    # Áreas de cada colaborador unidas con '|' en una sola columna (SQL Server 2017+)
    _AREAS_AGRUPADAS = (
        "(SELECT STRING_AGG(a.nombre, '|') WITHIN GROUP (ORDER BY a.id) "
        "FROM ColaboradorAreas ca INNER JOIN AreasColaboracion a ON a.id = ca.area_id "
        "WHERE ca.colaborador_id = c.id) AS areas"
    )
    LIMITE_EXPORTACION = 10000
    MESES_GRAFICO = 6

    # ------------------------------------------------------------------
    # Áreas de colaboración
    # ------------------------------------------------------------------
    def obtener_areas_activas(self) -> list[AreaColaboracion]:
        filas = self._consultar_todos(
            "SELECT id, nombre, activa FROM AreasColaboracion WHERE activa = 1 ORDER BY id"
        )
        return [AreaColaboracion(fila.id, fila.nombre, bool(fila.activa)) for fila in filas]

    def obtener_areas(self) -> list[AreaColaboracion]:
        filas = self._consultar_todos("SELECT id, nombre, activa FROM AreasColaboracion ORDER BY id")
        return [AreaColaboracion(fila.id, fila.nombre, bool(fila.activa)) for fila in filas]

    # ------------------------------------------------------------------
    # Registro público
    # ------------------------------------------------------------------
    def existe_correo(self, correo: str) -> bool:
        total = self._consultar_valor(
            "SELECT COUNT(1) FROM Colaboradores WHERE correo = ?", (correo.strip().lower(),)
        )
        return bool(total)

    def guardar(self, colaborador: Colaborador) -> int:
        """Guarda el colaborador y sus áreas como una sola transacción.

        Si falla cualquiera de las inserciones, SQL Server revierte todo y no
        queda un registro guardado a medias.
        """
        if not colaborador.areas:
            raise ReglaNegocioError("El colaborador debe tener al menos un área de colaboración.")

        with self._cursor() as cursor:
            nuevo_id = cursor.execute(
                """
                INSERT INTO Colaboradores (
                    nombre_completo, pais, correo, telefono, modalidad,
                    disponibilidad, motivacion, acepta_privacidad, fecha_registro
                )
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    colaborador.nombre,
                    colaborador.pais,
                    colaborador.correo,
                    colaborador.telefono or None,
                    colaborador.modalidad,
                    colaborador.disponibilidad,
                    colaborador.motivacion or None,
                    colaborador.acepta_privacidad,
                    self._ahora(),
                ),
            ).fetchval()

            cursor.executemany(
                "INSERT INTO ColaboradorAreas (colaborador_id, area_id) VALUES (?, ?)",
                [(nuevo_id, id_area) for id_area in colaborador.areas],
            )

        colaborador.id = nuevo_id
        return nuevo_id

    # ------------------------------------------------------------------
    # Consultas del panel administrativo
    # ------------------------------------------------------------------
    def obtener_por_id(self, id_colaborador: int) -> Colaborador | None:
        with self._cursor() as cursor:
            fila = cursor.execute(
                f"SELECT {self._COLUMNAS} FROM Colaboradores c WHERE c.id = ?", (id_colaborador,)
            ).fetchone()
            if fila is None:
                return None
            areas = cursor.execute(
                """
                SELECT a.id, a.nombre
                FROM ColaboradorAreas ca
                INNER JOIN AreasColaboracion a ON a.id = ca.area_id
                WHERE ca.colaborador_id = ?
                ORDER BY a.id
                """,
                (id_colaborador,),
            ).fetchall()
        return self._crear_colaborador(
            fila, areas=[area.id for area in areas], nombres_areas=[area.nombre for area in areas]
        )

    def buscar(self, filtros: FiltrosBusqueda, pagina: int = 1, por_pagina: int = 15) -> ResultadoPaginado:
        """Listado con búsqueda, filtros y paginación."""
        condicion, parametros = self._condiciones(filtros)
        with self._cursor() as cursor:
            total = self._ejecutar(
                cursor, f"SELECT COUNT(*) FROM Colaboradores c {condicion}", parametros
            ).fetchval()
            pagina = min(max(1, pagina), max(1, ceil(total / por_pagina)))
            filas = self._ejecutar(
                cursor,
                f"""
                SELECT {self._COLUMNAS}, {self._AREAS_AGRUPADAS}
                FROM Colaboradores c
                {condicion}
                ORDER BY c.fecha_registro DESC, c.id DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """,
                [*parametros, (pagina - 1) * por_pagina, por_pagina],
            ).fetchall()
        colaboradores = [
            self._crear_colaborador(fila, nombres_areas=self._separar(fila.areas)) for fila in filas
        ]
        return ResultadoPaginado(colaboradores, total, pagina, por_pagina)

    def listar(self, filtros: FiltrosBusqueda) -> list[Colaborador]:
        """Todos los colaboradores que cumplen los filtros (para exportar a Excel)."""
        condicion, parametros = self._condiciones(filtros)
        filas = self._consultar_todos(
            f"""
            SELECT TOP ({self.LIMITE_EXPORTACION}) {self._COLUMNAS}, {self._AREAS_AGRUPADAS}
            FROM Colaboradores c
            {condicion}
            ORDER BY c.fecha_registro DESC, c.id DESC
            """,
            parametros,
        )
        return [self._crear_colaborador(fila, nombres_areas=self._separar(fila.areas)) for fila in filas]

    def paises_registrados(self) -> list[str]:
        filas = self._consultar_todos("SELECT DISTINCT pais FROM Colaboradores ORDER BY pais")
        return [fila.pais for fila in filas]

    def obtener_historial(self, id_colaborador: int) -> list[CambioEstado]:
        filas = self._consultar_todos(
            """
            SELECT h.fecha, h.estado_anterior, h.estado_nuevo, h.comentario,
                   u.nombre_completo AS usuario
            FROM HistorialEstados h
            LEFT JOIN Usuarios u ON u.id = h.usuario_id
            WHERE h.colaborador_id = ?
            ORDER BY h.fecha DESC, h.id DESC
            """,
            (id_colaborador,),
        )
        return [
            CambioEstado(fila.fecha, fila.estado_anterior, fila.estado_nuevo,
                         fila.comentario or "", fila.usuario or "Sistema")
            for fila in filas
        ]

    def actualizar_estado(
        self, colaborador: Colaborador, estado_anterior: str, usuario_id: int | None, comentario: str = ""
    ) -> None:
        """Guarda el nuevo estado y su registro en el historial (una transacción)."""
        with self._cursor() as cursor:
            actualizados = cursor.execute(
                "UPDATE Colaboradores SET estado = ? WHERE id = ? AND estado = ?",
                (colaborador.estado, colaborador.id, estado_anterior),
            ).rowcount
            if actualizados != 1:
                # Otra persona cambió el estado mientras tanto: se revierte todo
                raise ReglaNegocioError(
                    "Otra persona modificó esta solicitud. Recarga la página e inténtalo de nuevo."
                )
            cursor.execute(
                """
                INSERT INTO HistorialEstados
                    (colaborador_id, estado_anterior, estado_nuevo, comentario, usuario_id, fecha)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (colaborador.id, estado_anterior, colaborador.estado, comentario or None, usuario_id, self._ahora()),
            )

    def eliminar(self, id_colaborador: int) -> bool:
        """Elimina todos los datos de una persona (derecho de supresión)."""
        with self._cursor() as cursor:
            cursor.execute("DELETE FROM HistorialEstados WHERE colaborador_id = ?", (id_colaborador,))
            cursor.execute("DELETE FROM ColaboradorAreas WHERE colaborador_id = ?", (id_colaborador,))
            return cursor.execute("DELETE FROM Colaboradores WHERE id = ?", (id_colaborador,)).rowcount == 1

    def eliminar_rechazados_antes_de(self, fecha_limite: datetime) -> int:
        """Política de conservación: borra solicitudes rechazadas registradas antes de la fecha."""
        seleccion = "SELECT id FROM Colaboradores WHERE estado = ? AND fecha_registro < ?"
        parametros = (Colaborador.ESTADO_RECHAZADO, fecha_limite)
        with self._cursor() as cursor:
            cursor.execute(f"DELETE FROM HistorialEstados WHERE colaborador_id IN ({seleccion})", parametros)
            cursor.execute(f"DELETE FROM ColaboradorAreas WHERE colaborador_id IN ({seleccion})", parametros)
            return cursor.execute(
                "DELETE FROM Colaboradores WHERE estado = ? AND fecha_registro < ?", parametros
            ).rowcount

    def obtener_estadisticas(self) -> Estadisticas:
        """Totales y distribuciones para el dashboard."""
        estadisticas = Estadisticas()
        meses = self._ultimos_meses(self.MESES_GRAFICO)
        inicio = datetime(meses[0][0], meses[0][1], 1)

        with self._cursor() as cursor:
            estadisticas.total = cursor.execute("SELECT COUNT(*) FROM Colaboradores").fetchval()
            estadisticas.ultimos_7_dias = cursor.execute(
                "SELECT COUNT(*) FROM Colaboradores WHERE fecha_registro >= ?",
                (self._ahora() - timedelta(days=7),),
            ).fetchval()

            por_estado = self._conteo(cursor, "SELECT estado, COUNT(*) FROM Colaboradores GROUP BY estado")
            estadisticas.por_estado = {estado: por_estado.get(estado, 0) for estado in Colaborador.ESTADOS}

            estadisticas.por_area = [
                (fila[0], fila[1])
                for fila in cursor.execute(
                    """
                    SELECT a.nombre, COUNT(ca.colaborador_id) AS total
                    FROM AreasColaboracion a
                    LEFT JOIN ColaboradorAreas ca ON ca.area_id = a.id
                    GROUP BY a.id, a.nombre
                    ORDER BY total DESC, a.id
                    """
                ).fetchall()
            ]
            estadisticas.por_pais = [
                (fila[0], fila[1])
                for fila in cursor.execute(
                    "SELECT TOP 8 pais, COUNT(*) AS total FROM Colaboradores "
                    "GROUP BY pais ORDER BY total DESC, pais"
                ).fetchall()
            ]

            por_modalidad = self._conteo(cursor, "SELECT modalidad, COUNT(*) FROM Colaboradores GROUP BY modalidad")
            estadisticas.por_modalidad = self._ordenar(Colaborador.MODALIDADES, por_modalidad)

            por_disponibilidad = self._conteo(
                cursor, "SELECT disponibilidad, COUNT(*) FROM Colaboradores GROUP BY disponibilidad"
            )
            estadisticas.por_disponibilidad = self._ordenar(Colaborador.DISPONIBILIDADES, por_disponibilidad)

            filas_mes = cursor.execute(
                """
                SELECT YEAR(fecha_registro), MONTH(fecha_registro), COUNT(*)
                FROM Colaboradores
                WHERE fecha_registro >= ?
                GROUP BY YEAR(fecha_registro), MONTH(fecha_registro)
                """,
                (inicio,),
            ).fetchall()
            conteo_mes = {(fila[0], fila[1]): fila[2] for fila in filas_mes}
            estadisticas.por_mes = [
                (f"{MESES[mes - 1]} {anio}", conteo_mes.get((anio, mes), 0)) for anio, mes in meses
            ]

            recientes = cursor.execute(
                f"SELECT TOP 5 {self._COLUMNAS} FROM Colaboradores c ORDER BY c.fecha_registro DESC, c.id DESC"
            ).fetchall()
            estadisticas.recientes = [self._crear_colaborador(fila) for fila in recientes]

        return estadisticas

    # ------------------------------------------------------------------
    # Métodos auxiliares (privados)
    # ------------------------------------------------------------------
    @staticmethod
    def _condiciones(filtros: FiltrosBusqueda) -> tuple[str, list]:
        """Construye el WHERE con marcadores ?; los valores van aparte en la lista."""
        condiciones: list[str] = []
        parametros: list = []
        if filtros.texto:
            patron = f"%{ColaboradorRepository._escapar_like(filtros.texto)}%"
            # CI_AI: la búsqueda ignora mayúsculas y tildes (maria = María)
            condiciones.append(
                "(c.nombre_completo COLLATE Latin1_General_CI_AI LIKE ? ESCAPE '\\' "
                "OR c.correo LIKE ? ESCAPE '\\')"
            )
            parametros += [patron, patron]
        if filtros.pais:
            condiciones.append("c.pais = ?")
            parametros.append(filtros.pais)
        if filtros.estado:
            condiciones.append("c.estado = ?")
            parametros.append(filtros.estado)
        if filtros.area_id:
            condiciones.append(
                "EXISTS (SELECT 1 FROM ColaboradorAreas x "
                "WHERE x.colaborador_id = c.id AND x.area_id = ?)"
            )
            parametros.append(filtros.area_id)
        condicion = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        return condicion, parametros

    @staticmethod
    def _escapar_like(texto: str) -> str:
        """Evita que %, _ o [ escritos por el usuario actúen como comodines de LIKE."""
        for caracter in ("\\", "%", "_", "["):
            texto = texto.replace(caracter, "\\" + caracter)
        return texto

    @staticmethod
    def _conteo(cursor, sql: str) -> dict:
        return {fila[0]: fila[1] for fila in cursor.execute(sql).fetchall()}

    @staticmethod
    def _ordenar(opciones: tuple, conteo: dict) -> list[tuple[str, int]]:
        """Todas las opciones (también las que tienen 0), de mayor a menor."""
        return sorted(((opcion, conteo.get(opcion, 0)) for opcion in opciones), key=lambda par: -par[1])

    @staticmethod
    def _separar(texto: str | None) -> list[str]:
        return texto.split("|") if texto else []

    @staticmethod
    def _ultimos_meses(cantidad: int) -> list[tuple[int, int]]:
        """Lista de (año, mes) de los últimos meses, del más antiguo al actual."""
        hoy = date.today()
        anio, mes = hoy.year, hoy.month
        meses = []
        for _ in range(cantidad):
            meses.append((anio, mes))
            anio, mes = (anio - 1, 12) if mes == 1 else (anio, mes - 1)
        return list(reversed(meses))

    @staticmethod
    def _crear_colaborador(fila, areas=None, nombres_areas=None) -> Colaborador:
        """Convierte una fila de SQL Server en un objeto Colaborador."""
        return Colaborador(
            nombre=fila.nombre_completo,
            pais=fila.pais,
            correo=fila.correo,
            telefono=fila.telefono or "",
            modalidad=fila.modalidad,
            disponibilidad=fila.disponibilidad,
            motivacion=fila.motivacion or "",
            areas=areas or [],
            acepta_privacidad=bool(fila.acepta_privacidad),
            id_colaborador=fila.id,
            estado=fila.estado,
            fecha_registro=fila.fecha_registro,
            nombres_areas=nombres_areas or [],
        )
