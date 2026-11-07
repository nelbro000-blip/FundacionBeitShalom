"""Pruebas del modelo Colaborador: reglas del negocio (POO)."""
import pytest

from models.colaborador import Colaborador
from models.errores import ReglaNegocioError
from tests.conftest import crear_colaborador

AREAS_ACTIVAS = list(range(1, 9))


def test_colaborador_correcto_no_tiene_errores():
    colaborador = crear_colaborador()
    assert colaborador.validar(AREAS_ACTIVAS) == {}
    assert colaborador.es_valido(AREAS_ACTIVAS)


def test_formulario_vacio_muestra_todos_los_errores():
    errores = Colaborador().validar(AREAS_ACTIVAS)
    assert set(errores) == {"nombre", "pais", "correo", "areas", "modalidad", "disponibilidad", "privacidad"}


@pytest.mark.parametrize("correo", ["ana", "ana@", "ana@correo", "ana correo@example.com", "@example.com", "ana@@example.com"])
def test_correo_incorrecto_es_rechazado(correo):
    errores = crear_colaborador(correo=correo).validar(AREAS_ACTIVAS)
    assert errores["correo"] == "Ingresa un correo electrónico válido."


def test_no_seleccionar_areas_solicita_al_menos_una():
    errores = crear_colaborador(areas=[]).validar(AREAS_ACTIVAS)
    assert errores["areas"] == "Selecciona al menos un área de colaboración."


def test_area_que_no_existe_en_sql_server_es_rechazada():
    errores = crear_colaborador(areas=[1, 99]).validar(AREAS_ACTIVAS)
    assert "no es válida" in errores["areas"]


def test_area_con_valor_no_numerico_es_rechazada():
    colaborador = crear_colaborador(areas=["1", "abc"])
    assert colaborador.areas == [1]
    assert "no es válida" in colaborador.validar(AREAS_ACTIVAS)["areas"]


def test_areas_repetidas_se_guardan_una_sola_vez():
    assert crear_colaborador(areas=["3", "3", 5]).areas == [3, 5]


def test_no_aceptar_privacidad_impide_el_registro():
    errores = crear_colaborador(acepta_privacidad=False).validar(AREAS_ACTIVAS)
    assert "privacidad" in errores


@pytest.mark.parametrize("telefono", ["", "+503 7012 3456", "(503) 7012-3456", "70123456", "+1 202 555 0147"])
def test_telefonos_validos(telefono):
    assert "telefono" not in crear_colaborador(telefono=telefono).validar(AREAS_ACTIVAS)


@pytest.mark.parametrize("telefono", ["abc", "12345", "+503 7012 3456 ext 2", "++50370123456", "1234567890123456"])
def test_telefonos_invalidos(telefono):
    assert "telefono" in crear_colaborador(telefono=telefono).validar(AREAS_ACTIVAS)


@pytest.mark.parametrize("nombre", ["Ana", "Ana123", "<script>alert(1)</script>", "Juan; DROP TABLE"])
def test_nombres_invalidos(nombre):
    assert "nombre" in crear_colaborador(nombre=nombre).validar(AREAS_ACTIVAS)


@pytest.mark.parametrize("nombre", ["María José Pérez", "Liam O'Connor", "Ana-Lucía Ruiz", "Ñandú Güemes Jr."])
def test_nombres_validos(nombre):
    assert "nombre" not in crear_colaborador(nombre=nombre).validar(AREAS_ACTIVAS)


def test_nombre_demasiado_largo():
    assert "nombre" in crear_colaborador(nombre="A" * 151).validar(AREAS_ACTIVAS)


def test_motivacion_maximo_1000_caracteres():
    assert "motivacion" not in crear_colaborador(motivacion="a" * 1000).validar(AREAS_ACTIVAS)
    assert "motivacion" in crear_colaborador(motivacion="a" * 1001).validar(AREAS_ACTIVAS)


def test_saltos_de_linea_del_navegador_cuentan_como_uno():
    texto = "linea\r\n" * 140   # 7 caracteres visibles por línea
    colaborador = crear_colaborador(motivacion=texto)
    assert "\r" not in colaborador.motivacion
    assert len(colaborador.motivacion) < 1000


@pytest.mark.parametrize("campo, valor", [("pais", "Narnia"), ("modalidad", "A distancia"), ("disponibilidad", "Nunca")])
def test_opciones_fuera_de_la_lista_son_rechazadas(campo, valor):
    assert campo in crear_colaborador(**{campo: valor}).validar(AREAS_ACTIVAS)


def test_los_setters_normalizan_los_datos():
    colaborador = crear_colaborador(nombre="  ana   sofía  ", correo="  ANA@Example.COM ", telefono=" +503  7000 0000 ")
    assert colaborador.nombre == "ana sofía"
    assert colaborador.correo == "ana@example.com"
    assert colaborador.telefono == "+503 7000 0000"


def test_estado_inicial_es_pendiente_y_es_de_solo_lectura():
    colaborador = crear_colaborador()
    assert colaborador.estado == "Pendiente"
    with pytest.raises(AttributeError):
        colaborador.estado = "Aprobado"


def test_el_identificador_no_puede_cambiar():
    colaborador = crear_colaborador()
    colaborador.id = 10
    with pytest.raises(ReglaNegocioError):
        colaborador.id = 11


def test_cambiar_estado_devuelve_el_estado_anterior():
    colaborador = crear_colaborador()
    assert colaborador.cambiar_estado("En revisión") == "Pendiente"
    assert colaborador.estado == "En revisión"


@pytest.mark.parametrize("estado, comentario", [
    ("Archivado", ""),                 # no existe
    ("Pendiente", ""),                 # ya está en ese estado
    ("Rechazado", ""),                 # rechazo sin motivo
    ("Rechazado", "No aplica"),        # motivo demasiado corto
    ("Aprobado", "x" * 501),           # comentario demasiado largo
])
def test_reglas_para_cambiar_estado(estado, comentario):
    colaborador = crear_colaborador()
    with pytest.raises(ReglaNegocioError):
        colaborador.cambiar_estado(estado, comentario)
    assert colaborador.estado == "Pendiente"


def test_rechazo_con_motivo_es_valido():
    colaborador = crear_colaborador()
    colaborador.cambiar_estado("Rechazado", "No hay actividades en su zona.")
    assert colaborador.estado == "Rechazado"


def test_datos_para_la_pagina_de_confirmacion():
    colaborador = crear_colaborador(nombre="Ana Sofía Martínez", correo="ana.martinez@example.com")
    assert colaborador.primer_nombre == "Ana"
    assert colaborador.correo_enmascarado == "an**********@example.com"
