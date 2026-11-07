"""Asistente de instalación del Sistema de Registro de Colaboradores.

Uso (desde la carpeta del proyecto, con el entorno virtual activo):

    python instalar.py

El asistente:
  1. Comprueba Python, las librerías y el controlador ODBC de SQL Server.
  2. Pregunta cómo te conectas a SQL Server (Windows o usuario y contraseña)
     y prueba la conexión antes de continuar.
  3. Escribe TU archivo .env (cada persona tiene el suyo; no se comparte).
  4. Crea la base de datos BeitShalomDB con los scripts de la carpeta sql/.
  5. Crea tu usuario del panel administrativo.
  6. Si quieres, carga datos de demostración.
"""
from __future__ import annotations

import argparse
import getpass
import logging
import platform
import secrets
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
DRIVERS_PREFERIDOS = ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server")


# ----------------------------------------------------------------------
# Utilidades (también se usan en tests/test_instalar.py)
# ----------------------------------------------------------------------
def elegir_driver(disponibles: list[str]) -> str | None:
    """Devuelve el mejor controlador ODBC de SQL Server instalado."""
    for driver in DRIVERS_PREFERIDOS:
        if driver in disponibles:
            return driver
    return next((d for d in disponibles if "SQL Server" in d), None)


def valor_env(valor: str) -> str:
    """Escribe un valor para el archivo .env, entre comillas si hace falta."""
    texto = str(valor)
    if texto and all(c.isalnum() or c in "-_.@:/" for c in texto):
        return texto
    return '"' + texto.replace("\\", "\\\\").replace('"', '\\"') + '"'


def contenido_env(servidor: str, driver: str, confiable: bool, usuario: str, contrasena: str) -> str:
    return "\n".join([
        "# =====================================================================",
        "# Configuración privada de ESTA computadora (creada con instalar.py).",
        "# No compartas este archivo: cada persona tiene el suyo.",
        "# =====================================================================",
        "",
        f"SECRET_KEY={secrets.token_hex(32)}",
        "FLASK_DEBUG=1",
        "",
        "# --- SQL Server ---",
        f"DB_DRIVER={valor_env(driver)}",
        f"DB_SERVER={valor_env(servidor)}",
        "DB_NAME=BeitShalomDB",
        f"DB_TRUSTED_CONNECTION={'yes' if confiable else 'no'}",
        f"DB_USER={valor_env(usuario) if not confiable else ''}",
        f"DB_PASSWORD={valor_env(contrasena) if not confiable else ''}",
        "DB_ENCRYPT=yes",
        "DB_TRUST_SERVER_CERTIFICATE=yes",
        "",
        "# --- Sesiones (SESSION_COOKIE_SECURE=yes cuando el sitio use HTTPS) ---",
        "SESSION_COOKIE_SECURE=no",
        "SESION_MINUTOS=30",
        "",
    ])


def preguntar(texto: str, por_defecto: str = "") -> str:
    sufijo = f" [{por_defecto}]" if por_defecto else ""
    respuesta = input(f"{texto}{sufijo}: ").strip()
    return respuesta or por_defecto


def confirmar(texto: str, por_defecto: bool = False) -> bool:
    opciones = "S/n" if por_defecto else "s/N"
    respuesta = input(f"{texto} ({opciones}): ").strip().lower()
    if not respuesta:
        return por_defecto
    return respuesta in ("s", "si", "sí", "y", "yes")


def titulo(texto: str) -> None:
    print(f"\n=== {texto} ===")


def salir(mensaje: str) -> None:
    print(f"\n✘ {mensaje}")
    sys.exit(1)


