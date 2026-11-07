"""Repositorio de los mensajes enviados desde la página de contacto."""
from __future__ import annotations

from models.mensaje import MensajeContacto
from repositories.base_repository import BaseRepository


class MensajeRepository(BaseRepository):
    """Guarda y consulta la tabla MensajesContacto."""

    _COLUMNAS = "id, nombre, correo, telefono, asunto, mensaje, fecha, leido"
    LIMITE_LISTADO = 300

    def guardar(self, mensaje: MensajeContacto) -> int:
        with self._cursor() as cursor:
            nuevo_id = cursor.execute(
                """
                INSERT INTO MensajesContacto (nombre, correo, telefono, asunto, mensaje, fecha)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (mensaje.nombre, mensaje.correo, mensaje.telefono or None,
                 mensaje.asunto, mensaje.mensaje, self._ahora()),
            ).fetchval()
        mensaje.id = nuevo_id
        return nuevo_id

    def listar(self, solo_no_leidos: bool = False) -> list[MensajeContacto]:
        condicion = "WHERE leido = 0" if solo_no_leidos else ""
        filas = self._consultar_todos(
            f"SELECT TOP ({self.LIMITE_LISTADO}) {self._COLUMNAS} FROM MensajesContacto "
            f"{condicion} ORDER BY fecha DESC, id DESC"
        )
        return [self._crear_mensaje(fila) for fila in filas]

    def obtener_por_id(self, id_mensaje: int) -> MensajeContacto | None:
        fila = self._consultar_uno(
            f"SELECT {self._COLUMNAS} FROM MensajesContacto WHERE id = ?", (id_mensaje,)
        )
        return self._crear_mensaje(fila) if fila else None

    def marcar_leido(self, id_mensaje: int) -> None:
        with self._cursor() as cursor:
            cursor.execute("UPDATE MensajesContacto SET leido = 1 WHERE id = ?", (id_mensaje,))

    def eliminar(self, id_mensaje: int) -> bool:
        with self._cursor() as cursor:
            return cursor.execute("DELETE FROM MensajesContacto WHERE id = ?", (id_mensaje,)).rowcount == 1

    def contar_no_leidos(self) -> int:
        return self._consultar_valor("SELECT COUNT(*) FROM MensajesContacto WHERE leido = 0")

    @staticmethod
    def _crear_mensaje(fila) -> MensajeContacto:
        return MensajeContacto(
            nombre=fila.nombre,
            correo=fila.correo,
            telefono=fila.telefono or "",
            asunto=fila.asunto,
            mensaje=fila.mensaje,
            acepta_privacidad=True,
            id_mensaje=fila.id,
            fecha=fila.fecha,
            leido=bool(fila.leido),
        )
