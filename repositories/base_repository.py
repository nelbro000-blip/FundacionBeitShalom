"""Funcionalidad común para todos los repositorios."""
from __future__ import annotations

import logging
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from math import ceil
from typing import Generic, TypeVar

import pyodbc

from database import BaseDatos, ErrorBaseDatos

registro = logging.getLogger(__name__)
T = TypeVar("T")


class RegistroDuplicadoError(Exception):
    """Se intentó guardar un dato que debe ser único (por ejemplo, un correo)."""


@dataclass
class ResultadoPaginado(Generic[T]):
    """Una página de resultados del listado administrativo."""

    elementos: list[T]
    total: int
    pagina: int
    por_pagina: int

    @property
    def paginas(self) -> int:
        return max(1, ceil(self.total / self.por_pagina))

    @property
    def tiene_anterior(self) -> bool:
        return self.pagina > 1

    @property
    def tiene_siguiente(self) -> bool:
        return self.pagina < self.paginas

    @property
    def desde(self) -> int:
        return 0 if self.total == 0 else (self.pagina - 1) * self.por_pagina + 1

    @property
    def hasta(self) -> int:
        return min(self.pagina * self.por_pagina, self.total)


class BaseRepository:
    """Clase base de los repositorios (herencia).

    Guarda la conexión y traduce los errores de pyodbc a errores propios del
    sistema. ColaboradorRepository y UsuarioRepository heredan de esta clase,
    así no repiten el manejo de conexiones, transacciones y errores.
    """

    # Cada repositorio hijo indica sus restricciones UNIQUE y el mensaje a mostrar
    RESTRICCIONES_UNICAS: dict[str, str] = {}

    def __init__(self, base_datos: BaseDatos):
        self._bd = base_datos

    @staticmethod
    def _ahora() -> datetime:
        """Hora local del servidor web.

        Se envía explícitamente al guardar fechas para que coincidan con la zona
        horaria local aunque SQL Server use UTC (por ejemplo, dentro de Docker).
        """
        return datetime.now()

    @contextmanager
    def _cursor(self):
        """Abre una transacción y convierte los errores de pyodbc."""
        try:
            with self._bd.transaccion() as cursor:
                yield cursor
        except pyodbc.IntegrityError as error:
            for restriccion, mensaje in self.RESTRICCIONES_UNICAS.items():
                if restriccion in str(error):
                    raise RegistroDuplicadoError(mensaje) from error
            registro.error("Violación de integridad en SQL Server: %s", error)
            raise ErrorBaseDatos("La operación no cumple las reglas de la base de datos.") from error
        except pyodbc.Error as error:
            registro.error("Error de SQL Server: %s", error)
            raise ErrorBaseDatos("Ocurrió un error al acceder a la base de datos.") from error

    @staticmethod
    def _ejecutar(cursor, sql: str, parametros: Sequence = ()):
        """Ejecuta una consulta parametrizada: los valores nunca se concatenan al SQL."""
        if parametros:
            return cursor.execute(sql, list(parametros))
        return cursor.execute(sql)

    def _consultar_todos(self, sql: str, parametros: Sequence = ()) -> list:
        with self._cursor() as cursor:
            return self._ejecutar(cursor, sql, parametros).fetchall()

    def _consultar_uno(self, sql: str, parametros: Sequence = ()):
        with self._cursor() as cursor:
            return self._ejecutar(cursor, sql, parametros).fetchone()

    def _consultar_valor(self, sql: str, parametros: Sequence = ()):
        with self._cursor() as cursor:
            return self._ejecutar(cursor, sql, parametros).fetchval()
