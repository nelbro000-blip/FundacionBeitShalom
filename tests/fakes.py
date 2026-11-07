"""Repositorios en memoria para probar la aplicación sin SQL Server.

Tienen los mismos métodos que los repositorios reales (polimorfismo): el
controlador los usa exactamente igual y no nota la diferencia.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from math import ceil

from database import ErrorBaseDatos
from models.area import AreaColaboracion
from models.colaborador import Colaborador
from models.errores import ReglaNegocioError
from repositories.base_repository import RegistroDuplicadoError, ResultadoPaginado
from repositories.colaborador_repository import (
    MESES,
    CambioEstado,
    ColaboradorRepository,
    Estadisticas,
    FiltrosBusqueda,
)

NOMBRES_AREAS = (
    "Voluntariado presencial",
    "Apoyo profesional o técnico",
    "Apoyo educativo",
    "Organización de actividades",
    "Comunicación y difusión",
    "Apoyo administrativo",
    "Donaciones y gestión de recursos",
    "Otro tipo de colaboración",
)


def copiar(colaborador: Colaborador, **cambios) -> Colaborador:
    datos = dict(
        nombre=colaborador.nombre,
        pais=colaborador.pais,
        correo=colaborador.correo,
        telefono=colaborador.telefono,
        modalidad=colaborador.modalidad,
        disponibilidad=colaborador.disponibilidad,
        motivacion=colaborador.motivacion,
        areas=colaborador.areas,
        acepta_privacidad=colaborador.acepta_privacidad,
        id_colaborador=colaborador.id,
        estado=colaborador.estado,
        fecha_registro=colaborador.fecha_registro,
        nombres_areas=colaborador.nombres_areas,
    )
    datos.update(cambios)
    return Colaborador(**datos)


class RepositorioColaboradoresEnMemoria:
    """Misma interfaz que ColaboradorRepository, guardando en un diccionario."""

    def __init__(self):
        self.areas = [AreaColaboracion(i, nombre) for i, nombre in enumerate(NOMBRES_AREAS, start=1)]
        self.colaboradores: dict[int, Colaborador] = {}
        self.historial: dict[int, list[CambioEstado]] = {}
        self.disponible = True          # False simula que SQL Server está caído
        self.ultimos_filtros: FiltrosBusqueda | None = None
        self._siguiente_id = 1

    def _verificar(self) -> None:
        if not self.disponible:
            raise ErrorBaseDatos("SQL Server no disponible (simulado).")

    # --- registro público ---
    def obtener_areas_activas(self):
        self._verificar()
        return [area for area in self.areas if area.activa]

    def obtener_areas(self):
        self._verificar()
        return list(self.areas)

    def existe_correo(self, correo: str) -> bool:
        self._verificar()
        return any(c.correo == correo.strip().lower() for c in self.colaboradores.values())

    def guardar(self, colaborador: Colaborador, dias_atras: int = 0) -> int:
        self._verificar()
        if self.existe_correo(colaborador.correo):
            raise RegistroDuplicadoError("Ya existe una solicitud registrada con este correo electrónico.")
        nombres = {area.id: area.nombre for area in self.areas}
        nuevo_id = self._siguiente_id
        self._siguiente_id += 1
        self.colaboradores[nuevo_id] = copiar(
            colaborador,
            id_colaborador=nuevo_id,
            fecha_registro=datetime.now() - timedelta(days=dias_atras),
            nombres_areas=[nombres[id_area] for id_area in colaborador.areas],
        )
        colaborador.id = nuevo_id
        return nuevo_id

    # --- panel administrativo ---
    def obtener_por_id(self, id_colaborador: int):
        self._verificar()
        guardado = self.colaboradores.get(id_colaborador)
        return copiar(guardado) if guardado else None

    def _filtrar(self, filtros: FiltrosBusqueda) -> list[Colaborador]:
        texto = filtros.texto.lower()
        ordenados = sorted(self.colaboradores.values(), key=lambda c: (c.fecha_registro, c.id), reverse=True)
        return [
            copiar(c)
            for c in ordenados
            if (not texto or texto in c.nombre.lower() or texto in c.correo)
            and (not filtros.pais or c.pais == filtros.pais)
            and (not filtros.estado or c.estado == filtros.estado)
            and (not filtros.area_id or filtros.area_id in c.areas)
        ]

    def buscar(self, filtros: FiltrosBusqueda, pagina: int = 1, por_pagina: int = 15):
        self._verificar()
        self.ultimos_filtros = filtros
        lista = self._filtrar(filtros)
        pagina = min(max(1, pagina), max(1, ceil(len(lista) / por_pagina)))
        inicio = (pagina - 1) * por_pagina
        return ResultadoPaginado(lista[inicio:inicio + por_pagina], len(lista), pagina, por_pagina)

    def listar(self, filtros: FiltrosBusqueda):
        self._verificar()
        self.ultimos_filtros = filtros
        return self._filtrar(filtros)

    def paises_registrados(self):
        self._verificar()
        return sorted({c.pais for c in self.colaboradores.values()})

    def obtener_historial(self, id_colaborador: int):
        self._verificar()
        return list(self.historial.get(id_colaborador, []))

    def actualizar_estado(self, colaborador, estado_anterior, usuario_id, comentario=""):
        self._verificar()
        guardado = self.colaboradores[colaborador.id]
        if guardado.estado != estado_anterior:
            raise ReglaNegocioError("Otra persona modificó esta solicitud. Recarga la página e inténtalo de nuevo.")
        self.colaboradores[colaborador.id] = copiar(guardado, estado=colaborador.estado)
        self.historial.setdefault(colaborador.id, []).insert(
            0, CambioEstado(datetime.now(), estado_anterior, colaborador.estado, comentario, f"Usuario {usuario_id}")
        )

    def eliminar(self, id_colaborador: int) -> bool:
        self._verificar()
        self.historial.pop(id_colaborador, None)
        return self.colaboradores.pop(id_colaborador, None) is not None

    def eliminar_rechazados_antes_de(self, fecha_limite: datetime) -> int:
        self._verificar()
        antiguos = [
            c.id for c in self.colaboradores.values()
            if c.estado == Colaborador.ESTADO_RECHAZADO and c.fecha_registro < fecha_limite
        ]
        for id_colaborador in antiguos:
            self.eliminar(id_colaborador)
        return len(antiguos)

    def obtener_estadisticas(self) -> Estadisticas:
        self._verificar()
        lista = list(self.colaboradores.values())
        hace_7_dias = datetime.now() - timedelta(days=7)
        estados = Counter(c.estado for c in lista)
        areas = Counter(nombre for c in lista for nombre in c.nombres_areas)
        modalidades = Counter(c.modalidad for c in lista)
        disponibilidades = Counter(c.disponibilidad for c in lista)
        meses = Counter((c.fecha_registro.year, c.fecha_registro.month) for c in lista)
        return Estadisticas(
            total=len(lista),
            ultimos_7_dias=sum(1 for c in lista if c.fecha_registro >= hace_7_dias),
            por_estado={estado: estados.get(estado, 0) for estado in Colaborador.ESTADOS},
            por_area=sorted(((a.nombre, areas.get(a.nombre, 0)) for a in self.areas), key=lambda par: -par[1]),
            por_pais=Counter(c.pais for c in lista).most_common(8),
            por_modalidad=ColaboradorRepository._ordenar(Colaborador.MODALIDADES, modalidades),
            por_disponibilidad=ColaboradorRepository._ordenar(Colaborador.DISPONIBILIDADES, disponibilidades),
            por_mes=[
                (f"{MESES[mes - 1]} {anio}", meses.get((anio, mes), 0))
                for anio, mes in ColaboradorRepository._ultimos_meses(ColaboradorRepository.MESES_GRAFICO)
            ],
            recientes=[copiar(c) for c in sorted(lista, key=lambda c: (c.fecha_registro, c.id), reverse=True)[:5]],
        )


class RepositorioMensajesEnMemoria:
    """Misma interfaz que MensajeRepository."""

    def __init__(self):
        self.mensajes = {}
        self.disponible = True
        self._siguiente_id = 1

    def _verificar(self) -> None:
        if not self.disponible:
            raise ErrorBaseDatos("SQL Server no disponible (simulado).")

    def guardar(self, mensaje) -> int:
        self._verificar()
        mensaje.id = self._siguiente_id
        self.mensajes[mensaje.id] = mensaje
        self._siguiente_id += 1
        return mensaje.id

    def listar(self, solo_no_leidos: bool = False):
        self._verificar()
        lista = sorted(self.mensajes.values(), key=lambda m: m.id, reverse=True)
        return [m for m in lista if not (solo_no_leidos and m.leido)]

    def obtener_por_id(self, id_mensaje: int):
        self._verificar()
        return self.mensajes.get(id_mensaje)

    def marcar_leido(self, id_mensaje: int) -> None:
        self._verificar()
        self.mensajes[id_mensaje].marcar_leido()

    def eliminar(self, id_mensaje: int) -> bool:
        self._verificar()
        return self.mensajes.pop(id_mensaje, None) is not None

    def contar_no_leidos(self) -> int:
        self._verificar()
        return sum(1 for m in self.mensajes.values() if not m.leido)


class RepositorioUsuariosEnMemoria:
    """Misma interfaz que UsuarioRepository."""

    def __init__(self):
        self.usuarios = {}
        self.accesos: list[int] = []
        self._siguiente_id = 1

    def obtener_por_usuario(self, nombre_usuario: str):
        nombre_usuario = str(nombre_usuario or "").strip().lower()
        return next((u for u in self.usuarios.values() if u.usuario == nombre_usuario), None)

    def obtener_por_id(self, id_usuario: int):
        return self.usuarios.get(id_usuario)

    def crear(self, usuario) -> int:
        if self.obtener_por_usuario(usuario.usuario):
            raise RegistroDuplicadoError("Ya existe un usuario con ese nombre.")
        usuario.id = self._siguiente_id
        self.usuarios[usuario.id] = usuario
        self._siguiente_id += 1
        return usuario.id

    def actualizar_password(self, usuario) -> None:
        self.usuarios[usuario.id] = usuario

    def registrar_acceso(self, id_usuario: int) -> None:
        self.accesos.append(id_usuario)

    def contar(self) -> int:
        return len(self.usuarios)
