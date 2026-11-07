"""Clase base Persona: datos de contacto comunes a varios modelos.

Herencia: Colaborador (quien se registra para colaborar) y MensajeContacto
(quien escribe desde la página de contacto) heredan de Persona. Así el
nombre, el correo y el teléfono se normalizan y validan en un solo lugar.

Polimorfismo: cada clase hija tiene su propio método validar(), y puede
cambiar una regla heredada sobrescribiendo una constante (por ejemplo,
MensajeContacto acepta nombres más cortos que Colaborador).
"""
from __future__ import annotations

import re


class Persona:
    """Nombre, correo y teléfono de una persona."""

    NOMBRE_MIN = 5
    NOMBRE_MAX = 150
    CORREO_MAX = 150
    TELEFONO_MAX = 30
    TELEFONO_MIN_DIGITOS = 7
    TELEFONO_MAX_DIGITOS = 15

    # Los mismos patrones que usan HTML5 (pattern) y validaciones.js
    PATRON_NOMBRE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ '.\-]*")
    PATRON_CORREO = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
    PATRON_TELEFONO = re.compile(r"\+?[0-9\s()\-]{7,30}")

    def __init__(self, nombre: str = "", correo: str = "", telefono: str = ""):
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    # ------------------------------------------------------------------
    # Propiedades (encapsulamiento)
    # ------------------------------------------------------------------
    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        # " ".join(split()) elimina espacios al inicio, al final y repetidos
        self._nombre = " ".join(str(valor or "").split())

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        self._correo = str(valor or "").strip().lower()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        self._telefono = " ".join(str(valor or "").split())

    @property
    def primer_nombre(self) -> str:
        return self._nombre.split(" ")[0] if self._nombre else ""

    @property
    def correo_enmascarado(self) -> str:
        """Ejemplo: ana.perez@gmail.com -> an*******@gmail.com"""
        if "@" not in self._correo:
            return ""
        usuario, dominio = self._correo.split("@", 1)
        visible = usuario[:2]
        return f"{visible}{'*' * max(len(usuario) - len(visible), 3)}@{dominio}"

    # ------------------------------------------------------------------
    # Validación de los datos de contacto
    # ------------------------------------------------------------------
    def _validar_nombre(self) -> str:
        if not self._nombre:
            return "El nombre es obligatorio."
        if len(self._nombre) < self.NOMBRE_MIN:
            return f"Ingresa tu nombre completo (mínimo {self.NOMBRE_MIN} caracteres)."
        if len(self._nombre) > self.NOMBRE_MAX:
            return f"El nombre no puede superar {self.NOMBRE_MAX} caracteres."
        if not self.PATRON_NOMBRE.fullmatch(self._nombre):
            return "El nombre solo puede contener letras, espacios, apóstrofos, puntos y guiones."
        return ""

    def _validar_correo(self) -> str:
        if not self._correo:
            return "El correo electrónico es obligatorio."
        if len(self._correo) > self.CORREO_MAX or not self.PATRON_CORREO.fullmatch(self._correo):
            return "Ingresa un correo electrónico válido."
        return ""

    def _validar_telefono(self) -> str:
        """El teléfono es opcional; si se escribe, debe tener un formato válido."""
        if not self._telefono:
            return ""
        digitos = sum(caracter.isdigit() for caracter in self._telefono)
        if (
            len(self._telefono) > self.TELEFONO_MAX
            or not self.PATRON_TELEFONO.fullmatch(self._telefono)
            or not self.TELEFONO_MIN_DIGITOS <= digitos <= self.TELEFONO_MAX_DIGITOS
        ):
            return "Revisa el número de teléfono (solo números, espacios, +, guiones o paréntesis)."
        return ""

    def validar(self) -> dict[str, str]:
        """Devuelve {campo: mensaje}. Las clases hijas agregan sus propias reglas."""
        errores = {
            "nombre": self._validar_nombre(),
            "correo": self._validar_correo(),
            "telefono": self._validar_telefono(),
        }
        return {campo: mensaje for campo, mensaje in errores.items() if mensaje}

    def es_valido(self, *args, **kwargs) -> bool:
        return not self.validar(*args, **kwargs)
