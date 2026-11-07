"""Pruebas del registro público (controlador + vista), sección 19 de la guía.

Usan un repositorio en memoria; las pruebas contra SQL Server real están en
test_integracion_sqlserver.py.
"""
from tests.conftest import crear_colaborador


def test_el_sitio_lleva_al_formulario_quiero_colaborar(cliente):
    """Sección 15 de la guía: la persona entra al sitio y elige «Quiero colaborar»."""
    html = cliente.get("/").get_data(as_text=True)
    assert 'href="/registro"' in html
    assert "Quiero colaborar" in html


def test_formulario_muestra_las_areas_de_la_base_de_datos(cliente, repositorio):
    respuesta = cliente.get("/registro")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "¡Queremos conocerte!" in html
    for area in repositorio.areas:
        assert area.nombre in html
    assert 'name="csrf_token"' in html
    assert "validaciones.js" in html


def test_enviar_formulario_vacio_muestra_errores(cliente, repositorio):
    respuesta = cliente.post("/registro", data={})
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    assert "El nombre es obligatorio." in html
    assert "Debes seleccionar un país." in html
    assert "Selecciona al menos un área de colaboración." in html
    assert not repositorio.colaboradores


def test_correo_incorrecto_es_rechazado(cliente, datos_validos, repositorio):
    datos_validos["correo"] = "correo-sin-arroba"
    respuesta = cliente.post("/registro", data=datos_validos)
    assert respuesta.status_code == 400
    assert "Ingresa un correo electrónico válido." in respuesta.get_data(as_text=True)
    assert not repositorio.colaboradores


def test_no_seleccionar_areas_solicita_al_menos_una(cliente, datos_validos, repositorio):
    del datos_validos["areas"]
    respuesta = cliente.post("/registro", data=datos_validos)
    assert respuesta.status_code == 400
    assert "Selecciona al menos un área de colaboración." in respuesta.get_data(as_text=True)
    assert not repositorio.colaboradores


def test_no_aceptar_privacidad_impide_el_envio(cliente, datos_validos, repositorio):
    del datos_validos["privacidad"]
    respuesta = cliente.post("/registro", data=datos_validos)
    assert respuesta.status_code == 400
    assert "Debes aceptar la política de privacidad" in respuesta.get_data(as_text=True)
    assert not repositorio.colaboradores


def test_area_inexistente_es_rechazada(cliente, datos_validos, repositorio):
    datos_validos["areas"] = ["1", "99"]
    respuesta = cliente.post("/registro", data=datos_validos)
    assert respuesta.status_code == 400
    assert not repositorio.colaboradores


def test_informacion_correcta_se_guarda_y_muestra_confirmacion(cliente, datos_validos, repositorio):
    respuesta = cliente.post("/registro", data=datos_validos)
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/registro/confirmacion")

    guardado = repositorio.colaboradores[1]
    assert guardado.nombre == "Ana Sofía Martínez"
    assert guardado.areas == [1, 3]
    assert guardado.nombres_areas == ["Voluntariado presencial", "Apoyo educativo"]
    assert guardado.estado == "Pendiente"

    confirmacion = cliente.get("/registro/confirmacion").get_data(as_text=True)
    assert "¡Gracias, Ana!" in confirmacion
    assert "an**********@example.com" in confirmacion


def test_la_confirmacion_solo_se_muestra_una_vez(cliente, datos_validos):
    cliente.post("/registro", data=datos_validos)
    assert cliente.get("/registro/confirmacion").status_code == 200
    segunda = cliente.get("/registro/confirmacion")
    assert segunda.status_code == 302


def test_confirmacion_sin_registro_redirige_al_formulario(cliente):
    respuesta = cliente.get("/registro/confirmacion")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/registro")


def test_correo_duplicado_informa_que_ya_existe(cliente, datos_validos, repositorio):
    repositorio.guardar(crear_colaborador(correo="ana.martinez@example.com"))
    datos_validos["correo"] = "ANA.Martinez@example.com"
    respuesta = cliente.post("/registro", data=datos_validos)
    assert respuesta.status_code == 409
    assert "Ya existe una solicitud registrada con este correo electrónico." in respuesta.get_data(as_text=True)
    assert len(repositorio.colaboradores) == 1


def test_los_datos_escritos_se_conservan_si_hay_errores(cliente, datos_validos):
    datos_validos["correo"] = "incorrecto"
    html = cliente.post("/registro", data=datos_validos).get_data(as_text=True)
    assert 'value="Ana Sofía Martínez"' in html
    assert "Quiero apoyar en actividades educativas con los niños." in html


def test_el_html_enviado_por_el_usuario_se_escapa(cliente, datos_validos):
    datos_validos["nombre"] = '<script>alert("x")</script>'
    html = cliente.post("/registro", data=datos_validos).get_data(as_text=True)
    assert '<script>alert("x")</script>' not in html
    assert "&lt;script&gt;" in html


def test_base_de_datos_caida_al_abrir_el_formulario(cliente, repositorio):
    repositorio.disponible = False
    respuesta = cliente.get("/registro")
    assert respuesta.status_code == 503
    assert "Servicio no disponible" in respuesta.get_data(as_text=True)


def test_base_de_datos_caida_al_guardar_conserva_los_datos(cliente, datos_validos, repositorio):
    areas = repositorio.obtener_areas_activas()
    repositorio.obtener_areas_activas = lambda: areas      # las áreas sí cargan...
    repositorio.disponible = False                          # ...pero guardar falla
    respuesta = cliente.post("/registro", data=datos_validos)
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 503
    assert "No pudimos guardar tu solicitud" in html
    assert 'value="Ana Sofía Martínez"' in html


def test_politica_de_privacidad(cliente):
    respuesta = cliente.get("/privacidad")
    assert respuesta.status_code == 200
    assert "Política de privacidad" in respuesta.get_data(as_text=True)


def test_pagina_no_encontrada(cliente):
    respuesta = cliente.get("/no-existe")
    assert respuesta.status_code == 404
    assert "Página no encontrada" in respuesta.get_data(as_text=True)


def test_cabeceras_de_seguridad(cliente):
    respuesta = cliente.get("/registro")
    assert "default-src 'self'" in respuesta.headers["Content-Security-Policy"]
    assert respuesta.headers["X-Frame-Options"] == "DENY"
    assert respuesta.headers["X-Content-Type-Options"] == "nosniff"


def test_la_cookie_de_sesion_es_httponly(cliente, datos_validos):
    respuesta = cliente.post("/registro", data=datos_validos)
    cookie = respuesta.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
