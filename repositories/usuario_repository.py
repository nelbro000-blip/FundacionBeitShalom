"""Repositorio de usuarios del panel administrativo."""
from __future__ import annotations

from models.errores import ReglaNegocioError
from models.usuario import Usuario
from repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository):
    """Guarda y consulta las cuentas del personal autorizado."""

    RESTRICCIONES_UNICAS = {"UQ_Usuarios_Usuario": "Ya existe un usuario con ese nombre."}

    _COLUMNAS = "id, usuario, nombre_completo, password_hash, rol, activo, ultimo_acceso"

    def obtener_por_usuario(self, nombre_usuario: str) -> Usuario | None:
        fila = self._consultar_uno(
            f"SELECT {self._COLUMNAS} FROM Usuarios WHERE usuario = ?",
            (str(nombre_usuario or "").strip().lower(),),
        )
        return self._crear_usuario(fila) if fila else None

    def obtener_por_id(self, id_usuario: int) -> Usuario | None:
        fila = self._consultar_uno(f"SELECT {self._COLUMNAS} FROM Usuarios WHERE id = ?", (id_usuario,))
        return self._crear_usuario(fila) if fila else None

    def crear(self, usuario: Usuario) -> int:
        if not usuario.password_hash:
            raise ReglaNegocioError("El usuario necesita una contraseña antes de guardarse.")
        with self._cursor() as cursor:
            nuevo_id = cursor.execute(
                """
                INSERT INTO Usuarios (usuario, nombre_completo, password_hash, rol, activo, fecha_creacion)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (usuario.usuario, usuario.nombre_completo, usuario.password_hash, usuario.rol, usuario.activo,
                 self._ahora()),
            ).fetchval()
        usuario.id = nuevo_id
        return nuevo_id

    def actualizar_password(self, usuario: Usuario) -> None:
        with self._cursor() as cursor:
            cursor.execute(
                "UPDATE Usuarios SET password_hash = ? WHERE id = ?", (usuario.password_hash, usuario.id)
            )

    def registrar_acceso(self, id_usuario: int) -> None:
        with self._cursor() as cursor:
            cursor.execute("UPDATE Usuarios SET ultimo_acceso = ? WHERE id = ?", (self._ahora(), id_usuario))

    def contar(self) -> int:
        return self._consultar_valor("SELECT COUNT(*) FROM Usuarios")

    def eliminar(self, id_usuario: int) -> bool:
        with self._cursor() as cursor:
            return cursor.execute("DELETE FROM Usuarios WHERE id = ?", (id_usuario,)).rowcount == 1

    @staticmethod
    def _crear_usuario(fila) -> Usuario:
        return Usuario(
            usuario=fila.usuario,
            nombre_completo=fila.nombre_completo,
            rol=fila.rol,
            activo=bool(fila.activo),
            id_usuario=fila.id,
            password_hash=fila.password_hash,
            ultimo_acceso=fila.ultimo_acceso,
        )
