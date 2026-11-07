"""Pruebas del modelo Usuario: contraseñas con hash y roles."""
import pytest

from models.errores import ReglaNegocioError
from models.usuario import Usuario


def test_la_contrasena_se_guarda_como_hash_y_no_en_texto_plano():
    usuario = Usuario("admin", "Administrador", Usuario.ROL_ADMINISTRADOR)
    usuario.establecer_password("ClaveSegura2026")
    assert usuario.password_hash != "ClaveSegura2026"
    assert "ClaveSegura2026" not in usuario.password_hash
    assert usuario.password_hash.startswith("scrypt:")


def test_verificar_contrasena():
    usuario = Usuario("admin", "Administrador")
    usuario.establecer_password("ClaveSegura2026")
    assert usuario.verificar_password("ClaveSegura2026")
    assert not usuario.verificar_password("clavesegura2026")
    assert not usuario.verificar_password("")


def test_el_hash_es_privado():
    usuario = Usuario("admin", "Administrador")
    with pytest.raises(AttributeError):
        usuario.password_hash = "texto plano"


@pytest.mark.parametrize("password", ["corta1A", "sinnumerosNiMayus", "SINMINUSCULAS123", "SinNumerosAqui"])
def test_contrasenas_debiles_son_rechazadas(password):
    usuario = Usuario("admin", "Administrador")
    with pytest.raises(ReglaNegocioError):
        usuario.establecer_password(password)
    assert usuario.password_hash is None


def test_rol_invalido():
    with pytest.raises(ReglaNegocioError):
        Usuario("admin", "Administrador", "SuperUsuario")


def test_solo_un_administrador_activo_puede_evaluar_solicitudes():
    assert Usuario("a", "Administrador", Usuario.ROL_ADMINISTRADOR).puede_evaluar_solicitudes()
    assert not Usuario("b", "Consulta", Usuario.ROL_CONSULTA).puede_evaluar_solicitudes()
    assert not Usuario("c", "Inactivo", Usuario.ROL_ADMINISTRADOR, activo=False).puede_evaluar_solicitudes()


@pytest.mark.parametrize("nombre, valido", [("admin", True), ("maria.lopez", True), ("ab", False), ("con espacio", False)])
def test_validar_nombre_de_usuario(nombre, valido):
    errores = Usuario(nombre, "Nombre Completo").validar()
    assert ("usuario" not in errores) == valido
