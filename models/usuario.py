"""Modelo Usuario: personal autorizado para entrar al panel administrativo.

La contraseña nunca se guarda en texto plano: el objeto solo conserva su
hash (scrypt, mediante Werkzeug) en un atributo privado.
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from models.errores import ReglaNegocioError


class Usuario:
    """Cuenta del módulo administrativo."""

    ROL_ADMINISTRADOR = "Administrador"   # consulta y evalúa solicitudes
    ROL_CONSULTA = "Consulta"             # solo consulta y exporta
    ROLES = (ROL_ADMINISTRADOR, ROL_CONSULTA)

    PASSWORD_MIN = 10
    PATRON_USUARIO = re.compile(r"[a-z0-9._-]{3,50}")

    _hash_ficticio: str | None = None

    def __init__(
        self,
        usuario: str,
        nombre_completo: str,
        rol: str = ROL_CONSULTA,
        *,
        activo: bool = True,
        id_usuario: int | None = None,
        password_hash: str | None = None,
        ultimo_acceso: datetime | None = None,
    ):
        self._usuario = str(usuario or "").strip().lower()
        self._nombre_completo = " ".join(str(nombre_completo or "").split())
        self.rol = rol
        self._activo = bool(activo)
        self._id = id_usuario
        self.__password_hash = password_hash  # doble guion bajo: atributo privado
        self._ultimo_acceso = ultimo_acceso

    # ---------------------------- propiedades ----------------------------
    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        if self._id is not None:
            raise ReglaNegocioError("El identificador de un usuario no puede cambiar.")
        self._id = int(valor)

    @property
    def usuario(self) -> str:
        return self._usuario

    @property
    def nombre_completo(self) -> str:
        return self._nombre_completo

    @property
    def rol(self) -> str:
        return self._rol

    @rol.setter
    def rol(self, valor: str) -> None:
        if valor not in self.ROLES:
            raise ReglaNegocioError(f"Rol no válido. Opciones: {', '.join(self.ROLES)}.")
        self._rol = valor

    @property
    def activo(self) -> bool:
        return self._activo

    @property
    def ultimo_acceso(self) -> datetime | None:
        return self._ultimo_acceso

    @property
    def password_hash(self) -> str | None:
        """Solo lectura: el repositorio lo necesita para guardarlo en SQL Server."""
        return self.__password_hash

    @property
    def es_administrador(self) -> bool:
        return self._rol == self.ROL_ADMINISTRADOR

    # ------------------------------ métodos ------------------------------
    def puede_evaluar_solicitudes(self) -> bool:
        """Control de autorización: solo un administrador activo aprueba o rechaza."""
        return self._activo and self.es_administrador

    def validar(self) -> dict[str, str]:
        errores: dict[str, str] = {}
        if not self.PATRON_USUARIO.fullmatch(self._usuario):
            errores["usuario"] = (
                "El usuario debe tener de 3 a 50 caracteres: letras minúsculas, "
                "números, punto, guion o guion bajo."
            )
        if len(self._nombre_completo) < 3:
            errores["nombre_completo"] = "Escribe el nombre completo de la persona."
        return errores

    @classmethod
    def validar_password(cls, password: str) -> list[str]:
        """Comprueba que la contraseña sea robusta."""
        errores = []
        if len(password or "") < cls.PASSWORD_MIN:
            errores.append(f"La contraseña debe tener al menos {cls.PASSWORD_MIN} caracteres.")
        if not re.search(r"[A-ZÁÉÍÓÚÑ]", password or ""):
            errores.append("Debe incluir al menos una letra mayúscula.")
        if not re.search(r"[a-záéíóúñ]", password or ""):
            errores.append("Debe incluir al menos una letra minúscula.")
        if not re.search(r"\d", password or ""):
            errores.append("Debe incluir al menos un número.")
        return errores

    def establecer_password(self, password: str) -> None:
        """Valida la contraseña y guarda únicamente su hash."""
        errores = self.validar_password(password)
        if errores:
            raise ReglaNegocioError(" ".join(errores))
        self.__password_hash = generate_password_hash(password)

    def verificar_password(self, password: str) -> bool:
        if not self.__password_hash or not password:
            return False
        return check_password_hash(self.__password_hash, password)

    @classmethod
    def simular_verificacion(cls, password: str) -> None:
        """Tarda lo mismo que una verificación real aunque el usuario no exista.

        Así nadie puede averiguar qué usuarios existen midiendo cuánto tarda
        en responder el inicio de sesión.
        """
        if cls._hash_ficticio is None:
            cls._hash_ficticio = generate_password_hash(secrets.token_urlsafe(16))
        check_password_hash(cls._hash_ficticio, password or "")

    def __repr__(self) -> str:
        return f"Usuario(id={self._id!r}, usuario={self._usuario!r}, rol={self._rol!r})"
