"""Configuración de la aplicación.

Los datos sensibles (clave secreta y credenciales de SQL Server) se leen del
archivo .env para no escribirlos directamente en el código fuente.
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

DIRECTORIO_BASE = Path(__file__).resolve().parent
load_dotenv(DIRECTORIO_BASE / ".env")


def leer_booleano(nombre: str, por_defecto: bool = False) -> bool:
    """Convierte valores como yes/no, true/false o 1/0 en un booleano."""
    valor = os.getenv(nombre, "").strip().lower()
    if not valor:
        return por_defecto
    return valor in {"1", "true", "yes", "si", "sí", "on"}


def leer_entero(nombre: str, por_defecto: int) -> int:
    try:
        return int(os.getenv(nombre, por_defecto))
    except ValueError:
        return por_defecto


class Config:
    """Configuración general de la aplicación."""

    SECRET_KEY = os.getenv("SECRET_KEY", "")
    DEBUG = leer_booleano("FLASK_DEBUG", False)

    # --- Conexión con SQL Server (database.py) ---
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    DB_SERVER = os.getenv("DB_SERVER", "localhost")
    DB_NAME = os.getenv("DB_NAME", "BeitShalomDB")
    # yes = autenticación de Windows; no = usuario y contraseña de SQL Server
    DB_TRUSTED_CONNECTION = leer_booleano("DB_TRUSTED_CONNECTION", True)
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_ENCRYPT = leer_booleano("DB_ENCRYPT", True)
    DB_TRUST_SERVER_CERTIFICATE = leer_booleano("DB_TRUST_SERVER_CERTIFICATE", True)
    DB_TIMEOUT = leer_entero("DB_TIMEOUT", 5)

    # --- Sesiones seguras ---
    SESSION_COOKIE_NAME = "beitshalom_sesion"
    SESSION_COOKIE_HTTPONLY = True          # JavaScript no puede leer la cookie
    SESSION_COOKIE_SAMESITE = "Lax"         # Dificulta ataques desde otros sitios
    SESSION_COOKIE_SECURE = leer_booleano("SESSION_COOKIE_SECURE", False)  # yes con HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=leer_entero("SESION_MINUTOS", 30))

    # --- Protección CSRF (Flask-WTF) ---
    WTF_CSRF_TIME_LIMIT = 2 * 60 * 60       # 2 horas para completar el formulario

    # Tamaño máximo de una solicitud (el formulario ocupa unos pocos KB)
    MAX_CONTENT_LENGTH = 1024 * 1024

    # --- Panel administrativo ---
    REGISTROS_POR_PAGINA = 15
    MAX_INTENTOS_LOGIN = 5
    MINUTOS_BLOQUEO_LOGIN = 15

    @classmethod
    def como_diccionario(cls) -> dict:
        """Devuelve la configuración como diccionario (útil fuera de Flask)."""
        return {clave: getattr(cls, clave) for clave in dir(cls) if clave.isupper()}


class ConfigPruebas(Config):
    """Configuración usada por las pruebas automáticas."""

    TESTING = True
    DEBUG = False
    SECRET_KEY = "clave-exclusiva-para-pruebas"
    WTF_CSRF_ENABLED = False
