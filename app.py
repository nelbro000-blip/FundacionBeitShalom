"""Punto de entrada del sistema: inicializa Flask y registra los controladores.

Ejecutar en modo desarrollo:
    flask --app app run --debug
o bien:
    python app.py
"""
import secrets
from datetime import datetime, timedelta

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFError, CSRFProtect

from comandos import registrar_comandos
from config import DIRECTORIO_BASE, Config
from controllers.admin_controller import admin_bp
from controllers.colaborador_controller import colaborador_bp
from controllers.sitio_controller import sitio_bp
from database import BaseDatos, ErrorBaseDatos
from repositories.colaborador_repository import ColaboradorRepository
from repositories.contenido_repository import ContenidoRepository
from repositories.mensaje_repository import MensajeRepository
from repositories.usuario_repository import UsuarioRepository
from services.autenticacion import LimitadorIntentos

csrf = CSRFProtect()

# Política de seguridad de contenido (CSP). JavaScript solo se carga desde
# nuestro propio servidor (nunca en línea). Para la plantilla Kidearn se
# permiten estilos en línea (colores e imágenes de fondo), las tipografías de
# Google Fonts y los mapas y videos de Google y YouTube.
POLITICA_CONTENIDO = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com data:",
        "img-src 'self' data:",
        "frame-src https://www.google.com https://maps.google.com https://www.youtube.com https://www.youtube-nocookie.com",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

ARCHIVO_CONTENIDO = DIRECTORIO_BASE / "contenido" / "sitio.json"

CLASES_ESTADO = {
    "Pendiente": "pendiente",
    "En revisión": "revision",
    "Aprobado": "aprobado",
    "Rechazado": "rechazado",
}


def crear_app(
    configuracion=Config,
    repositorio_colaboradores=None,
    repositorio_usuarios=None,
    repositorio_mensajes=None,
) -> Flask:
    """Crea y configura la aplicación (patrón "fábrica de aplicaciones").

    Las pruebas automáticas envían repositorios en memoria para no depender
    de SQL Server; en uso normal se crean los repositorios reales.
    """
    app = Flask(__name__)
    app.config.from_object(configuracion)
    _asegurar_clave_secreta(app)

    base_datos = BaseDatos.desde_config(app.config)
    app.extensions["base_datos"] = base_datos
    app.extensions["repositorios"] = {
        "colaboradores": repositorio_colaboradores or ColaboradorRepository(base_datos),
        "usuarios": repositorio_usuarios or UsuarioRepository(base_datos),
        "mensajes": repositorio_mensajes or MensajeRepository(base_datos),
    }
    # Contenido institucional (programas, equipo, eventos...) en contenido/sitio.json
    app.extensions["contenido"] = ContenidoRepository(ARCHIVO_CONTENIDO)
    app.extensions["limitador_login"] = LimitadorIntentos(
        app.config["MAX_INTENTOS_LOGIN"], timedelta(minutes=app.config["MINUTOS_BLOQUEO_LOGIN"])
    )

    csrf.init_app(app)
    app.register_blueprint(sitio_bp)
    app.register_blueprint(colaborador_bp)
    app.register_blueprint(admin_bp)

    _registrar_filtros(app)
    _registrar_errores(app)
    _registrar_cabeceras_seguridad(app)
    registrar_comandos(app)
    return app


def _asegurar_clave_secreta(app: Flask) -> None:
    if not app.config.get("SECRET_KEY"):
        app.logger.warning(
            "SECRET_KEY no está definida en .env: se usará una clave temporal "
            "y las sesiones se cerrarán al reiniciar el servidor."
        )
        app.config["SECRET_KEY"] = secrets.token_hex(32)


def _registrar_filtros(app: Flask) -> None:
    """Filtros de Jinja2 para dar formato a los datos en las vistas."""

    @app.template_filter("fecha")
    def formato_fecha(valor, con_hora=True):
        if not valor:
            return "—"
        return valor.strftime("%d/%m/%Y %H:%M" if con_hora else "%d/%m/%Y")

    @app.template_filter("porcentaje")
    def porcentaje(valor, total):
        return round(valor * 100 / total) if total else 0

    @app.template_filter("clase_estado")
    def clase_estado(estado):
        return CLASES_ESTADO.get(estado, "pendiente")

    @app.context_processor
    def datos_globales():
        """Datos disponibles en todas las plantillas (encabezado, menú y pie)."""
        contenido = app.extensions["contenido"]

        def menu_activo(*endpoints):
            return "current" if request.endpoint in endpoints else ""

        return {
            "anio_actual": datetime.now().year,
            "fundacion": contenido.fundacion(),
            "programas_menu": contenido.programas(),
            "menu_activo": menu_activo,
        }


def _registrar_errores(app: Flask) -> None:
    """Páginas amables para los errores más comunes."""

    def pagina_error(codigo, titulo, mensaje):
        return render_template("error.html", codigo=codigo, titulo=titulo, mensaje=mensaje), codigo

    @app.errorhandler(CSRFError)
    def error_csrf(_error):
        return pagina_error(
            400,
            "El formulario expiró",
            "Por seguridad, el formulario caducó. Vuelve a la página anterior, recárgala e inténtalo de nuevo.",
        )

    @app.errorhandler(ErrorBaseDatos)
    def error_base_datos(error):
        app.logger.error("Base de datos no disponible: %s", error)
        return pagina_error(
            503,
            "Servicio no disponible",
            "No pudimos conectarnos con la base de datos. Inténtalo de nuevo en unos minutos.",
        )

    @app.errorhandler(403)
    def acceso_denegado(_error):
        return pagina_error(403, "Acceso denegado", "Tu usuario no tiene permiso para realizar esta acción.")

    @app.errorhandler(404)
    def no_encontrado(_error):
        return pagina_error(404, "Página no encontrada", "La página que buscas no existe o fue movida.")

    @app.errorhandler(413)
    def demasiado_grande(_error):
        return pagina_error(413, "Solicitud demasiado grande", "La información enviada supera el tamaño permitido.")

    @app.errorhandler(500)
    def error_interno(_error):
        return pagina_error(500, "Error interno", "Ocurrió un problema inesperado. Inténtalo de nuevo más tarde.")


def _registrar_cabeceras_seguridad(app: Flask) -> None:
    @app.after_request
    def cabeceras(respuesta):
        respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
        respuesta.headers.setdefault("X-Frame-Options", "DENY")
        # Solo envía el dominio a otros sitios (YouTube lo necesita para mostrar el video)
        respuesta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        respuesta.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # La página de depuración de Flask necesita scripts en línea
        if not (app.debug and respuesta.status_code >= 500):
            respuesta.headers.setdefault("Content-Security-Policy", POLITICA_CONTENIDO)
        if app.config.get("SESSION_COOKIE_SECURE"):
            respuesta.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return respuesta


app = crear_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
