"""Pruebas de piezas que no necesitan SQL Server: conexión, scripts y seguridad."""
from datetime import timedelta
from pathlib import Path

from database import BaseDatos
from repositories.colaborador_repository import ColaboradorRepository, FiltrosBusqueda
from services.autenticacion import LimitadorIntentos, destino_seguro

CARPETA_SQL = Path(__file__).resolve().parent.parent / "sql"


def test_cadena_de_conexion_con_autenticacion_de_windows():
    cadena = BaseDatos("localhost", "BeitShalomDB").cadena_conexion()
    assert "DRIVER={ODBC Driver 18 for SQL Server}" in cadena
    assert "SERVER=localhost" in cadena
    assert "DATABASE=BeitShalomDB" in cadena
    assert "Trusted_Connection=yes" in cadena
    assert "PWD" not in cadena


def test_cadena_de_conexion_con_usuario_y_contrasena_especial():
    cadena = BaseDatos("localhost\\SQLEXPRESS", "BeitShalomDB", conexion_confiable=False,
                       usuario="sa", contrasena="a;b}c").cadena_conexion()
    assert "SERVER=localhost\\SQLEXPRESS" in cadena
    assert "UID={sa}" in cadena
    assert "PWD={a;b}}c}" in cadena      # el ; y la } no rompen la cadena
    assert "Trusted_Connection" not in cadena


def test_la_contrasena_de_la_base_de_datos_es_privada():
    base_datos = BaseDatos("localhost", "BeitShalomDB", conexion_confiable=False, contrasena="secreta")
    assert not hasattr(base_datos, "contrasena")
    assert "secreta" not in repr(vars(base_datos).keys())


def test_dividir_scripts_por_go():
    lotes = BaseDatos.dividir_lotes("SELECT 1\nGO\nSELECT 'GOOD'\n  go  \nSELECT 2;\nGO")
    assert lotes == ["SELECT 1", "SELECT 'GOOD'", "SELECT 2;"]


def test_los_scripts_sql_existen_y_se_dividen_en_lotes():
    script = (CARPETA_SQL / "01_crear_base_datos.sql").read_text(encoding="utf-8-sig")
    lotes = BaseDatos.dividir_lotes(script)
    assert lotes[0].startswith("/*") and "CREATE DATABASE BeitShalomDB" in lotes[0]
    assert any("CREATE TABLE Colaboradores" in lote for lote in lotes)
    assert any("CREATE TABLE ColaboradorAreas" in lote for lote in lotes)
    for nombre in ("02_modulo_administrativo.sql", "03_consultas_verificacion.sql", "04_datos_demo.sql"):
        assert BaseDatos.dividir_lotes((CARPETA_SQL / nombre).read_text(encoding="utf-8-sig"))


def test_filtros_se_convierten_en_sql_parametrizado():
    filtros = FiltrosBusqueda(texto="ana%'; DROP TABLE Colaboradores;--", pais="El Salvador", area_id=3, estado="Aprobado")
    condicion, parametros = ColaboradorRepository._condiciones(filtros)
    # El texto escrito por el usuario nunca aparece dentro del SQL
    assert "DROP TABLE" not in condicion
    assert condicion.count("?") == len(parametros) == 5
    assert parametros[0] == "%ana\\%'; DROP TABLE Colaboradores;--%"


def test_destino_seguro_tras_iniciar_sesion():
    assert destino_seguro("/admin/colaboradores?estado=Pendiente") == "/admin/colaboradores?estado=Pendiente"
    for destino in ("https://sitio-malicioso.example", "//sitio-malicioso.example", "/registro", "/\\sitio.example", None):
        assert destino_seguro(destino) is None


def test_limitador_de_intentos():
    reloj = [0.0]
    limitador = LimitadorIntentos(maximo_intentos=3, ventana=timedelta(minutes=15), reloj=lambda: reloj[0])
    for _ in range(3):
        assert not limitador.esta_bloqueado("ip|admin")
        limitador.registrar_fallo("ip|admin")
    assert limitador.esta_bloqueado("ip|admin")
    assert not limitador.esta_bloqueado("ip|otro")          # cada clave es independiente
    reloj[0] += 15 * 60 + 1                                   # pasan 15 minutos
    assert not limitador.esta_bloqueado("ip|admin")
    limitador.registrar_fallo("ip|admin")
    limitador.reiniciar("ip|admin")
    assert not limitador.esta_bloqueado("ip|admin")


def test_ultimos_meses_cruza_el_cambio_de_anio():
    meses = ColaboradorRepository._ultimos_meses(6)
    assert len(meses) == 6
    assert len(set(meses)) == 6
    assert meses == sorted(meses)
