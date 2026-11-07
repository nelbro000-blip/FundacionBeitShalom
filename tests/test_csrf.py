"""Protección CSRF (Flask-WTF): solo se aceptan formularios de nuestra aplicación."""
import re

import pytest

from app import crear_app
from config import ConfigPruebas


class ConfigConCsrf(ConfigPruebas):
    WTF_CSRF_ENABLED = True


@pytest.fixture
def cliente_csrf(repositorio, repositorio_usuarios, repositorio_mensajes):
    return crear_app(ConfigConCsrf, repositorio, repositorio_usuarios, repositorio_mensajes).test_client()


def test_formulario_sin_token_csrf_es_rechazado(cliente_csrf, datos_validos, repositorio):
    respuesta = cliente_csrf.post("/registro", data=datos_validos)
    assert respuesta.status_code == 400
    assert "El formulario expiró" in respuesta.get_data(as_text=True)
    assert not repositorio.colaboradores


def test_formulario_con_token_csrf_es_aceptado(cliente_csrf, datos_validos, repositorio):
    html = cliente_csrf.get("/registro").get_data(as_text=True)
    token = re.search(r'name="csrf_token"\s+value="([^"]+)"', html).group(1)
    respuesta = cliente_csrf.post("/registro", data={**datos_validos, "csrf_token": token})
    assert respuesta.status_code == 302
    assert len(repositorio.colaboradores) == 1


def test_login_sin_token_csrf_es_rechazado(cliente_csrf):
    respuesta = cliente_csrf.post("/admin/login", data={"usuario": "admin", "password": "x"})
    assert respuesta.status_code == 400
