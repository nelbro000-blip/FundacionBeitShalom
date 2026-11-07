"""Autenticación y autorización del panel administrativo."""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from urllib.parse import urlsplit

from flask import abort, flash, g, redirect, request, url_for


def login_requerido(vista: Callable) -> Callable:
    """Decorador: la vista solo se muestra a personas con sesión iniciada."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if g.get("usuario") is None:
            flash("Inicia sesión para acceder al panel administrativo.", "aviso")
            siguiente = request.full_path.rstrip("?") if request.method == "GET" else None
            return redirect(url_for("admin.login", siguiente=siguiente))
        return vista(*args, **kwargs)

    return envoltura


def rol_requerido(*roles: str) -> Callable:
    """Decorador: además de la sesión, exige uno de los roles indicados."""

    def decorador(vista: Callable) -> Callable:
        @wraps(vista)
        @login_requerido
        def envoltura(*args, **kwargs):
            if g.usuario.rol not in roles:
                abort(403)
            return vista(*args, **kwargs)

        return envoltura

    return decorador


def destino_seguro(destino: str | None) -> str | None:
    """Acepta solo rutas internas del panel para evitar redirecciones a otros sitios."""
    if not destino:
        return None
    partes = urlsplit(destino)
    if partes.scheme or partes.netloc or "\\" in destino or destino.startswith("//"):
        return None
    if not destino.startswith("/admin"):
        return None
    return destino


class LimitadorIntentos:
    """Bloquea temporalmente una clave después de varios intentos fallidos.

    Protege el inicio de sesión contra ataques de fuerza bruta: tras
    `maximo_intentos` fallos dentro de la ventana de tiempo, la clave
    (IP + usuario) queda bloqueada hasta que los fallos antiguos expiran.
    """

    def __init__(
        self,
        maximo_intentos: int = 5,
        ventana: timedelta = timedelta(minutes=15),
        reloj: Callable[[], float] = time.monotonic,
    ):
        self._maximo = maximo_intentos
        self._ventana = ventana.total_seconds()
        self._reloj = reloj
        self._fallos: dict[str, list[float]] = {}
        self._candado = threading.Lock()

    def _fallos_recientes(self, clave: str) -> list[float]:
        limite = self._reloj() - self._ventana
        recientes = [momento for momento in self._fallos.get(clave, []) if momento > limite]
        if recientes:
            self._fallos[clave] = recientes
        else:
            self._fallos.pop(clave, None)
        return recientes

    def esta_bloqueado(self, clave: str) -> bool:
        with self._candado:
            return len(self._fallos_recientes(clave)) >= self._maximo

    def registrar_fallo(self, clave: str) -> None:
        with self._candado:
            self._fallos_recientes(clave)
            self._fallos.setdefault(clave, []).append(self._reloj())

    def reiniciar(self, clave: str) -> None:
        with self._candado:
            self._fallos.pop(clave, None)
