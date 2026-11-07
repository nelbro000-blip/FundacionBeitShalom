"""Modelo MensajeContacto: mensaje enviado desde la página de contacto."""
from __future__ import annotations

from datetime import datetime

from models.persona import Persona


class MensajeContacto(Persona):
    """Mensaje de una persona que escribe a la Fundación.

    Hereda de Persona el nombre, el correo, el teléfono y su validación.
    Sobrescribe NOMBRE_MIN porque aquí basta con un nombre corto (polimorfismo).
    """

    NOMBRE_MIN = 3
    MENSAJE_MIN = 10
    MENSAJE_MAX = 2000

    ASUNTOS = {
        "informacion": "Información general",
        "voluntariado": "Quiero ser voluntario",
        "donacion": "Quiero apoyar con una donación",
        "inscripcion": "Inscribir a mi hijo o hija",
        "otro": "Otro asunto",
    }

    def __init__(
        self,
        nombre: str = "",
        correo: str = "",
        telefono: str = "",
        asunto: str = "",
        mensaje: str = "",
        acepta_privacidad: bool = False,
        *,
        id_mensaje: int | None = None,
        fecha: datetime | None = None,
        leido: bool = False,
    ):
        super().__init__(nombre=nombre, correo=correo, telefono=telefono)
        self.asunto = asunto
        self.mensaje = mensaje
        self._acepta_privacidad = bool(acepta_privacidad)
        self._id = id_mensaje
        self._fecha = fecha
        self._leido = bool(leido)

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        self._id = int(valor)

    @property
    def asunto(self) -> str:
        """Clave del asunto (por ejemplo "donacion")."""
        return self._asunto

    @asunto.setter
    def asunto(self, valor: str) -> None:
        self._asunto = str(valor or "").strip()

    @property
    def asunto_texto(self) -> str:
        return self.ASUNTOS.get(self._asunto, self._asunto)

    @property
    def mensaje(self) -> str:
        return self._mensaje

    @mensaje.setter
    def mensaje(self, valor: str) -> None:
        self._mensaje = str(valor or "").replace("\r\n", "\n").replace("\r", "\n").strip()

    @property
    def acepta_privacidad(self) -> bool:
        return self._acepta_privacidad

    @property
    def fecha(self) -> datetime | None:
        return self._fecha

    @property
    def leido(self) -> bool:
        return self._leido

    def marcar_leido(self) -> None:
        self._leido = True

    def validar(self) -> dict[str, str]:
        """Reglas heredadas de Persona + asunto, mensaje y privacidad."""
        errores = super().validar()
        if self._asunto not in self.ASUNTOS:
            errores["asunto"] = "Selecciona el asunto de tu mensaje."
        if len(self._mensaje) < self.MENSAJE_MIN:
            errores["mensaje"] = f"Escribe tu mensaje (mínimo {self.MENSAJE_MIN} caracteres)."
        elif len(self._mensaje) > self.MENSAJE_MAX:
            errores["mensaje"] = f"El mensaje no puede superar {self.MENSAJE_MAX} caracteres."
        if not self._acepta_privacidad:
            errores["privacidad"] = "Debes aceptar la política de privacidad para enviar el mensaje."
        return errores

    def __repr__(self) -> str:
        return f"MensajeContacto(id={self._id!r}, asunto={self._asunto!r}, leido={self._leido!r})"
