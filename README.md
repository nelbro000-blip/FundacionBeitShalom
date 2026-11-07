# Sistema de Registro de Colaboradores — Fundación Beit Shalom

Sitio web institucional de la **Fundación Internacional Beit Shalom** con su sistema
de registro de colaboradores, desarrollado con **Python · POO · MVC**. Une dos trabajos
de la clase:

1. La **plantilla Kidearn** (diseño del sitio: inicio, nosotros, programas, equipo,
   eventos, galería, noticias, contacto…), convertida en plantillas de Flask.
2. El **Sistema de Registro de Colaboradores** (guía "POO y Web"): formulario
   «Quiero colaborar», validaciones, SQL Server y panel administrativo.

**Universidad Doctor Andrés Bello** · Facultad de Tecnología e Innovación
Ingeniería en Computación · Programación Orientada a Objetos · Tema: POO y Web
Docente: Ing. Balmore Montano

> ¿Vas a instalarlo en otra computadora o compartirlo con tu grupo?
> Sigue **`GUIA_DE_INSTALACION.pdf`** (paso a paso para Windows, Linux y Mac) y lee
> **[GUIA_PARA_COMPANEROS.md](GUIA_PARA_COMPANEROS.md)**: explica qué se comparte,
> cómo funciona el usuario `sa` de SQL Server y el asistente `python instalar.py`.

---

## Contenido

