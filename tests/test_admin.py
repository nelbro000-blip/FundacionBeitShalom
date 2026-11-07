"""Pruebas del módulo administrativo (sección 16 de la guía)."""
from io import BytesIO

from openpyxl import load_workbook

from tests.conftest import PASSWORD_PRUEBA, crear_colaborador, iniciar_sesion


def cargar_datos(repositorio):
    repositorio.guardar(crear_colaborador(nombre="Ana Martínez", correo="ana@example.com", pais="El Salvador", areas=[1, 3]))
    repositorio.guardar(crear_colaborador(nombre="Luis Gómez", correo="luis@example.com", pais="México", areas=[5]))
    repositorio.guardar(crear_colaborador(
        nombre="Eva Ruiz", correo="eva@example.com", pais="El Salvador", areas=[7],
        motivacion='=HYPERLINK("http://sitio-malicioso.example","clic")',
    ))


# ---------------------------------------------------------------- acceso
def test_el_panel_exige_iniciar_sesion(cliente):
    for ruta in ("/admin/", "/admin/colaboradores", "/admin/colaboradores/1", "/admin/exportar"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 302
        assert "/admin/login" in respuesta.headers["Location"]


def test_contrasena_incorrecta(cliente):
    respuesta = iniciar_sesion(cliente, password="Incorrecta123")
    assert respuesta.status_code == 401
    assert "Usuario o contraseña incorrectos." in respuesta.get_data(as_text=True)


def test_usuario_inexistente_recibe_el_mismo_mensaje(cliente):
    respuesta = iniciar_sesion(cliente, usuario="nadie")
    assert respuesta.status_code == 401
    assert "Usuario o contraseña incorrectos." in respuesta.get_data(as_text=True)


def test_inicio_de_sesion_correcto(cliente, repositorio_usuarios):
    respuesta = iniciar_sesion(cliente)
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/admin/")
    assert repositorio_usuarios.accesos == [1]
    assert cliente.get("/admin/").status_code == 200


def test_bloqueo_tras_varios_intentos_fallidos(cliente):
    for _ in range(5):
        assert iniciar_sesion(cliente, password="Incorrecta123").status_code == 401
    # Aun con la contraseña correcta queda bloqueado temporalmente
    respuesta = iniciar_sesion(cliente, password=PASSWORD_PRUEBA)
    assert respuesta.status_code == 429


def test_redireccion_solo_a_rutas_internas(cliente):
    respuesta = cliente.post(
        "/admin/login?siguiente=https://sitio-malicioso.example",
        data={"usuario": "admin", "password": PASSWORD_PRUEBA},
    )
    assert respuesta.headers["Location"].endswith("/admin/")

    cliente.post("/admin/logout")
    respuesta = cliente.post(
        "/admin/login?siguiente=/admin/colaboradores",
        data={"usuario": "admin", "password": PASSWORD_PRUEBA},
    )
    assert respuesta.headers["Location"].endswith("/admin/colaboradores")


def test_cerrar_sesion(cliente):
    iniciar_sesion(cliente)
    assert cliente.get("/admin/logout").status_code == 405      # solo por POST
    assert cliente.post("/admin/logout").status_code == 302
    assert cliente.get("/admin/").status_code == 302


def test_usuario_desactivado_pierde_el_acceso(cliente, repositorio_usuarios):
    iniciar_sesion(cliente)
    repositorio_usuarios.usuarios[1]._activo = False
    assert cliente.get("/admin/").status_code == 302


def test_las_paginas_del_panel_no_se_guardan_en_cache(cliente):
    iniciar_sesion(cliente)
    assert cliente.get("/admin/").headers["Cache-Control"] == "no-store"


# ------------------------------------------------- dashboard y listado
def test_dashboard_muestra_totales_y_estadisticas(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente)
    html = cliente.get("/admin/").get_data(as_text=True)
    assert "Total de solicitudes" in html
    assert "Solicitudes por área de colaboración" in html
    assert "Registros por mes" in html
    assert "Ana Martínez" in html


def test_dashboard_sin_solicitudes(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/admin/")
    assert respuesta.status_code == 200
    assert "Aún no hay solicitudes registradas." in respuesta.get_data(as_text=True)


def test_listado_con_busqueda_y_filtros(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente)
    html = cliente.get("/admin/colaboradores?q=ana&pais=El+Salvador&area=3&estado=Pendiente").get_data(as_text=True)
    filtros = repositorio.ultimos_filtros
    assert (filtros.texto, filtros.pais, filtros.area_id, filtros.estado) == ("ana", "El Salvador", 3, "Pendiente")
    assert "Ana Martínez" in html
    assert "Luis Gómez" not in html


def test_filtros_con_valores_no_validos_se_ignoran(cliente, repositorio):
    iniciar_sesion(cliente)
    cliente.get("/admin/colaboradores?estado=Inventado&area=abc")
    assert repositorio.ultimos_filtros.estado == ""
    assert repositorio.ultimos_filtros.area_id is None


def test_detalle_de_un_colaborador(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente)
    html = cliente.get("/admin/colaboradores/1").get_data(as_text=True)
    assert "Ana Martínez" in html
    assert "Voluntariado presencial" in html
    assert "Apoyo educativo" in html


def test_detalle_inexistente(cliente):
    iniciar_sesion(cliente)
    assert cliente.get("/admin/colaboradores/999").status_code == 404


# ------------------------------------------- aprobación y rechazo
def test_aprobar_solicitud_registra_el_historial(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente)
    respuesta = cliente.post("/admin/colaboradores/1/estado", data={"estado": "Aprobado", "comentario": "Perfil adecuado"})
    assert respuesta.status_code == 302
    assert repositorio.colaboradores[1].estado == "Aprobado"
    cambio = repositorio.historial[1][0]
    assert (cambio.estado_anterior, cambio.estado_nuevo, cambio.comentario) == ("Pendiente", "Aprobado", "Perfil adecuado")


def test_rechazo_sin_motivo_no_se_guarda(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente)
    respuesta = cliente.post("/admin/colaboradores/1/estado", data={"estado": "Rechazado", "comentario": ""})
    assert respuesta.status_code == 400
    assert "Indica el motivo del rechazo" in respuesta.get_data(as_text=True)
    assert repositorio.colaboradores[1].estado == "Pendiente"


def test_rechazo_con_motivo(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente)
    cliente.post("/admin/colaboradores/1/estado", data={"estado": "Rechazado", "comentario": "No hay actividades en su zona."})
    assert repositorio.colaboradores[1].estado == "Rechazado"


def test_rol_consulta_no_puede_cambiar_estados_ni_eliminar(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente, usuario="consulta")
    assert cliente.post("/admin/colaboradores/1/estado", data={"estado": "Aprobado"}).status_code == 403
    assert cliente.post("/admin/colaboradores/1/eliminar").status_code == 403
    assert repositorio.colaboradores[1].estado == "Pendiente"
    html = cliente.get("/admin/colaboradores/1").get_data(as_text=True)
    assert "no cambiar el estado" in html
    assert "Eliminar datos" not in html


def test_eliminar_todos_los_datos_de_una_persona(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente)
    respuesta = cliente.post("/admin/colaboradores/2/eliminar")
    assert respuesta.status_code == 302
    assert 2 not in repositorio.colaboradores


# ------------------------------------------------------- exportación
def test_exportar_a_excel(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente, usuario="consulta")
    respuesta = cliente.get("/admin/exportar?pais=El+Salvador")
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment" in respuesta.headers["Content-Disposition"]

    libro = load_workbook(BytesIO(respuesta.data))
    hoja = libro["Colaboradores"]
    nombres = [hoja.cell(row=fila, column=3).value for fila in range(5, hoja.max_row + 1)]
    assert sorted(nombres) == ["Ana Martínez", "Eva Ruiz"]
    assert "Resumen" in libro.sheetnames


def test_el_excel_no_ejecuta_formulas_escritas_por_usuarios(cliente, repositorio):
    cargar_datos(repositorio)
    iniciar_sesion(cliente)
    libro = load_workbook(BytesIO(cliente.get("/admin/exportar").data))
    hoja = libro["Colaboradores"]
    celdas = [hoja.cell(row=fila, column=10) for fila in range(5, hoja.max_row + 1)]
    peligrosa = next(c for c in celdas if c.value and str(c.value).startswith("=HYPERLINK"))
    assert peligrosa.data_type == "s"       # texto, no fórmula
