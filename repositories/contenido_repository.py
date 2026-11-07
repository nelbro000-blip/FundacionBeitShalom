"""Repositorio del contenido institucional (contenido/sitio.json).

Igual que los repositorios de SQL Server, entrega objetos del modelo; la
diferencia es que los lee de un archivo JSON. Así, para cambiar un texto,
una foto o agregar una noticia basta con editar ese archivo.
"""
from __future__ import annotations

import json
import threading
from datetime import date
from pathlib import Path

from models.contenido import (
    Cifra,
    Diapositiva,
    Evento,
    FormaApoyo,
    Fundacion,
    ImagenGaleria,
    MiembroEquipo,
    Noticia,
    Pilar,
    PreguntaFrecuente,
    Programa,
    RedSocial,
    Testimonio,
)


class ContenidoRepository:
    """Lee el contenido del sitio y lo convierte en objetos."""

    def __init__(self, ruta: Path):
        self._ruta = Path(ruta)
        self._datos: dict | None = None
        self._modificado: float | None = None
        self._candado = threading.Lock()

    def _cargar(self) -> dict:
        """Lee el JSON y lo vuelve a leer automáticamente si el archivo cambió."""
        modificado = self._ruta.stat().st_mtime
        with self._candado:
            if self._datos is None or modificado != self._modificado:
                self._datos = json.loads(self._ruta.read_text(encoding="utf-8"))
                self._modificado = modificado
            return self._datos

    # ------------------------------------------------------------------
    def fundacion(self) -> Fundacion:
        datos = dict(self._cargar()["fundacion"])
        datos["redes"] = tuple(RedSocial(**red) for red in datos["redes"])
        return Fundacion(**datos)

    def diapositivas(self) -> list[Diapositiva]:
        return [Diapositiva(**d) for d in self._cargar()["diapositivas"]]

    def pilares(self) -> list[Pilar]:
        return [Pilar(**p) for p in self._cargar()["pilares"]]

    def cifras(self) -> list[Cifra]:
        return [Cifra(**c) for c in self._cargar()["cifras"]]

    def programas(self) -> list[Programa]:
        return [Programa(**p) for p in self._cargar()["programas"]]

    def programa(self, slug: str) -> Programa | None:
        return next((p for p in self.programas() if p.slug == slug), None)

    def preguntas_programa(self) -> list[PreguntaFrecuente]:
        return [PreguntaFrecuente(**p) for p in self._cargar()["preguntas_programa"]]

    def equipo(self) -> list[MiembroEquipo]:
        return [MiembroEquipo(**m) for m in self._cargar()["equipo"]]

    def testimonios(self) -> list[Testimonio]:
        return [Testimonio(**t) for t in self._cargar()["testimonios"]]

    def eventos(self) -> list[Evento]:
        """Eventos ordenados por fecha (el más cercano primero)."""
        eventos = [
            Evento(**{**e, "fecha": date.fromisoformat(e["fecha"]),
                      "descripcion": tuple(e["descripcion"]), "requisitos": tuple(e["requisitos"])})
            for e in self._cargar()["eventos"]
        ]
        return sorted(eventos, key=lambda evento: evento.fecha)

    def evento(self, slug: str) -> Evento | None:
        return next((e for e in self.eventos() if e.slug == slug), None)

    def noticias(self) -> list[Noticia]:
        """Noticias ordenadas de la más reciente a la más antigua."""
        noticias = [
            Noticia(**{**n, "fecha": date.fromisoformat(n["fecha"]),
                       "etiquetas": tuple(n["etiquetas"]), "parrafos": tuple(n["parrafos"])})
            for n in self._cargar()["noticias"]
        ]
        return sorted(noticias, key=lambda noticia: noticia.fecha, reverse=True)

    def noticia(self, slug: str) -> Noticia | None:
        return next((n for n in self.noticias() if n.slug == slug), None)

    def galeria(self) -> list[ImagenGaleria]:
        return [ImagenGaleria(**g) for g in self._cargar()["galeria"]]

    def preguntas_frecuentes(self) -> list[PreguntaFrecuente]:
        return [PreguntaFrecuente(**p) for p in self._cargar()["preguntas_frecuentes"]]

    def formas_apoyo(self) -> list[FormaApoyo]:
        return [FormaApoyo(**{**f, "beneficios": tuple(f["beneficios"])}) for f in self._cargar()["formas_apoyo"]]
