"""Controlador del sitio institucional (Blueprint "sitio").

Muestra las páginas públicas de la Fundación con el contenido de
contenido/sitio.json y recibe los mensajes del formulario de contacto.
"""
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from database import ErrorBaseDatos
from models.mensaje import MensajeContacto

sitio_bp = Blueprint("sitio", __name__)


def _contenido():
    return current_app.extensions["contenido"]


def _mensajes():
    return current_app.extensions["repositorios"]["mensajes"]


@sitio_bp.route("/")
def inicio():
    contenido = _contenido()
    return render_template(
        "sitio/inicio.html",
        diapositivas=contenido.diapositivas(),
        pilares=contenido.pilares(),
        programas=[p for p in contenido.programas() if p.imagen_inicio][:4],
        testimonios=contenido.testimonios(),
        equipo=contenido.equipo(),
        noticias=contenido.noticias()[:3],
    )


@sitio_bp.route("/nosotros")
def nosotros():
    contenido = _contenido()
    return render_template(
        "sitio/nosotros.html",
        cifras=contenido.cifras(),
        testimonios=contenido.testimonios(),
        equipo=contenido.equipo(),
    )


@sitio_bp.route("/programas")
def programas():
    return render_template("sitio/programas.html", programas=_contenido().programas())


@sitio_bp.route("/programas/<slug>")
def programa(slug: str):
    contenido = _contenido()
    programa = contenido.programa(slug)
    if programa is None:
        abort(404)
    return render_template(
        "sitio/programa.html",
        programa=programa,
        preguntas=contenido.preguntas_programa(),
        otros=[p for p in contenido.programas() if p.slug != slug],
    )


@sitio_bp.route("/equipo")
def equipo():
    return render_template("sitio/equipo.html", equipo=_contenido().equipo())


@sitio_bp.route("/eventos")
def eventos():
    return render_template("sitio/eventos.html", eventos=_contenido().eventos())


@sitio_bp.route("/eventos/<slug>")
def evento(slug: str):
    evento = _contenido().evento(slug)
    if evento is None:
        abort(404)
    return render_template("sitio/evento.html", evento=evento)


@sitio_bp.route("/galeria")
def galeria():
    return render_template("sitio/galeria.html", imagenes=_contenido().galeria())


@sitio_bp.route("/noticias")
def noticias():
    return render_template("sitio/noticias.html", noticias=_contenido().noticias())


@sitio_bp.route("/noticias/<slug>")
def noticia(slug: str):
    contenido = _contenido()
    noticia = contenido.noticia(slug)
    if noticia is None:
        abort(404)
    recientes = [n for n in contenido.noticias() if n.slug != slug][:3]
    return render_template("sitio/noticia.html", noticia=noticia, recientes=recientes)


@sitio_bp.route("/apoyanos")
def apoyanos():
    return render_template("sitio/apoyanos.html", formas=_contenido().formas_apoyo())


@sitio_bp.route("/preguntas-frecuentes")
def preguntas_frecuentes():
    return render_template("sitio/preguntas.html", preguntas=_contenido().preguntas_frecuentes())


@sitio_bp.route("/contacto", methods=["GET", "POST"])
def contacto():
    if request.method == "GET":
        # Permite enlaces como /contacto?asunto=donacion para preseleccionar el asunto
        asunto = request.args.get("asunto", "")
        mensaje = MensajeContacto(asunto=asunto if asunto in MensajeContacto.ASUNTOS else "")
        return render_template("sitio/contacto.html", mensaje=mensaje, errores={}, reglas=MensajeContacto)

    mensaje = MensajeContacto(
        nombre=request.form.get("nombre", ""),
        correo=request.form.get("correo", ""),
        telefono=request.form.get("telefono", ""),
        asunto=request.form.get("asunto", ""),
        mensaje=request.form.get("mensaje", ""),
        acepta_privacidad=request.form.get("privacidad") == "1",
    )
    errores = mensaje.validar()
    if not errores:
        try:
            _mensajes().guardar(mensaje)
        except ErrorBaseDatos:
            errores["general"] = "No pudimos enviar tu mensaje en este momento. Inténtalo de nuevo en unos minutos."
            codigo = 503
        else:
            flash(f"¡Gracias, {mensaje.primer_nombre}! Recibimos tu mensaje y te responderemos pronto.", "exito")
            return redirect(url_for("sitio.contacto") + "#formulario-contacto")
    else:
        codigo = 400

    return render_template("sitio/contacto.html", mensaje=mensaje, errores=errores, reglas=MensajeContacto), codigo
