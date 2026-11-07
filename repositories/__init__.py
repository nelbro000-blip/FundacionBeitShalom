"""Repositorios: única capa que ejecuta instrucciones SQL.

Es una capa adicional al MVC tradicional: evita que el acceso a datos quede
mezclado con el modelo o con el controlador.
"""
from repositories.base_repository import RegistroDuplicadoError, ResultadoPaginado
from repositories.colaborador_repository import (
    CambioEstado,
    ColaboradorRepository,
    Estadisticas,
    FiltrosBusqueda,
)
from repositories.usuario_repository import UsuarioRepository

__all__ = [
    "CambioEstado",
    "ColaboradorRepository",
    "Estadisticas",
    "FiltrosBusqueda",
    "RegistroDuplicadoError",
    "ResultadoPaginado",
    "UsuarioRepository",
]
