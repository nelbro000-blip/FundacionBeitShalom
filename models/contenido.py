"""Clases del contenido institucional del sitio (programas, equipo, eventos...).

Cada clase es un @dataclass inmutable (frozen=True): representa un dato que
se muestra en las páginas y que no cambia mientras el sitio está en uso.
El contenido se escribe en contenido/sitio.json y lo carga ContenidoRepository.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")
MESES_CORTOS = ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")


@dataclass(frozen=True)
class RedSocial:
    nombre: str
    icono: str
    url: str


@dataclass(frozen=True)
class Fundacion:
    nombre: str
    nombre_corto: str
    lema: str
    descripcion: str
    quienes_somos: str
    bienvenida: str
    mision: str
    vision: str
    direccion: str
    telefono: str
    telefono_enlace: str
    correo: str
    horario: str
    mapa: str
    video: str
    redes: tuple[RedSocial, ...]


@dataclass(frozen=True)
class Diapositiva:
    titulo: str
    imagen: str
    boton: str
    destino: str          # nombre de la ruta de Flask, por ejemplo "sitio.programas"


@dataclass(frozen=True)
class Pilar:
    titulo: str
    imagen: str
    color: str


@dataclass(frozen=True)
class Cifra:
    valor: int
    sufijo: str
    titulo: str
    icono: str


@dataclass(frozen=True)
class PreguntaFrecuente:
    pregunta: str
    respuesta: str


@dataclass(frozen=True)
class Programa:
    slug: str
    titulo: str
    resumen: str
    descripcion: str
    color: str
    icono: str
    imagen: str
    imagen_inicio: str
    imagen_detalle: str


@dataclass(frozen=True)
class MiembroEquipo:
    nombre: str
    cargo: str
    imagen: str
    color: str


@dataclass(frozen=True)
class Testimonio:
    texto: str
    autor: str
    rol: str
    imagen: str


@dataclass(frozen=True)
class Evento:
    slug: str
    titulo: str
    categoria: str
    fecha: date
    horario: str
    imagen: str
    imagen_detalle: str
    color: str
    resumen: str
    descripcion: tuple[str, ...]
    requisitos: tuple[str, ...]

    @property
    def dia(self) -> str:
        return f"{self.fecha.day:02d}"

    @property
    def mes_anio(self) -> str:
        return f"{MESES[self.fecha.month - 1].capitalize()} {self.fecha.year}"

    @property
    def fecha_texto(self) -> str:
        return f"{self.fecha.day} de {MESES[self.fecha.month - 1]} de {self.fecha.year}"

    def es_proximo(self, hoy: date | None = None) -> bool:
        return self.fecha >= (hoy or date.today())


@dataclass(frozen=True)
class Noticia:
    slug: str
    titulo: str
    categoria: str
    fecha: date
    autor: str
    cargo_autor: str
    imagen: str
    imagen_detalle: str
    color: str
    etiquetas: tuple[str, ...]
    parrafos: tuple[str, ...]

    @property
    def fecha_texto(self) -> str:
        """Ejemplo: 30 Sep, 2026 (el formato de la plantilla)."""
        return f"{self.fecha.day} {MESES_CORTOS[self.fecha.month - 1]}, {self.fecha.year}"


@dataclass(frozen=True)
class ImagenGaleria:
    imagen: str
    descripcion: str


@dataclass(frozen=True)
class FormaApoyo:
    titulo: str
    periodo: str
    precio: str
    color: str
    icono: str
    beneficios: tuple[str, ...]
    boton: str
    destino: str
    asunto: str
