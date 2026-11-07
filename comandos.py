"""Comandos de consola para instalar y administrar el sistema.

Se ejecutan desde la carpeta del proyecto con el entorno virtual activo:

    flask --app app probar-conexion      Comprueba la conexión con SQL Server
    flask --app app crear-bd             Crea BeitShalomDB, sus tablas y las áreas
    flask --app app crear-admin          Crea un usuario para el panel administrativo
    flask --app app cargar-demo          Inserta solicitudes ficticias de ejemplo
    flask --app app depurar-datos        Aplica la política de conservación de datos
"""
import os
from datetime import datetime, timedelta
from pathlib import Path

import click
from flask import Flask, current_app

from database import ErrorBaseDatos
from models.errores import ReglaNegocioError
from models.usuario import Usuario
from repositories.base_repository import RegistroDuplicadoError

CARPETA_SQL = Path(__file__).resolve().parent / "sql"
SCRIPTS_INSTALACION = ("01_crear_base_datos.sql", "02_modulo_administrativo.sql")
SCRIPT_DEMO = "04_datos_demo.sql"


def registrar_comandos(app: Flask) -> None:
    for comando in (probar_conexion, crear_bd, crear_admin, cargar_demo, depurar_datos):
        app.cli.add_command(comando)


def _base_datos():
    return current_app.extensions["base_datos"]


def _error_conexion(error: ErrorBaseDatos) -> click.ClickException:
    detalle = f"\nDetalle: {error.__cause__}" if error.__cause__ else ""
    return click.ClickException(f"{error}{detalle}\nRevisa los valores DB_* del archivo .env.")


@click.command("probar-conexion")
def probar_conexion():
    """Comprueba la conexión con SQL Server."""
    base_datos = _base_datos()
    try:
        version = base_datos.probar_conexion(base_datos="master")
        existe = base_datos.existe_base_datos()
    except ErrorBaseDatos as error:
        raise _error_conexion(error) from error
    click.secho(f"Conexión correcta con {base_datos.servidor}.", fg="green")
    click.echo(version.splitlines()[0])
    if existe:
        click.echo(f"La base de datos {base_datos.nombre} existe.")
    else:
        click.secho(f"La base de datos {base_datos.nombre} aún no existe: ejecuta 'flask --app app crear-bd'.", fg="yellow")


@click.command("crear-bd")
def crear_bd():
    """Crea la base de datos BeitShalomDB, sus tablas y las áreas de colaboración."""
    base_datos = _base_datos()
    for nombre in SCRIPTS_INSTALACION:
        try:
            lotes = base_datos.ejecutar_script(CARPETA_SQL / nombre)
        except ErrorBaseDatos as error:
            raise _error_conexion(error) from error
        click.echo(f"  ✔ {nombre} ({lotes} lotes ejecutados)")
    click.secho("Base de datos lista.", fg="green")


@click.command("crear-admin")
@click.option("--usuario", "nombre_usuario", default=None, help="Nombre para iniciar sesión.")
@click.option("--nombre", "nombre_completo", default=None, help="Nombre completo de la persona.")
@click.option(
    "--rol",
    type=click.Choice(Usuario.ROLES),
    default=Usuario.ROL_ADMINISTRADOR,
    show_default=True,
    help="Administrador evalúa solicitudes; Consulta solo puede verlas.",
)
@click.option("--desde-env", is_flag=True, help="Usa ADMIN_USUARIO, ADMIN_NOMBRE y ADMIN_PASSWORD del .env.")
def crear_admin(nombre_usuario, nombre_completo, rol, desde_env):
    """Crea un usuario del panel administrativo (la contraseña se guarda como hash)."""
    if desde_env:
        nombre_usuario = nombre_usuario or os.getenv("ADMIN_USUARIO", "")
        nombre_completo = nombre_completo or os.getenv("ADMIN_NOMBRE", "Administrador del sistema")
        password = os.getenv("ADMIN_PASSWORD", "")
        if not nombre_usuario or not password:
            raise click.ClickException("Define ADMIN_USUARIO y ADMIN_PASSWORD en el archivo .env.")
    else:
        nombre_usuario = nombre_usuario or click.prompt("Usuario")
        nombre_completo = nombre_completo or click.prompt("Nombre completo")
        password = click.prompt("Contraseña", hide_input=True, confirmation_prompt="Repite la contraseña")

    usuario = Usuario(nombre_usuario, nombre_completo, rol)
    errores = usuario.validar()
    if errores:
        raise click.ClickException(" ".join(errores.values()))
    try:
        usuario.establecer_password(password)
        current_app.extensions["repositorios"]["usuarios"].crear(usuario)
    except (ReglaNegocioError, RegistroDuplicadoError) as error:
        raise click.ClickException(str(error)) from error
    except ErrorBaseDatos as error:
        raise _error_conexion(error) from error
    click.secho(f"Usuario «{usuario.usuario}» creado con el rol {usuario.rol}.", fg="green")


@click.command("cargar-demo")
def cargar_demo():
    """Inserta solicitudes ficticias para probar el panel (correos @example.com)."""
    try:
        _base_datos().ejecutar_script(CARPETA_SQL / SCRIPT_DEMO)
    except ErrorBaseDatos as error:
        raise _error_conexion(error) from error
    click.secho("Datos de demostración cargados.", fg="green")


@click.command("depurar-datos")
@click.option("--meses", default=12, show_default=True, type=click.IntRange(min=1),
              help="Antigüedad mínima de las solicitudes rechazadas que se eliminarán.")
@click.confirmation_option(prompt="¿Eliminar definitivamente las solicitudes rechazadas antiguas?")
def depurar_datos(meses):
    """Política de conservación: elimina solicitudes rechazadas con más de N meses."""
    fecha_limite = datetime.now() - timedelta(days=30 * meses)
    try:
        eliminadas = current_app.extensions["repositorios"]["colaboradores"].eliminar_rechazados_antes_de(fecha_limite)
    except ErrorBaseDatos as error:
        raise _error_conexion(error) from error
    click.echo(f"Solicitudes rechazadas eliminadas: {eliminadas}.")