1. [Qué hace el sistema](#1-qué-hace-el-sistema)
2. [Tecnologías](#2-tecnologías)
3. [Arquitectura MVC + Repository](#3-arquitectura-mvc--repository)
4. [Estructura de carpetas](#4-estructura-de-carpetas)
5. [Base de datos BeitShalomDB](#5-base-de-datos-beitshalomdb)
6. [Programación orientada a objetos](#6-programación-orientada-a-objetos)
7. [Instalación y ejecución](#7-instalación-y-ejecución)
8. [Uso del sistema](#8-uso-del-sistema)
9. [Editar el contenido del sitio](#9-editar-el-contenido-del-sitio)
10. [Pruebas](#10-pruebas)
11. [Seguridad y protección de datos](#11-seguridad-y-protección-de-datos)
12. [Plan de desarrollo por etapas](#12-plan-de-desarrollo-por-etapas)
13. [Configuración usada en el desarrollo](#13-configuración-usada-en-el-desarrollo)
14. [Solución de problemas](#14-solución-de-problemas)

---

## 1. Qué hace el sistema

| Módulo | Funcionalidades |
|---|---|
| **Sitio institucional** | Inicio con carrusel, Nosotros (misión y visión), Programas (6, cada uno con su página), Equipo, Eventos (con detalle y mapa), Galería, Noticias (con detalle), Formas de apoyar, Preguntas frecuentes, Contacto y Política de privacidad. Diseño de la plantilla Kidearn, adaptable a celulares. |
| **Registro de colaboradores** (`/registro`) | Formulario «Quiero colaborar» en 4 secciones: información personal, áreas de colaboración, disponibilidad y confirmación. Validación con HTML5, JavaScript **y** Python. Se guarda en SQL Server. |
| **Contacto** (`/contacto`) | Formulario que guarda los mensajes en SQL Server; el personal los lee en el panel. |
| **Panel administrativo** (`/admin`) | Inicio de sesión, dashboard con gráficos, listado con búsqueda y filtros, detalle, aprobación y rechazo con historial, mensajes de contacto, eliminación de datos y exportación a Excel. |

## 2. Tecnologías

| Tecnología | Aplicación en el proyecto |
|---|---|
| Python 3 | Lenguaje principal (probado con Python 3.14). |
| POO | Clases, objetos, encapsulamiento, herencia y polimorfismo. |
| Flask | Framework web: rutas organizadas con *Blueprints*. |
| MVC + Repository | Organización de la arquitectura. |
| HTML5 / Jinja2 | Plantillas con herencia (`base.html`) y macros reutilizables. |
| CSS3 | Plantilla Kidearn + `estilos.css` propio (Grid, Flexbox, Media Queries). |
| JavaScript | Validaciones en tiempo real (`validaciones.js`) e interactividad de la plantilla. |
| Bootstrap 5, jQuery y complementos | Librerías de la plantilla Kidearn (carruseles, animaciones, galería). |
| SQL Server + pyodbc | Base de datos institucional `BeitShalomDB`. |
| python-dotenv | Configuración privada en el archivo `.env`: la contraseña de `sa` queda fuera del código (la guía lo marca como opcional). |
| Flask-WTF | Protección CSRF de todos los formularios (la guía lo marca como opcional). |
| openpyxl | Reportes en Excel. |
| pytest | Pruebas automáticas. |

HTML, CSS y JavaScript están en archivos separados: no hay scripts dentro del HTML.

## 3. Arquitectura MVC + Repository

```
 Navegador
    │  1. Página del sitio → botón «Quiero colaborar»          8. confirmacion.html
    ▼                                                                   ▲
 VISTA  templates/registro.html + estilos.css + validaciones.js
    │  2-3. La persona completa los datos y JavaScript los revisa
    │  4. POST /registro (con token CSRF)
    ▼
 CONTROLADOR  controllers/colaborador_controller.py
    │  5. Recibe los datos y crea un objeto Colaborador
    ▼
 MODELO  models/colaborador.py (hereda de models/persona.py)
    │  6. validar(): Python vuelve a comprobar las reglas del negocio
    ▼
 REPOSITORY  repositories/colaborador_repository.py
    │  7. INSERT parametrizado dentro de una transacción
    ▼
 SQL SERVER  BeitShalomDB
```

| Componente | Archivos | ¿Qué hace? |
|---|---|---|
| Vista | `templates/` | Presenta el sitio, el formulario y el panel. |
| Controlador | `controllers/` | `sitio_controller` (páginas del sitio y contacto), `colaborador_controller` (registro) y `admin_controller` (panel). **No contienen SQL.** |
| Modelo | `models/` | Clases y reglas del negocio. |
| Repository | `repositories/` | Única capa que lee datos: SQL Server (colaboradores, usuarios, mensajes) y `contenido/sitio.json` (textos del sitio). |

## 4. Estructura de carpetas

```
FundacionBeitShalom/
├── app.py                      Inicio de Flask: controladores, seguridad y errores
├── config.py                   Configuración (lee el archivo .env)
├── database.py                 Conexión a SQL Server y transacciones (pyodbc)
├── comandos.py                 Comandos: crear-bd, crear-admin, cargar-demo...
├── instalar.py                 Asistente de instalación (crea .env, base y usuario)
├── requirements.txt            Dependencias
├── .env.example                Plantilla de configuración (el .env real es privado)
├── GUIA_PARA_COMPANEROS.md     Cómo compartir e instalar el proyecto
├── GUIA_DE_INSTALACION.pdf     Paso a paso para instalarlo en otra computadora
├── contenido/
│   └── sitio.json              Textos del sitio: programas, equipo, eventos, noticias...
├── models/
│   ├── persona.py              Clase base Persona (nombre, correo, teléfono)
│   ├── colaborador.py          Colaborador(Persona): reglas del registro
│   ├── mensaje.py              MensajeContacto(Persona): mensajes de contacto
│   ├── usuario.py              Usuario del panel (contraseña con hash)
│   ├── contenido.py            Programa, Evento, Noticia... (dataclasses)
│   ├── area.py, errores.py
├── repositories/
│   ├── base_repository.py      Clase base: transacciones y errores (herencia)
│   ├── colaborador_repository.py, usuario_repository.py, mensaje_repository.py
│   └── contenido_repository.py Lee contenido/sitio.json
├── controllers/
│   ├── sitio_controller.py     Páginas del sitio y formulario de contacto
│   ├── colaborador_controller.py   Registro de colaboradores
│   └── admin_controller.py     Panel administrativo
├── services/
│   ├── autenticacion.py        Inicio de sesión, roles y bloqueo por intentos
│   └── exportador_excel.py     Reportes en Excel
├── templates/
│   ├── base.html               Diseño común: menú, encabezado y pie (Kidearn)
│   ├── registro.html, confirmacion.html, privacidad.html, error.html
│   ├── sitio/                  Páginas del sitio + macros.html (tarjetas reutilizables)
│   ├── admin/                  Panel administrativo
│   └── parciales/              Mensajes de aviso
├── static/
│   ├── assets/                 Plantilla Kidearn (solo lo que se usa: CSS, JS, imágenes)
│   ├── css/estilos.css         Estilos propios del sitio y del formulario
│   ├── css/admin.css           Estilos del panel
│   └── js/validaciones.js, js/admin.js
├── sql/
│   ├── 01_crear_base_datos.sql         Base de datos, tablas y áreas
│   ├── 02_modulo_administrativo.sql    Usuarios, historial, mensajes e índices
│   ├── 03_consultas_verificacion.sql   Consultas para comprobar las pruebas
│   └── 04_datos_demo.sql               Datos ficticios opcionales
└── tests/                      Pruebas automáticas (pytest)
```

## 5. Base de datos BeitShalomDB

Las tres tablas del diseño de la guía (sección 5) se crearon tal como se propusieron:

```
Colaboradores                ColaboradorAreas               AreasColaboracion
─────────────                ────────────────               ─────────────────
id (PK)            1 ──── N  colaborador_id (FK)   N ──── 1  id (PK)
nombre_completo              area_id (FK)                   nombre (UNIQUE)
pais, correo (UNIQUE)        UNIQUE(colaborador_id,         activa
telefono, modalidad                 area_id)
disponibilidad, motivacion
acepta_privacidad (CHECK = 1)
fecha_registro, estado (CHECK)
```

El script `sql/02_modulo_administrativo.sql` agrega:

- **Usuarios**: personal autorizado; la contraseña se guarda solo como hash.
- **HistorialEstados**: quién aprobó o rechazó cada solicitud, cuándo y por qué.
- **MensajesContacto**: mensajes enviados desde la página de contacto.

Las fechas se envían desde Python con la hora local, así coinciden con la hora del país
aunque SQL Server use UTC (como ocurre dentro de Docker).

## 6. Programación orientada a objetos

| Concepto | Dónde se aplica |
|---|---|
| Clase y objeto | `Colaborador` es el molde; cada solicitud recibida es un objeto. |
| Constructor | `__init__()` inicializa los atributos (y llama a `super().__init__()`). |
| Atributos y métodos | Nombre, país, correo…; `validar()`, `cambiar_estado()`. |
| Encapsulamiento | Atributos privados (`_nombre`, `__password_hash`) con `@property`; el estado solo cambia con `cambiar_estado()`. |
| **Herencia** | `Colaborador` y `MensajeContacto` heredan de **`Persona`** el nombre, el correo, el teléfono y su validación. `ColaboradorRepository`, `UsuarioRepository` y `MensajeRepository` heredan de `BaseRepository`. |
| **Polimorfismo** | Cada clase tiene su propio `validar()`; `MensajeContacto` sobrescribe `NOMBRE_MIN`. Las pruebas usan repositorios en memoria con los mismos métodos que los reales. |
| Dataclasses | `Programa`, `Evento`, `Noticia`, `MiembroEquipo`… representan el contenido del sitio. |
| Métodos de clase y estáticos | `BaseDatos.desde_config()`, `FiltrosBusqueda.desde_argumentos()`, `Usuario.validar_password()`. |

## 7. Instalación y ejecución

Requisitos: Python 3.11 o superior (recomendado 3.13 o 3.14), SQL Server 2017 o superior
con el **modo mixto** activado y el usuario `sa` habilitado (sección 13 de la guía), y el
controlador **ODBC Driver 18 for SQL Server**. El paso a paso completo (Windows, Linux y
Mac) está en `GUIA_DE_INSTALACION.pdf`; la explicación de `sa` y de cómo compartir el
proyecto, en [GUIA_PARA_COMPANEROS.md](GUIA_PARA_COMPANEROS.md).

```powershell
python -m venv venv
.\venv\Scripts\Activate          # En Linux/Mac: source venv/bin/activate
python -m pip install -r requirements.txt
python instalar.py               # crea .env, la base de datos y tu usuario del panel
flask --app app run --debug
```

Comandos útiles (con el entorno virtual activo):

| Comando | Para qué sirve |
|---|---|
| `flask --app app probar-conexion` | Comprobar la conexión con SQL Server. |
| `flask --app app crear-bd` | Crear o actualizar la base de datos (se puede repetir sin riesgo). |
| `flask --app app crear-admin` | Crear otro usuario del panel (`--rol Consulta` para solo lectura). |
| `flask --app app cargar-demo` | Cargar 16 solicitudes ficticias (correos `@example.com`). |
| `flask --app app depurar-datos --meses 12` | Borrar solicitudes rechazadas antiguas (política de conservación). |

## 8. Uso del sistema

| Dirección | Contenido |
|---|---|
| `/` | Inicio del sitio. |
| `/nosotros`, `/programas`, `/equipo`, `/eventos`, `/galeria`, `/noticias` | Páginas institucionales. |
| `/apoyanos`, `/preguntas-frecuentes`, `/contacto`, `/privacidad` | Apoyo, dudas, contacto y privacidad. |
| `/registro` | Formulario «Quiero colaborar». |
| `/admin` | Panel administrativo (requiere iniciar sesión; enlace "Acceso del personal" en el pie). |

| Rol del panel | Puede |
|---|---|
| Administrador | Consultar, buscar, filtrar, exportar, aprobar, rechazar, eliminar datos y mensajes. |
| Consulta | Consultar, buscar, filtrar y exportar (no modifica nada). |

## 9. Editar el contenido del sitio

Los textos y fotos del sitio están en **`contenido/sitio.json`**: datos de la fundación,
carrusel, programas, equipo, testimonios, eventos, noticias, galería, preguntas frecuentes
y formas de apoyar. Para agregar una noticia basta con copiar un bloque de `"noticias"`,
cambiar sus datos y guardar: el sitio la muestra sin tocar el código (el archivo se vuelve
a leer automáticamente). Las imágenes van en `static/assets/images/`.

## 10. Pruebas

```bash
pytest -v                 # todas las pruebas
pytest -m integracion -v  # solo las pruebas contra SQL Server real
```

Las pruebas de integración se omiten automáticamente si SQL Server está apagado.
Pruebas de la sección 19 de la guía:

| Prueba | Resultado esperado | Prueba automática |
|---|---|---|
| Enviar formulario vacío | Mostrar errores | `test_registro.py::test_enviar_formulario_vacio_muestra_errores` |
| Introducir correo incorrecto | Rechazar el dato | `test_registro.py::test_correo_incorrecto_es_rechazado` |
| No seleccionar áreas | Solicitar al menos una | `test_registro.py::test_no_seleccionar_areas_solicita_al_menos_una` |
| No aceptar privacidad | Impedir el envío | `test_registro.py::test_no_aceptar_privacidad_impide_el_envio` |
| Enviar información correcta | Guardar en SQL Server | `test_integracion_sqlserver.py::test_enviar_informacion_correcta_se_guarda_en_sql_server` |
| Registrar correo duplicado | Informar que ya existe | `test_integracion_sqlserver.py::test_registrar_correo_duplicado_informa_que_ya_existe` |
| Consultar la base de datos | Visualizar el colaborador | `test_integracion_sqlserver.py::test_consultar_la_base_de_datos_muestra_el_colaborador` |
| Consultar sus áreas | Mostrar todas las áreas seleccionadas | `test_integracion_sqlserver.py::test_consultar_sus_areas_muestra_todas_las_seleccionadas` |
| Simular error SQL | Revertir la transacción | `test_integracion_sqlserver.py::test_simular_error_sql_revierte_la_transaccion` |

Además: todas las páginas del sitio cargan y ninguna imagen o archivo enlazado falta
(`test_sitio.py`), formulario de contacto, panel (roles, bloqueo de contraseñas,
mensajes, exportación), protección CSRF y el asistente de instalación.

## 11. Seguridad y protección de datos

| Medida (sección 17) | Implementación |
|---|---|
| Recopilar solo información necesaria | Teléfono y motivación son opcionales. |
| Aceptación expresa de la privacidad | Casilla obligatoria en registro y contacto, validada en HTML5, JavaScript, Python y SQL Server (`CHECK`). |
| HTTPS al publicar | `SESSION_COOKIE_SECURE=yes` activa cookies seguras y HSTS. |
| Validar en JavaScript y en Python | `validaciones.js` y los métodos `validar()` usan las mismas reglas. |
| Consultas SQL parametrizadas | Todos los valores viajan como `?`; los comodines de `LIKE` se escapan. |
| Proteger las rutas administrativas | `login_requerido` y `rol_requerido`; sesiones de 30 minutos. |
| Contraseñas protegidas | Hash *scrypt*; bloqueo de 15 minutos tras 5 intentos fallidos. |
| El público no ve registros de otros | La confirmación no usa identificadores en la URL y se muestra una sola vez. |
| Protección CSRF | Flask-WTF en todos los formularios. |
| Cabeceras de seguridad | CSP (JavaScript solo del propio sitio; se permiten estilos de la plantilla, Google Fonts, mapas y videos), X-Frame-Options, `no-store` en el panel. |
| Conservación y eliminación | Botones "Eliminar" en el panel y `flask --app app depurar-datos`. |
| Trabajo con menores | El registro y la política aclaran que inscribirse no autoriza a trabajar con niños. |

## 12. Plan de desarrollo por etapas

| Etapa | Actividad | Estado |
|---|---|---|
| 1 | Preparación de Visual Studio Code y Python | ✔ (`.vscode/`, `venv`, `requirements.txt`, `instalar.py`) |
| 2 | Creación de la base de datos SQL Server | ✔ (`sql/`) |
| 3 | Desarrollo de la clase Colaborador | ✔ (con la clase base `Persona`) |
| 4 | Construcción de HTML | ✔ (plantilla Kidearn integrada) |
| 5 | Desarrollo de CSS | ✔ |
| 6 | Desarrollo de JavaScript | ✔ |
| 7 | Desarrollo de Flask (controladores y rutas) | ✔ |
| 8 | Desarrollo del Repository | ✔ |
| 9 | Integración | ✔ (sitio + registro + panel) |
| 10 | Pruebas y seguridad | ✔ |
| 11 | Panel administrativo | ✔ |
| 12 | Publicación | Preparado: HTTPS, `FLASK_DEBUG=0` y un servidor WSGI. |

## 13. Configuración usada en el desarrollo

| Elemento | Configuración |
|---|---|
| Instancia de SQL Server | `localhost`, puerto 1433: SQL Server 2022 en un contenedor Docker sobre Arch Linux. |
| Autenticación | SQL Server con el usuario `sa` (modo mixto), como en la sección 13 de la guía. El código también acepta la autenticación de Windows (`DB_TRUSTED_CONNECTION=yes`). |
| Contraseña de `sa` | En el archivo privado `.env` (`DB_PASSWORD`), no dentro de `database.py`: así el mismo código sirve en todas las computadoras. |
| Versión de Python | Python 3.14 (funciona desde 3.11). |

## 14. Solución de problemas

| Mensaje | Solución |
|---|---|
| La página dice "Servicio no disponible" | SQL Server está apagado. Docker: `sudo systemctl start docker` y `sudo docker start <contenedor>`. |
| `Login timeout expired` | Lo mismo: comprobar que SQL Server esté encendido y el valor de `DB_SERVER`. |
| `Login failed for user` | Revisar `DB_USER` y `DB_PASSWORD`, o volver a ejecutar `python instalar.py`. En Windows, comprobar que el modo mixto esté activo y `sa` habilitado (`GUIA_DE_INSTALACION.pdf`, paso 2). |
| `Can't open lib 'ODBC Driver 18 for SQL Server'` | Instalar el controlador ODBC 18 (o cambiar `DB_DRIVER` a la versión instalada). |
| `Cannot open database "BeitShalomDB"` | Ejecutar `flask --app app crear-bd`. |
| "El formulario expiró" | El token CSRF caducó: recargar la página. |
