"""Pruebas reales contra SQL Server (sección 19 de la guía).

Usan la base BeitShalomDB configurada en el archivo .env. Si SQL Server no
está disponible, pytest las marca como omitidas ("skipped") en lugar de
fallar. Cada prueba borra los registros que crea.

Ejecutar solo estas pruebas:   pytest -m integracion -v
"""
import uuid
from datetime import datetime, timedelta

import pytest

from config import Config
from database import BaseDatos, ErrorBaseDatos
from models.colaborador import Colaborador
from models.usuario import Usuario
from repositories.base_repository import RegistroDuplicadoError
from repositories.colaborador_repository import ColaboradorRepository, FiltrosBusqueda
from repositories.usuario_repository import UsuarioRepository

pytestmark = pytest.mark.integracion


@pytest.fixture(scope="module")
def base_datos():
    base_datos = BaseDatos.desde_config(Config.como_diccionario())
    try:
        existe = base_datos.existe_base_datos()
    except ErrorBaseDatos:
        pytest.skip("SQL Server no está disponible: revisa el servicio y el archivo .env.")
    if not existe:
        pytest.skip("La base BeitShalomDB no existe: ejecuta 'flask --app app crear-bd'.")
    return base_datos


@pytest.fixture
def repositorio(base_datos):
    return ColaboradorRepository(base_datos)


@pytest.fixture
def correo():
    return f"prueba.{uuid.uuid4().hex[:12]}@example.test"


@pytest.fixture
def guardar(repositorio):
    """Guarda colaboradores de prueba y los elimina al terminar la prueba."""
    creados = []

    def _guardar(colaborador):
        creados.append(repositorio.guardar(colaborador))
        return creados[-1]

    yield _guardar
    for id_colaborador in creados:
        repositorio.eliminar(id_colaborador)


def nuevo_colaborador(correo, areas=(1, 3, 5), **cambios):
    datos = dict(
        nombre="Prueba de Integración",
        pais="El Salvador",
        correo=correo,
        telefono="+503 7000 0000",
        modalidad="Virtual",
        disponibilidad="Ocasional",
        motivacion="Registro creado por las pruebas automáticas.",
        areas=list(areas),
        acepta_privacidad=True,
    )
    datos.update(cambios)
    return Colaborador(**datos)


def test_enviar_informacion_correcta_se_guarda_en_sql_server(repositorio, guardar, correo):
    nuevo_id = guardar(nuevo_colaborador(correo))
    assert nuevo_id > 0
    assert repositorio.existe_correo(correo)


def test_consultar_la_base_de_datos_muestra_el_colaborador(repositorio, guardar, correo):
    nuevo_id = guardar(nuevo_colaborador(correo))
    guardado = repositorio.obtener_por_id(nuevo_id)
    assert guardado.nombre == "Prueba de Integración"
    assert guardado.correo == correo
    assert guardado.estado == "Pendiente"          # valor por defecto de la tabla
    # La fecha se guarda en la hora local, aunque SQL Server esté en UTC (Docker)
    assert abs(guardado.fecha_registro - datetime.now()) < timedelta(minutes=5)


def test_consultar_sus_areas_muestra_todas_las_seleccionadas(repositorio, guardar, correo):
    nuevo_id = guardar(nuevo_colaborador(correo, areas=(1, 3, 5)))
    guardado = repositorio.obtener_por_id(nuevo_id)
    assert guardado.areas == [1, 3, 5]
    assert guardado.nombres_areas == ["Voluntariado presencial", "Apoyo educativo", "Comunicación y difusión"]


def test_registrar_correo_duplicado_informa_que_ya_existe(repositorio, guardar, correo):
    guardar(nuevo_colaborador(correo))
    with pytest.raises(RegistroDuplicadoError, match="Ya existe una solicitud"):
        repositorio.guardar(nuevo_colaborador(correo.upper()))


def test_simular_error_sql_revierte_la_transaccion(repositorio, correo):
    # El área 999999 no existe: la segunda inserción viola la llave foránea
    with pytest.raises(ErrorBaseDatos):
        repositorio.guardar(nuevo_colaborador(correo, areas=(1, 999999)))
    # El INSERT en Colaboradores también se revirtió: no quedó nada a medias
    assert not repositorio.existe_correo(correo)


def test_sql_server_rechaza_solicitudes_sin_aceptar_privacidad(repositorio, correo):
    with pytest.raises(ErrorBaseDatos):
        repositorio.guardar(nuevo_colaborador(correo, acepta_privacidad=False))
    assert not repositorio.existe_correo(correo)


def test_busqueda_sin_tildes_y_filtros(repositorio, guardar, correo):
    nuevo_id = guardar(nuevo_colaborador(correo))
    filtros = FiltrosBusqueda(texto="integracion", pais="El Salvador", area_id=3, estado="Pendiente")
    resultado = repositorio.buscar(filtros, por_pagina=100)
    assert nuevo_id in [c.id for c in resultado.elementos]

    sin_resultados = repositorio.buscar(FiltrosBusqueda(texto=correo, area_id=2))
    assert sin_resultados.total == 0


def test_los_comodines_de_like_se_buscan_como_texto(repositorio, guardar, correo):
    nuevo_id = guardar(nuevo_colaborador(correo))
    # Sin escaparlos, "%" y "_" coincidirían con todos los registros
    for comodin in ("%", "_"):
        resultado = repositorio.buscar(FiltrosBusqueda(texto=comodin), por_pagina=1000)
        assert nuevo_id not in [c.id for c in resultado.elementos]


def test_cambiar_estado_guarda_el_historial(repositorio, guardar, correo):
    nuevo_id = guardar(nuevo_colaborador(correo))
    colaborador = repositorio.obtener_por_id(nuevo_id)
    anterior = colaborador.cambiar_estado("Aprobado", "Perfil adecuado para el programa.")
    repositorio.actualizar_estado(colaborador, anterior, None, "Perfil adecuado para el programa.")

    assert repositorio.obtener_por_id(nuevo_id).estado == "Aprobado"
    historial = repositorio.obtener_historial(nuevo_id)
    assert historial[0].estado_anterior == "Pendiente"
    assert historial[0].estado_nuevo == "Aprobado"


def test_estadisticas_del_dashboard(repositorio, guardar, correo):
    guardar(nuevo_colaborador(correo))
    estadisticas = repositorio.obtener_estadisticas()
    assert estadisticas.total >= 1
    assert sum(estadisticas.por_estado.values()) == estadisticas.total
    assert len(estadisticas.por_area) == 8
    assert len(estadisticas.por_mes) == 6
    assert estadisticas.por_mes[-1][1] >= 1          # el registro de hoy cuenta en el mes actual


def test_usuario_administrativo_guarda_solo_el_hash(base_datos):
    repositorio = UsuarioRepository(base_datos)
    usuario = Usuario(f"prueba_{uuid.uuid4().hex[:8]}", "Usuario de Prueba", Usuario.ROL_CONSULTA)
    usuario.establecer_password("ClaveDePrueba2026")
    repositorio.crear(usuario)
    try:
        guardado = repositorio.obtener_por_usuario(usuario.usuario)
        assert guardado.password_hash.startswith("scrypt:")
        assert guardado.verificar_password("ClaveDePrueba2026")
        repetido = Usuario(usuario.usuario, "Otra Persona")
        repetido.establecer_password("OtraClaveSegura2026")
        with pytest.raises(RegistroDuplicadoError):
            repositorio.crear(repetido)
    finally:
        repositorio.eliminar(usuario.id)
