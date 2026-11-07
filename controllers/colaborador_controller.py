"""Controlador del registro público (Blueprint "colaborador").

Recibe las solicitudes del navegador, usa el modelo Colaborador para
aplicar las reglas del negocio y el repositorio para guardar en SQL Server.
Este archivo no contiene ninguna consulta SQL.
"""
from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from database import ErrorBaseDatos
from models.colaborador import Colaborador
from repositories.base_repository import RegistroDuplicadoError

colaborador_bp = Blueprint("colaborador", __name__)


def _repositorio():
    """Repositorio configurado en app.py (en las pruebas se usa uno en memoria)."""
    return current_app.extensions["repositorios"]["colaboradores"]


def _mostrar_formulario(colaborador, areas, errores=None, aviso=None, codigo=200):
    return (
        render_template(
            "registro.html",
            colaborador=colaborador,
            areas=areas,
            errores=errores or {},
            aviso=aviso,
            reglas=Colaborador,
        ),
        codigo,
    )


@colaborador_bp.route("/registro", methods=["GET", "POST"])
def registrar():
    repositorio = _repositorio()
    # Las áreas se leen de SQL Server: el formulario no depende de textos fijos
    areas = repositorio.obtener_areas_activas()

    if request.method == "GET":
        return _mostrar_formulario(Colaborador(), areas)

    # 1. Crear el objeto con los datos recibidos (la vista solo los recoge)
    colaborador = Colaborador(
        nombre=request.form.get("nombre", ""),
        pais=request.form.get("pais", ""),
        correo=request.form.get("correo", ""),
        telefono=request.form.get("telefono", ""),
        modalidad=request.form.get("modalidad", ""),
        disponibilidad=request.form.get("disponibilidad", ""),
        motivacion=request.form.get("motivacion", ""),
        areas=request.form.getlist("areas"),
        acepta_privacidad=request.form.get("privacidad") == "1",
    )

    # 2. Python vuelve a validar todo, aunque JavaScript ya lo haya hecho
    errores = colaborador.validar(areas_validas=[area.id for area in areas])
    if errores:
        return _mostrar_formulario(colaborador, areas, errores, codigo=400)

    # 3. El repositorio guarda los datos en SQL Server
    try:
        repositorio.guardar(colaborador)
    except RegistroDuplicadoError as error:
        return _mostrar_formulario(colaborador, areas, {"correo": str(error)}, codigo=409)
    except ErrorBaseDatos:
        aviso = "No pudimos guardar tu solicitud en este momento. Inténtalo de nuevo en unos minutos."
        return _mostrar_formulario(colaborador, areas, aviso=aviso, codigo=503)

    # 4. Patrón Post/Redirect/Get: recargar la confirmación no reenvía el formulario
    session["registro_confirmado"] = {
        "nombre": colaborador.primer_nombre,
        "correo": colaborador.correo_enmascarado,
    }
    return redirect(url_for("colaborador.confirmacion"))


@colaborador_bp.route("/registro/confirmacion")
def confirmacion():
    # Los datos se leen una sola vez: nadie puede consultar registros de otras personas
    datos = session.pop("registro_confirmado", None)
    if datos is None:
        return redirect(url_for("colaborador.registrar"))
    return render_template("confirmacion.html", datos=datos)


@colaborador_bp.route("/privacidad")
def privacidad():
    return render_template("privacidad.html")
