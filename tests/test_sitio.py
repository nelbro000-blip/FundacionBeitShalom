"""Pruebas del sitio institucional (plantilla Kidearn integrada con Flask)."""
import re
from pathlib import Path

import pytest

from app import ARCHIVO_CONTENIDO
from models.mensaje import MensajeContacto
from repositories.contenido_repository import ContenidoRepository
from tests.conftest import iniciar_sesion

CARPETA_STATIC = Path(__file__).resolve().parent.parent / "static"
contenido = ContenidoRepository(ARCHIVO_CONTENIDO)

PAGINAS = [
    "/",
    "/nosotros",
    "/programas",
    f"/programas/{contenido.programas()[0].slug}",
    "/equipo",
    "/eventos",
    f"/eventos/{contenido.eventos()[0].slug}",
    "/galeria",
    "/noticias",
    f"/noticias/{contenido.noticias()[0].slug}",
    "/apoyanos",
    "/preguntas-frecuentes",
    "/contacto",
    "/privacidad",
    "/registro",
    "/admin/login",
]


@pytest.mark.parametrize("ruta", PAGINAS)
def test_todas_las_paginas_cargan(cliente, ruta):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)
    assert "Fundación Internacional Beit Shalom" in html     # encabezado y pie comunes
    assert "kidearn.css" in html


@pytest.mark.parametrize("ruta", PAGINAS)
def test_los_archivos_estaticos_de_cada_pagina_existen(cliente, ruta):
    """Ninguna imagen, hoja de estilos o script enlazado debe dar error 404."""
    html = cliente.get(ruta).get_data(as_text=True)
    archivos = set(re.findall(r"/static/([^\"')\s?#]+)", html))
    assert archivos
    faltantes = [archivo for archivo in archivos if not (CARPETA_STATIC / archivo).exists()]
    assert faltantes == []


@pytest.mark.parametrize("ruta", ["/programas/no-existe", "/eventos/no-existe", "/noticias/no-existe"])
def test_detalle_inexistente_da_404(cliente, ruta):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 404
    assert "Página no encontrada" in respuesta.get_data(as_text=True)


def test_inicio_muestra_el_contenido_de_la_fundacion(cliente):
    html = cliente.get("/").get_data(as_text=True)
    assert "Descubre tus talentos y vive con propósito" in html
    assert "Formación ética y religiosa" in html
    assert "Néstor Castillo" in html
    assert contenido.noticias()[0].titulo in html


def test_el_menu_marca_la_pagina_actual(cliente):
    html = cliente.get("/programas").get_data(as_text=True)
    assert re.search(r'<li class="dropdown current">\s*<a href="/programas">Programas</a>', html)


def test_todos_los_programas_tienen_su_pagina(cliente):
    for programa in contenido.programas():
        html = cliente.get(f"/programas/{programa.slug}").get_data(as_text=True)
        assert programa.descripcion in html
        assert "Inscribir a mi hijo o hija" in html


def test_contenido_sin_slugs_repetidos():
    for coleccion in (contenido.programas(), contenido.eventos(), contenido.noticias()):
        slugs = [elemento.slug for elemento in coleccion]
        assert len(slugs) == len(set(slugs))


def test_noticias_de_la_mas_reciente_a_la_mas_antigua():
    fechas = [noticia.fecha for noticia in contenido.noticias()]
    assert fechas == sorted(fechas, reverse=True)


def test_la_politica_de_seguridad_permite_la_plantilla_y_bloquea_scripts_externos(cliente):
    politica = cliente.get("/").headers["Content-Security-Policy"]
    assert "script-src 'self'" in politica
    assert "https://fonts.googleapis.com" in politica
    assert "https://www.youtube.com" in politica


# ------------------------------------------------------- contacto
def datos_contacto(**cambios):
    datos = {
        "nombre": "Luis Gómez",
        "correo": "luis@example.com",
        "telefono": "",
        "asunto": "voluntariado",
        "mensaje": "Me gustaría saber cómo puedo ayudar los sábados.",
        "privacidad": "1",
    }
    datos.update(cambios)
    return datos


def test_contacto_preselecciona_el_asunto(cliente):
    html = cliente.get("/contacto?asunto=donacion").get_data(as_text=True)
    assert '<option value="donacion" selected>' in html


def test_mensaje_de_contacto_correcto_se_guarda(cliente, repositorio_mensajes):
    respuesta = cliente.post("/contacto", data=datos_contacto(), follow_redirects=True)
    assert respuesta.status_code == 200
    assert "Recibimos tu mensaje" in respuesta.get_data(as_text=True)
    guardado = repositorio_mensajes.mensajes[1]
    assert guardado.asunto == "voluntariado"
    assert not guardado.leido


@pytest.mark.parametrize("campo, valor, texto", [
    ("correo", "sin-arroba", "Ingresa un correo electrónico válido."),
    ("asunto", "inventado", "Selecciona el asunto de tu mensaje."),
    ("mensaje", "Hola", "Escribe tu mensaje (mínimo 10 caracteres)."),
    ("privacidad", "", "Debes aceptar la política de privacidad"),
])
def test_mensaje_de_contacto_con_errores(cliente, repositorio_mensajes, campo, valor, texto):
    respuesta = cliente.post("/contacto", data=datos_contacto(**{campo: valor}))
    assert respuesta.status_code == 400
    assert texto in respuesta.get_data(as_text=True)
    assert not repositorio_mensajes.mensajes


def test_contacto_con_base_de_datos_caida(cliente, repositorio_mensajes):
    repositorio_mensajes.disponible = False
    respuesta = cliente.post("/contacto", data=datos_contacto())
    assert respuesta.status_code == 503
    assert "No pudimos enviar tu mensaje" in respuesta.get_data(as_text=True)


def test_mensaje_hereda_las_reglas_de_persona():
    mensaje = MensajeContacto(nombre="Ana", correo="ana@example.com", asunto="otro",
                              mensaje="Un mensaje de prueba.", acepta_privacidad=True)
    assert mensaje.es_valido()                      # "Ana" basta: NOMBRE_MIN = 3
    assert mensaje.asunto_texto == "Otro asunto"


# ------------------------------------------- mensajes en el panel
def test_el_panel_muestra_y_marca_como_leidos_los_mensajes(cliente, repositorio_mensajes):
    cliente.post("/contacto", data=datos_contacto())
    iniciar_sesion(cliente)
    panel = cliente.get("/admin/").get_data(as_text=True)
    assert "mensaje de contacto sin leer" in panel
    assert "Luis Gómez" in cliente.get("/admin/mensajes").get_data(as_text=True)
    detalle = cliente.get("/admin/mensajes/1").get_data(as_text=True)
    assert "Me gustaría saber cómo puedo ayudar" in detalle
    assert repositorio_mensajes.mensajes[1].leido


def test_solo_el_administrador_elimina_mensajes(cliente, repositorio_mensajes):
    cliente.post("/contacto", data=datos_contacto())
    iniciar_sesion(cliente, usuario="consulta")
    assert cliente.post("/admin/mensajes/1/eliminar").status_code == 403
    cliente.post("/admin/logout")
    iniciar_sesion(cliente)
    assert cliente.post("/admin/mensajes/1/eliminar").status_code == 302
    assert not repositorio_mensajes.mensajes


def test_los_mensajes_requieren_iniciar_sesion(cliente):
    assert cliente.get("/admin/mensajes").status_code == 302
