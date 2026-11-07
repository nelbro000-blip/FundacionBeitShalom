"""Controlador del panel administrativo (Blueprint "admin").

Todas las rutas, excepto el inicio de sesión, exigen una sesión iniciada.
Las acciones que modifican solicitudes exigen además el rol Administrador.
"""
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from database import ErrorBaseDatos
from models.colaborador import Colaborador
from models.errores import ReglaNegocioError
from models.usuario import Usuario
from repositories.colaborador_repository import FiltrosBusqueda
from services.autenticacion import destino_seguro, login_requerido, rol_requerido
from services.exportador_excel import ExportadorExcel

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _colaboradores():
    return current_app.extensions["repositorios"]["colaboradores"]


def _usuarios():
    return current_app.extensions["repositorios"]["usuarios"]


def _limitador():
    return current_app.extensions["limitador_login"]


def _mensajes():
    return current_app.extensions["repositorios"]["mensajes"]


@admin_bp.context_processor
def datos_del_panel():
    """Número de mensajes sin leer para el menú del panel."""
    if g.get("usuario") is None:
        return {}
    try:
        return {"mensajes_sin_leer": _mensajes().contar_no_leidos()}
    except ErrorBaseDatos:
        return {"mensajes_sin_leer": 0}


@admin_bp.before_request
def cargar_usuario_actual():
    """En cada solicitud recupera al usuario de la sesión y comprueba que siga activo."""
    g.usuario = None
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return
    usuario = _usuarios().obtener_por_id(usuario_id)
    if usuario is not None and usuario.activo:
        g.usuario = usuario
    else:
        session.clear()


@admin_bp.after_request
def evitar_cache(respuesta):
    """Los datos personales no deben quedar guardados en la caché del navegador."""
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


# ----------------------------------------------------------------------
# Inicio y cierre de sesión
# ----------------------------------------------------------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario is not None:
        return redirect(url_for("admin.dashboard"))

    siguiente = destino_seguro(request.args.get("siguiente"))
    if request.method == "GET":
        return render_template("admin/login.html", nombre_usuario="", siguiente=siguiente)

    nombre_usuario = request.form.get("usuario", "").strip().lower()[:50]
    password = request.form.get("password", "")
    clave = f"{request.remote_addr}|{nombre_usuario}"
    limitador = _limitador()

    if limitador.esta_bloqueado(clave):
        minutos = current_app.config["MINUTOS_BLOQUEO_LOGIN"]
        flash(f"Demasiados intentos fallidos. Espera {minutos} minutos e inténtalo de nuevo.", "error")
        return render_template("admin/login.html", nombre_usuario=nombre_usuario, siguiente=siguiente), 429

    usuario = _usuarios().obtener_por_usuario(nombre_usuario) if nombre_usuario else None
    if usuario is None:
        Usuario.simular_verificacion(password)
        credenciales_validas = False
    else:
        credenciales_validas = usuario.verificar_password(password) and usuario.activo

    if not credenciales_validas:
        limitador.registrar_fallo(clave)
        flash("Usuario o contraseña incorrectos.", "error")
        return render_template("admin/login.html", nombre_usuario=nombre_usuario, siguiente=siguiente), 401

    limitador.reiniciar(clave)
    session.clear()             # sesión nueva: evita la fijación de sesión
    session.permanent = True    # expira según PERMANENT_SESSION_LIFETIME (config.py)
    session["usuario_id"] = usuario.id
    _usuarios().registrar_acceso(usuario.id)
    flash(f"Bienvenido(a), {usuario.nombre_completo}.", "exito")
    return redirect(siguiente or url_for("admin.dashboard"))


@admin_bp.post("/logout")
def logout():
    session.clear()
    flash("Cerraste sesión correctamente.", "exito")
    return redirect(url_for("admin.login"))


# ----------------------------------------------------------------------
# Dashboard, listado y detalle
# ----------------------------------------------------------------------
@admin_bp.get("/")
@login_requerido
def dashboard():
    estadisticas = _colaboradores().obtener_estadisticas()
    return render_template("admin/dashboard.html", estadisticas=estadisticas)


@admin_bp.get("/colaboradores")
@login_requerido
def listado():
    repositorio = _colaboradores()
    filtros = FiltrosBusqueda.desde_argumentos(request.args)
    pagina = request.args.get("pagina", 1, type=int)
    resultado = repositorio.buscar(
        filtros, pagina=pagina, por_pagina=current_app.config["REGISTROS_POR_PAGINA"]
    )
    return render_template(
        "admin/colaboradores.html",
        resultado=resultado,
        filtros=filtros,
        paises=repositorio.paises_registrados(),
        areas=repositorio.obtener_areas(),
        estados=Colaborador.ESTADOS,
    )


