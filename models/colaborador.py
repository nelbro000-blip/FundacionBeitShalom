"""Modelo Colaborador: representa a una persona que desea apoyar a la Fundación.

Conceptos de POO aplicados (sección 6 de la guía):

- Clase: Colaborador es el molde para crear objetos.
- Objeto: cada solicitud recibida se representa con una instancia.
- Constructor: __init__() inicializa los atributos.
- Atributos: nombre, país, correo, teléfono y demás datos.
- Métodos: validar() y cambiar_estado() aplican las reglas del negocio.
- Encapsulamiento: los atributos son privados (_pais, _areas, ...) y se
  accede a ellos mediante propiedades (@property). Los setters normalizan
  los datos y el estado solo puede cambiar a través de cambiar_estado().
- Herencia: Colaborador hereda de Persona el nombre, el correo, el teléfono
  y su validación (models/persona.py).
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from models.errores import ReglaNegocioError
from models.persona import Persona


class Colaborador(Persona):
    """Persona inscrita en el programa de colaboradores."""

    # ---- Límites propios (los de nombre, correo y teléfono vienen de Persona) ----
    MOTIVACION_MAX = 1000
    COMENTARIO_MAX = 500
    MOTIVO_RECHAZO_MIN = 10

    # ---- Opciones permitidas en el formulario ----
    PAISES = (
        "El Salvador", "Colombia", "Argentina", "Belice", "Bolivia", "Brasil",
        "Canadá", "Chile", "Costa Rica", "Cuba", "Ecuador", "España",
        "Estados Unidos", "Guatemala", "Honduras", "México", "Nicaragua",
        "Panamá", "Paraguay", "Perú", "Puerto Rico", "República Dominicana",
        "Uruguay", "Venezuela", "Otro",
    )
    MODALIDADES = ("Presencial", "Virtual", "Ambas")
    DISPONIBILIDADES = ("Entre semana", "Fines de semana", "Horarios flexibles", "Ocasional")

    # ---- Estados de una solicitud (restricción CK_Colaboradores_Estado) ----
    ESTADO_PENDIENTE = "Pendiente"
    ESTADO_EN_REVISION = "En revisión"
    ESTADO_APROBADO = "Aprobado"
    ESTADO_RECHAZADO = "Rechazado"
    ESTADOS = (ESTADO_PENDIENTE, ESTADO_EN_REVISION, ESTADO_APROBADO, ESTADO_RECHAZADO)

    def __init__(
        self,
        nombre: str = "",
        pais: str = "",
        correo: str = "",
        telefono: str = "",
        modalidad: str = "",
        disponibilidad: str = "",
        motivacion: str = "",
        areas: Iterable | None = None,
        acepta_privacidad: bool = False,
        *,
        id_colaborador: int | None = None,
        estado: str | None = None,
        fecha_registro: datetime | None = None,
        nombres_areas: Iterable[str] | None = None,
    ):
        # super() llama al constructor de Persona (nombre, correo y teléfono)
        super().__init__(nombre=nombre, correo=correo, telefono=telefono)
        # Las asignaciones pasan por los setters, que normalizan cada dato.
        self.pais = pais
        self.modalidad = modalidad
        self.disponibilidad = disponibilidad
        self.motivacion = motivacion
        self.areas = areas or []
        self.acepta_privacidad = acepta_privacidad
        # Datos que asigna la base de datos (solo lectura desde fuera)
        self._id = id_colaborador
        self._estado = estado or self.ESTADO_PENDIENTE
        self._fecha_registro = fecha_registro
        self._nombres_areas = list(nombres_areas or [])

    # ------------------------------------------------------------------
    # Propiedades (encapsulamiento)
    # ------------------------------------------------------------------
    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        if self._id is not None:
            raise ReglaNegocioError("El identificador de un colaborador no puede cambiar.")
        self._id = int(valor)

    @property
    def pais(self) -> str:
        return self._pais

    @pais.setter
    def pais(self, valor: str) -> None:
        self._pais = str(valor or "").strip()

    @property
    def modalidad(self) -> str:
        return self._modalidad

    @modalidad.setter
    def modalidad(self, valor: str) -> None:
        self._modalidad = str(valor or "").strip()

    @property
    def disponibilidad(self) -> str:
        return self._disponibilidad

    @disponibilidad.setter
    def disponibilidad(self, valor: str) -> None:
        self._disponibilidad = str(valor or "").strip()

    @property
    def motivacion(self) -> str:
        return self._motivacion

    @motivacion.setter
    def motivacion(self, valor: str) -> None:
        # Los navegadores envían los saltos de línea como \r\n: se cuentan como uno
        texto = str(valor or "").replace("\r\n", "\n").replace("\r", "\n")
        self._motivacion = texto.strip()

    @property
    def areas(self) -> list[int]:
        """Identificadores de las áreas seleccionadas (tabla AreasColaboracion)."""
        return list(self._areas)

    @areas.setter
    def areas(self, valores: Iterable) -> None:
        identificadores: list[int] = []
        self._areas_invalidas = False
        for valor in valores:
            try:
                id_area = int(valor)
            except (TypeError, ValueError):
                self._areas_invalidas = True
                continue
            if id_area <= 0:
                self._areas_invalidas = True
            elif id_area not in identificadores:
                identificadores.append(id_area)
        self._areas = identificadores

    @property
    def acepta_privacidad(self) -> bool:
        return self._acepta_privacidad

    @acepta_privacidad.setter
    def acepta_privacidad(self, valor: bool) -> None:
        self._acepta_privacidad = bool(valor)

    @property
    def estado(self) -> str:
        """Solo lectura: para modificarlo se usa cambiar_estado()."""
        return self._estado

    @property
    def fecha_registro(self) -> datetime | None:
        return self._fecha_registro

    @property
    def nombres_areas(self) -> list[str]:
        return list(self._nombres_areas)

    # ------------------------------------------------------------------
    # Métodos: reglas del negocio
    # ------------------------------------------------------------------
    def validar(self, areas_validas: Iterable[int] | None = None) -> dict[str, str]:
        """Valida los datos y devuelve {campo: mensaje}. Vacío = todo correcto.

        areas_validas: identificadores de las áreas activas en SQL Server. Si
        se indican, se comprueba que cada área seleccionada exista.
        """
        # Reglas heredadas de Persona: nombre, correo y teléfono
        heredados = super().validar()
        errores: dict[str, str] = {}

        # Se agregan en el mismo orden en que aparecen en el formulario
        if "nombre" in heredados:
            errores["nombre"] = heredados["nombre"]

        if not self._pais:
            errores["pais"] = "Debes seleccionar un país."
        elif self._pais not in self.PAISES:
            errores["pais"] = "Selecciona un país de la lista."

        for campo in ("telefono", "correo"):
            if campo in heredados:
                errores[campo] = heredados[campo]

        if self._areas_invalidas:
            errores["areas"] = "Una de las áreas seleccionadas no es válida."
        elif not self._areas:
            errores["areas"] = "Selecciona al menos un área de colaboración."
        elif areas_validas is not None and not set(self._areas) <= set(areas_validas):
            errores["areas"] = "Una de las áreas seleccionadas no es válida."

        if not self._modalidad:
            errores["modalidad"] = "Selecciona la modalidad de colaboración."
        elif self._modalidad not in self.MODALIDADES:
            errores["modalidad"] = "La modalidad seleccionada no es válida."

        if not self._disponibilidad:
            errores["disponibilidad"] = "Selecciona tu disponibilidad."
        elif self._disponibilidad not in self.DISPONIBILIDADES:
            errores["disponibilidad"] = "La disponibilidad seleccionada no es válida."

        if len(self._motivacion) > self.MOTIVACION_MAX:
            errores["motivacion"] = "La motivación no puede superar 1,000 caracteres."

        if not self._acepta_privacidad:
            errores["privacidad"] = "Debes aceptar la política de privacidad para enviar la solicitud."

        return errores

    def cambiar_estado(self, nuevo_estado: str, comentario: str = "") -> str:
        """Cambia el estado de la solicitud y devuelve el estado anterior.

        Reglas: el estado debe existir, debe ser distinto del actual y un
        rechazo siempre debe registrar el motivo.
        """
        nuevo_estado = (nuevo_estado or "").strip()
        comentario = (comentario or "").strip()

        if nuevo_estado not in self.ESTADOS:
            raise ReglaNegocioError("El estado seleccionado no es válido.")
        if nuevo_estado == self._estado:
            raise ReglaNegocioError(f"La solicitud ya se encuentra en estado «{nuevo_estado}».")
        if nuevo_estado == self.ESTADO_RECHAZADO and len(comentario) < self.MOTIVO_RECHAZO_MIN:
            raise ReglaNegocioError("Indica el motivo del rechazo (mínimo 10 caracteres).")
        if len(comentario) > self.COMENTARIO_MAX:
            raise ReglaNegocioError("El comentario no puede superar 500 caracteres.")

        estado_anterior = self._estado
        self._estado = nuevo_estado
        return estado_anterior

    def __repr__(self) -> str:
        return f"Colaborador(id={self._id!r}, nombre={self._nombre!r}, estado={self._estado!r})"
