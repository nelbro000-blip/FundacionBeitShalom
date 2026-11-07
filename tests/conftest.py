"""Configuración compartida por todas las pruebas (fixtures de pytest)."""
import pytest

from app import crear_app
from config import ConfigPruebas
from models.colaborador import Colaborador
from models.usuario import Usuario
from tests.fakes import (
    RepositorioColaboradoresEnMemoria,
    RepositorioMensajesEnMemoria,
    RepositorioUsuariosEnMemoria,
)

PASSWORD_PRUEBA = "ClaveDePrueba2026"


@pytest.fixture
def repositorio():
    return RepositorioColaboradoresEnMemoria()


@pytest.fixture
def repositorio_mensajes():
    return RepositorioMensajesEnMemoria()


@pytest.fixture
def repositorio_usuarios():
    repositorio = RepositorioUsuariosEnMemoria()
    for nombre, rol in (("admin", Usuario.ROL_ADMINISTRADOR), ("consulta", Usuario.ROL_CONSULTA)):
        usuario = Usuario(nombre, f"Persona {nombre}", rol)
        usuario.establecer_password(PASSWORD_PRUEBA)
        repositorio.crear(usuario)
    return repositorio


@pytest.fixture
def app(repositorio, repositorio_usuarios, repositorio_mensajes):
    return crear_app(ConfigPruebas, repositorio, repositorio_usuarios, repositorio_mensajes)


@pytest.fixture
def cliente(app):
    return app.test_client()


@pytest.fixture
def datos_validos():
    """Datos de un formulario correcto, tal como los envía el navegador."""
    return {
        "nombre": "Ana Sofía Martínez",
        "pais": "El Salvador",
        "correo": "ana.martinez@example.com",
        "telefono": "+503 7012 3456",
        "modalidad": "Presencial",
        "disponibilidad": "Fines de semana",
        "motivacion": "Quiero apoyar en actividades educativas con los niños.",
        "areas": ["1", "3"],
        "privacidad": "1",
    }


def crear_colaborador(**cambios) -> Colaborador:
    datos = dict(
        nombre="Carlos Hernández",
        pais="Guatemala",
        correo="carlos@example.com",
        telefono="",
        modalidad="Virtual",
        disponibilidad="Ocasional",
        motivacion="",
        areas=[2, 5],
        acepta_privacidad=True,
    )
    datos.update(cambios)
    return Colaborador(**datos)


def iniciar_sesion(cliente, usuario="admin", password=PASSWORD_PRUEBA):
    return cliente.post("/admin/login", data={"usuario": usuario, "password": password})
