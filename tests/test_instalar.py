"""Pruebas de las utilidades del asistente instalar.py."""
from io import StringIO

import pytest
from dotenv import dotenv_values

from instalar import contenido_env, elegir_autenticacion, elegir_driver, valor_env


def test_elige_el_driver_mas_reciente():
    assert elegir_driver(["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server"]) == "ODBC Driver 18 for SQL Server"
    assert elegir_driver(["SQL Server"]) == "SQL Server"
    assert elegir_driver(["PostgreSQL Unicode"]) is None


@pytest.mark.parametrize("valor", [
    "Clave2026", "con espacio", 'co"mi"llas', "barra\\invertida", "almo#hadilla", "localhost\\SQLEXPRESS", "",
])
def test_los_valores_del_env_se_leen_igual_que_se_escribieron(valor):
    leido = dotenv_values(stream=StringIO(f"CLAVE={valor_env(valor)}\n"))
    assert leido["CLAVE"] == valor


def test_env_con_autenticacion_de_windows_no_guarda_contrasena():
    datos = dotenv_values(stream=StringIO(contenido_env("localhost\\SQLEXPRESS", "ODBC Driver 18 for SQL Server", True, "", "")))
    assert datos["DB_TRUSTED_CONNECTION"] == "yes"
    assert datos["DB_SERVER"] == "localhost\\SQLEXPRESS"
    assert datos["DB_PASSWORD"] == ""
    assert len(datos["SECRET_KEY"]) == 64


def test_env_con_usuario_sa():
    datos = dotenv_values(stream=StringIO(contenido_env("localhost", "ODBC Driver 18 for SQL Server", False, "sa", "Mi Clave#1")))
    assert (datos["DB_TRUSTED_CONNECTION"], datos["DB_USER"], datos["DB_PASSWORD"]) == ("no", "sa", "Mi Clave#1")


@pytest.mark.parametrize("respuestas, es_windows", [
    ([""], False),          # Enter: usuario sa, como en la guía del profesor
    (["2"], False),
    (["1"], True),
    (["3", "1"], True),     # una respuesta inválida se vuelve a preguntar
])
def test_en_windows_la_opcion_por_defecto_es_el_usuario_sa(monkeypatch, respuestas, es_windows):
    entradas = iter(respuestas)
    monkeypatch.setattr("builtins.input", lambda _texto: next(entradas))
    assert elegir_autenticacion() is es_windows
