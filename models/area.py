"""Modelo AreaColaboracion."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AreaColaboracion:
    """Un área en la que una persona puede participar (tabla AreasColaboracion).

    @dataclass genera automáticamente el constructor, __repr__ y __eq__.
    frozen=True vuelve el objeto inmutable: sus datos no cambian después
    de crearlo.
    """

    id: int
    nombre: str
    activa: bool = True