# ----------------------------------------------------------------------
# Pasos del asistente
# ----------------------------------------------------------------------
def comprobar_entorno():
    titulo("1. Comprobando Python y las librerías")
    if sys.version_info < (3, 11):
        salir(f"Se necesita Python 3.11 o superior (tienes {platform.python_version()}).")
    try:
        import flask  # noqa: F401
        import flask_wtf  # noqa: F401
        import openpyxl  # noqa: F401
        import pyodbc
        from dotenv import dotenv_values  # noqa: F401
    except ImportError as error:
        salir(f"Falta una librería ({error.name}). Ejecuta primero:\n   python -m pip install -r requirements.txt")
    print(f"✔ Python {platform.python_version()} y librerías instaladas.")

    driver = elegir_driver(pyodbc.drivers())
    if driver is None:
        salir(
            "No se encontró el controlador ODBC de SQL Server.\n"
            "   Instala «ODBC Driver 18 for SQL Server» desde la página de Microsoft\n"
            "   (en Linux, el paquete msodbcsql18) y vuelve a ejecutar este asistente."
        )
    print(f"✔ Controlador encontrado: {driver}")
    return driver


def elegir_autenticacion() -> bool:
    """Pregunta cómo conectarse en Windows. Devuelve True si se elige la autenticación de Windows.

    La opción por defecto es el usuario sa, como en la sección 13 de la guía del profesor.
    """
    print("Autenticación:  1) Windows (sin contraseña)   2) SQL Server con el usuario sa (como en la guía)")
    while (opcion := preguntar("Elige 1 o 2", "2")) not in ("1", "2"):
        print("Escribe 1 o 2.")
    return opcion == "1"


def configurar_conexion(driver: str, archivo_env: Path):
    from database import BaseDatos, ErrorBaseDatos

    titulo("2. Conexión con SQL Server")
    es_windows = platform.system() == "Windows"
    print("Instancia predeterminada: localhost   ·   SQL Server Express: localhost\\SQLEXPRESS")

    while True:
        servidor = preguntar("Servidor", "localhost")
        if es_windows:
            confiable = elegir_autenticacion()
        else:
            print("En Linux y Mac se usa la autenticación de SQL Server (usuario y contraseña).")
            confiable = False
        usuario = contrasena = ""
        if not confiable:
            usuario = preguntar("Usuario de SQL Server", "sa")
            contrasena = getpass.getpass("Contraseña de ese usuario (no se mostrará al escribir): ")

        base = BaseDatos(servidor, "BeitShalomDB", driver=driver, conexion_confiable=confiable,
                         usuario=usuario, contrasena=contrasena, tiempo_espera=8)
        try:
            version = base.probar_conexion(base_datos="master")
        except ErrorBaseDatos as error:
            print(f"✘ No se pudo conectar: {error.__cause__ or error}")
            print("  Revisa que SQL Server esté encendido, el nombre del servidor y la contraseña.")
            if confirmar("¿Intentar de nuevo?", True):
                continue
            salir("Instalación cancelada.")
        print(f"✔ Conectado: {version.splitlines()[0]}")
        break

    archivo_env.write_text(contenido_env(servidor, driver, confiable, usuario, contrasena), encoding="utf-8")
    try:
        archivo_env.chmod(0o600)
    except OSError:
        pass
    print(f"✔ Configuración guardada en {archivo_env.name} (privado, no se comparte).")
    return base


def conexion_existente(archivo_env: Path):
    """Usa el .env que ya existe y prueba la conexión."""
    from dotenv import dotenv_values

    from database import BaseDatos, ErrorBaseDatos

    datos = dotenv_values(archivo_env)
    confiable = str(datos.get("DB_TRUSTED_CONNECTION", "yes")).lower() in ("1", "true", "yes", "si", "sí")
    base = BaseDatos(
        datos.get("DB_SERVER") or "localhost",
        datos.get("DB_NAME") or "BeitShalomDB",
        driver=datos.get("DB_DRIVER") or DRIVERS_PREFERIDOS[0],
        conexion_confiable=confiable,
        usuario=datos.get("DB_USER") or "",
        contrasena=datos.get("DB_PASSWORD") or "",
        tiempo_espera=8,
    )
    try:
        print(f"✔ Conectado: {base.probar_conexion(base_datos='master').splitlines()[0]}")
    except ErrorBaseDatos as error:
        salir(f"No se pudo conectar con los datos de {archivo_env.name}: {error.__cause__ or error}\n"
              "   Corrige el archivo o vuelve a ejecutar el asistente y elige reemplazarlo.")
    return base


