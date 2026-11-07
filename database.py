"""Administración de la conexión con SQL Server mediante pyodbc.

Este módulo solo sabe conectarse y manejar transacciones. Las consultas
SQL del sistema viven en la carpeta repositories/.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

import pyodbc

registro = logging.getLogger(__name__)


class ErrorBaseDatos(Exception):
    """No fue posible completar una operación en SQL Server."""


class BaseDatos:
    """Encapsula los datos de conexión y entrega conexiones a SQL Server."""

    def __init__(
        self,
        servidor: str,
        nombre: str,
        driver: str = "ODBC Driver 18 for SQL Server",
        conexion_confiable: bool = True,
        usuario: str = "",
        contrasena: str = "",
        cifrar: bool = True,
        confiar_certificado: bool = True,
        tiempo_espera: int = 5,
    ):
        self._servidor = servidor
        self._nombre = nombre
        self._driver = driver
        self._conexion_confiable = conexion_confiable
        self._usuario = usuario
        self.__contrasena = contrasena  # privada: no se expone fuera de la clase
        self._cifrar = cifrar
        self._confiar_certificado = confiar_certificado
        self._tiempo_espera = tiempo_espera

    @classmethod
    def desde_config(cls, config: Mapping) -> BaseDatos:
        """Crea la conexión a partir de la configuración de Flask (config.py)."""
        return cls(
            servidor=config["DB_SERVER"],
            nombre=config["DB_NAME"],
            driver=config["DB_DRIVER"],
            conexion_confiable=config["DB_TRUSTED_CONNECTION"],
            usuario=config["DB_USER"],
            contrasena=config["DB_PASSWORD"],
            cifrar=config["DB_ENCRYPT"],
            confiar_certificado=config["DB_TRUST_SERVER_CERTIFICATE"],
            tiempo_espera=config["DB_TIMEOUT"],
        )

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def servidor(self) -> str:
        return self._servidor

    @staticmethod
    def _valor_seguro(valor: str) -> str:
        """Encierra el valor entre llaves para admitir caracteres como ';'."""
        return "{" + str(valor).replace("}", "}}") + "}"

    def cadena_conexion(self, base_datos: str | None = None) -> str:
        partes = [
            f"DRIVER={self._valor_seguro(self._driver)}",
            f"SERVER={self._servidor}",
            f"DATABASE={base_datos or self._nombre}",
            f"Encrypt={'yes' if self._cifrar else 'no'}",
            f"TrustServerCertificate={'yes' if self._confiar_certificado else 'no'}",
        ]
        if self._conexion_confiable:
            partes.append("Trusted_Connection=yes")
        else:
            partes.append(f"UID={self._valor_seguro(self._usuario)}")
            partes.append(f"PWD={self._valor_seguro(self.__contrasena)}")
        return ";".join(partes) + ";"

    def obtener_conexion(self, base_datos: str | None = None, autocommit: bool = False):
        """Abre una conexión nueva. Quien la recibe debe cerrarla."""
        try:
            return pyodbc.connect(
                self.cadena_conexion(base_datos),
                autocommit=autocommit,
                timeout=self._tiempo_espera,
            )
        except pyodbc.Error as error:
            registro.error("No fue posible conectar con SQL Server (%s): %s", self._servidor, error)
            raise ErrorBaseDatos("No fue posible conectar con la base de datos.") from error

    @contextmanager
    def transaccion(self) -> Iterator[pyodbc.Cursor]:
        """Ejecuta un bloque como una sola transacción.

        Si todo sale bien se confirma (commit). Si ocurre cualquier error se
        revierte (rollback) y no queda ningún registro guardado a medias.
        """
        conexion = self.obtener_conexion()
        cursor = conexion.cursor()
        try:
            yield cursor
            conexion.commit()
        except Exception:
            try:
                conexion.rollback()
            except pyodbc.Error:
                registro.exception("No fue posible revertir la transacción")
            raise
        finally:
            cursor.close()
            conexion.close()

    def probar_conexion(self, base_datos: str | None = None) -> str:
        """Devuelve la versión de SQL Server o lanza ErrorBaseDatos."""
        conexion = self.obtener_conexion(base_datos=base_datos)
        try:
            return conexion.cursor().execute("SELECT @@VERSION").fetchval()
        finally:
            conexion.close()

    def existe_base_datos(self) -> bool:
        """Indica si la base de datos configurada (BeitShalomDB) ya fue creada."""
        conexion = self.obtener_conexion(base_datos="master")
        try:
            return conexion.cursor().execute("SELECT DB_ID(?)", self._nombre).fetchval() is not None
        finally:
            conexion.close()

    @staticmethod
    def dividir_lotes(script: str) -> list[str]:
        """Separa un script .sql en lotes usando las líneas que contienen GO."""
        lotes = re.split(r"^\s*GO\s*;?\s*$", script, flags=re.IGNORECASE | re.MULTILINE)
        return [lote.strip() for lote in lotes if lote.strip()]

    def ejecutar_script(self, ruta: Path, base_datos: str = "master") -> int:
        """Ejecuta un archivo .sql completo (equivale a abrirlo en SSMS y presionar F5)."""
        lotes = self.dividir_lotes(Path(ruta).read_text(encoding="utf-8-sig"))
        # CREATE DATABASE no puede ejecutarse dentro de una transacción
        conexion = self.obtener_conexion(base_datos=base_datos, autocommit=True)
        try:
            cursor = conexion.cursor()
            for lote in lotes:
                cursor.execute(lote)
                while cursor.nextset():
                    pass
        except pyodbc.Error as error:
            raise ErrorBaseDatos(f"Error al ejecutar {Path(ruta).name}: {error}") from error
        finally:
            conexion.close()
        return len(lotes)