def _mostrar_detalle(id_colaborador: int, comentario: str = "", codigo: int = 200):
    repositorio = _colaboradores()
    colaborador = repositorio.obtener_por_id(id_colaborador)
    if colaborador is None:
        abort(404)
    return (
        render_template(
            "admin/detalle.html",
            colaborador=colaborador,
            historial=repositorio.obtener_historial(id_colaborador),
            estados=Colaborador.ESTADOS,
            reglas=Colaborador,
            comentario=comentario,
        ),
        codigo,
    )


@admin_bp.get("/colaboradores/<int:id_colaborador>")
@login_requerido
def detalle(id_colaborador: int):
    return _mostrar_detalle(id_colaborador)


# ----------------------------------------------------------------------
# Evaluación: aprobar, rechazar o cambiar el estado (solo Administrador)
# ----------------------------------------------------------------------
@admin_bp.post("/colaboradores/<int:id_colaborador>/estado")
@rol_requerido(Usuario.ROL_ADMINISTRADOR)
def cambiar_estado(id_colaborador: int):
    repositorio = _colaboradores()
    colaborador = repositorio.obtener_por_id(id_colaborador)
    if colaborador is None:
        abort(404)

    nuevo_estado = request.form.get("estado", "")
    comentario = request.form.get("comentario", "").strip()
    try:
        estado_anterior = colaborador.cambiar_estado(nuevo_estado, comentario)
        repositorio.actualizar_estado(colaborador, estado_anterior, g.usuario.id, comentario)
    except ReglaNegocioError as error:
        flash(str(error), "error")
        return _mostrar_detalle(id_colaborador, comentario=comentario, codigo=400)

    flash(f"La solicitud de {colaborador.nombre} ahora está «{colaborador.estado}».", "exito")
    return redirect(url_for("admin.detalle", id_colaborador=id_colaborador))


@admin_bp.post("/colaboradores/<int:id_colaborador>/eliminar")
@rol_requerido(Usuario.ROL_ADMINISTRADOR)
def eliminar(id_colaborador: int):
    repositorio = _colaboradores()
    colaborador = repositorio.obtener_por_id(id_colaborador)
    if colaborador is None:
        abort(404)
    repositorio.eliminar(id_colaborador)
    flash(f"Se eliminaron todos los datos de {colaborador.nombre}.", "exito")
    return redirect(url_for("admin.listado"))


# ----------------------------------------------------------------------
# Mensajes de la página de contacto
# ----------------------------------------------------------------------
@admin_bp.get("/mensajes")
@login_requerido
def mensajes():
    solo_no_leidos = request.args.get("filtro") == "no-leidos"
    return render_template(
        "admin/mensajes.html",
        mensajes=_mensajes().listar(solo_no_leidos=solo_no_leidos),
        solo_no_leidos=solo_no_leidos,
    )


@admin_bp.get("/mensajes/<int:id_mensaje>")
@login_requerido
def mensaje(id_mensaje: int):
    repositorio = _mensajes()
    mensaje = repositorio.obtener_por_id(id_mensaje)
    if mensaje is None:
        abort(404)
    if not mensaje.leido:
        repositorio.marcar_leido(id_mensaje)
        mensaje.marcar_leido()
    return render_template("admin/mensaje.html", mensaje=mensaje)


@admin_bp.post("/mensajes/<int:id_mensaje>/eliminar")
@rol_requerido(Usuario.ROL_ADMINISTRADOR)
def eliminar_mensaje(id_mensaje: int):
    if not _mensajes().eliminar(id_mensaje):
        abort(404)
    flash("Mensaje eliminado.", "exito")
    return redirect(url_for("admin.mensajes"))


# ----------------------------------------------------------------------
# Exportación a Excel
# ----------------------------------------------------------------------
def _describir_filtros(filtros: FiltrosBusqueda, areas) -> str:
    partes = []
    if filtros.texto:
        partes.append(f"búsqueda «{filtros.texto}»")
    if filtros.pais:
        partes.append(f"país {filtros.pais}")
    if filtros.area_id:
        nombre_area = next((area.nombre for area in areas if area.id == filtros.area_id), filtros.area_id)
        partes.append(f"área {nombre_area}")
    if filtros.estado:
        partes.append(f"estado {filtros.estado}")
    return ", ".join(partes)


@admin_bp.get("/exportar")
@login_requerido
def exportar():
    repositorio = _colaboradores()
    filtros = FiltrosBusqueda.desde_argumentos(request.args)
    colaboradores = repositorio.listar(filtros)
    descripcion = _describir_filtros(filtros, repositorio.obtener_areas())
    archivo = ExportadorExcel().generar(colaboradores, descripcion)
    return send_file(
        archivo,
        mimetype=TIPO_EXCEL,
        as_attachment=True,
        download_name=f"colaboradores_{datetime.now():%Y%m%d_%H%M}.xlsx",
    )