def crear_base_datos(base) -> None:
    from comandos import CARPETA_SQL, SCRIPTS_INSTALACION

    titulo("3. Creando la base de datos BeitShalomDB")
    for nombre in SCRIPTS_INSTALACION:
        lotes = base.ejecutar_script(CARPETA_SQL / nombre)
        print(f"✔ {nombre} ({lotes} lotes)")


def crear_administrador(base) -> None:
    from models.errores import ReglaNegocioError
    from models.usuario import Usuario
    from repositories.base_repository import RegistroDuplicadoError
    from repositories.usuario_repository import UsuarioRepository

    titulo("4. Usuario del panel administrativo")
    repositorio = UsuarioRepository(base)
    if repositorio.contar() and not confirmar("Ya hay usuarios creados. ¿Crear otro?"):
        return

    while True:
        usuario = Usuario(preguntar("Usuario para iniciar sesión", "admin"),
                          preguntar("Nombre completo", "Administrador del sistema"),
                          Usuario.ROL_ADMINISTRADOR)
        errores = usuario.validar()
        if errores:
            print("✘ " + " ".join(errores.values()))
            continue
        print(f"La contraseña necesita al menos {Usuario.PASSWORD_MIN} caracteres, una mayúscula, una minúscula y un número.")
        password = getpass.getpass("Contraseña: ")
        if password != getpass.getpass("Repite la contraseña: "):
            print("✘ Las contraseñas no coinciden.")
            continue
        try:
            usuario.establecer_password(password)
            repositorio.crear(usuario)
        except (ReglaNegocioError, RegistroDuplicadoError) as error:
            print(f"✘ {error}")
            continue
        print(f"✔ Usuario «{usuario.usuario}» creado (en la base de datos solo se guarda el hash de la contraseña).")
        return


def cargar_demo(base) -> None:
    from comandos import CARPETA_SQL, SCRIPT_DEMO

    titulo("5. Datos de demostración (opcional)")
    if confirmar("¿Cargar 16 solicitudes ficticias para ver el dashboard con datos?"):
        base.ejecutar_script(CARPETA_SQL / SCRIPT_DEMO)
        print("✔ Datos de demostración cargados (correos @example.com).")


def main() -> None:
    analizador = argparse.ArgumentParser(description="Asistente de instalación de Fundación Beit Shalom.")
    analizador.add_argument("--archivo-env", default=str(CARPETA / ".env"), help="Ruta del archivo .env a crear.")
    argumentos = analizador.parse_args()
    archivo_env = Path(argumentos.archivo_env)
    # El asistente muestra sus propios mensajes de error; se ocultan los del registro interno
    logging.getLogger("database").setLevel(logging.CRITICAL)

    print("Asistente de instalación · Sistema de Registro de Colaboradores · Fundación Beit Shalom")
    driver = comprobar_entorno()

    if archivo_env.exists() and not confirmar(f"\nYa existe {archivo_env.name}. ¿Quieres reemplazarlo con una configuración nueva?"):
        titulo("2. Conexión con SQL Server (usando tu .env actual)")
        base = conexion_existente(archivo_env)
    else:
        base = configurar_conexion(driver, archivo_env)

    crear_base_datos(base)
    crear_administrador(base)
    cargar_demo(base)

    titulo("¡Listo!")
    print("Inicia el sistema con:   flask --app app run --debug")
    print("Sitio web:               http://127.0.0.1:5000")
    print("Panel administrativo:    http://127.0.0.1:5000/admin")


if __name__ == "__main__":
    sys.path.insert(0, str(CARPETA))
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstalación cancelada.")
