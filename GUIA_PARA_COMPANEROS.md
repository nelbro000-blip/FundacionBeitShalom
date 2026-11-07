# Guía para compartir el proyecto y prepararlo en otra computadora

Esta guía explica qué se comparte, cómo funciona la base de datos (y el famoso
usuario **sa**) y qué debe hacer cada compañero para que el sistema funcione en
su computadora.

El paso a paso detallado, pregunta por pregunta, está en **`GUIA_DE_INSTALACION.pdf`**
(en esta misma carpeta).

---

## 1. La idea clave: el código se comparte, la base de datos no

El proyecto tiene dos partes:

| Parte | ¿Se comparte? | Explicación |
|---|---|---|
| Código (Python, HTML, CSS, JS) | **Sí** | Es igual para todos. |
| Scripts SQL (`sql/`) | **Sí** | Son las "instrucciones" para crear la base de datos. |
| `.env.example` | **Sí** | Plantilla de configuración, sin contraseñas. |
| `.env` | **No** | Tiene las contraseñas de TU computadora. Cada uno crea el suyo. |
| `venv/` | **No** | El entorno virtual se crea en cada computadora (pesa mucho y depende del sistema). |
| La base de datos `BeitShalomDB` | **No** | Vive dentro del SQL Server de cada computadora. Cada compañero la crea con los scripts. |

Por eso, cuando compartes el proyecto, tus compañeros reciben el código y los
scripts, y **cada uno crea su propia base de datos** en su propio SQL Server.
Los datos que tú registraste (solicitudes, mensajes, usuarios) no viajan con el
proyecto. Si todos quieren ver datos de ejemplo, cada uno puede cargar los
mismos datos ficticios con `flask --app app cargar-demo`.

---

## 2. SQL Server y el usuario "sa", explicado fácil

- **SQL Server** es el programa que guarda la base de datos. Se instala en cada computadora
  (en Windows normalmente; en Linux y Mac, dentro de Docker).
- **Instancia**: es "la copia" de SQL Server instalada. Casi siempre se llama `localhost`
  (instancia predeterminada) o `localhost\SQLEXPRESS` si instalaste la edición Express.
- **sa** (*system administrator*): es la cuenta **administradora** que trae SQL Server.
  Tiene todos los permisos. **Su contraseña la elige quien instala SQL Server en esa
  computadora**, por eso la contraseña de `sa` de tu computadora no sirve en la de otro
  compañero, y nunca deberías compartirla.

### Hay dos formas de conectarse

| Forma | ¿Dónde? | ¿Qué pones en `.env`? |
|---|---|---|
| **Autenticación de SQL Server** (usuario `sa`, la de la guía del profesor, sección 13) | Windows, Linux, Mac y Docker | `DB_TRUSTED_CONNECTION=no`, `DB_USER=sa` y `DB_PASSWORD=` con la contraseña de **tu** `sa`. |
| **Autenticación de Windows** (alternativa sin contraseña) | Solo en Windows | `DB_TRUSTED_CONNECTION=yes` y nada más. SQL Server confía en tu usuario de Windows. |

**No necesitas escribir esto a mano:** el asistente `python instalar.py` te pregunta
cuál usas (por defecto, `sa`), prueba la conexión y escribe tu `.env` por ti.

### Activar `sa` en Windows (modo mixto)

La guía del profesor pide tener activado el **modo mixto** y el usuario `sa` habilitado.
En Docker ya viene así. En Windows:

1. Abre SSMS, conéctate a `localhost` (o `localhost\SQLEXPRESS`) con *Windows Authentication*
   y marca *Trust server certificate*.
2. Clic derecho sobre el servidor → *Properties* → *Security* → *SQL Server and Windows
   Authentication mode* → *OK*.
3. *Security* → *Logins* → clic derecho sobre `sa` → *Properties*: escribe la contraseña en
   *General* y, en *Status*, elige *Login: Enabled*.
4. Reinicia SQL Server (clic derecho sobre el servidor → *Restart*, o desde `services.msc`).
5. Prueba a conectarte con *SQL Server Authentication*, usuario `sa` y tu contraseña.

Si instalas SQL Server desde cero, elige la instalación *Personalizada* y marca
*Modo mixto* ahí mismo.

En este proyecto la contraseña de `sa` va en el archivo privado `.env`, no dentro de
`database.py` como en el ejemplo de la guía: así el mismo código sirve en todas las
computadoras y ninguna contraseña viaja en el ZIP ni en GitHub.

### ¿Olvidaste la contraseña de sa?

- **Windows:** entra a SSMS con autenticación de Windows → *Security* → *Logins* → `sa` →
  *Properties* → escribe una contraseña nueva y vuelve a ejecutar `python instalar.py`.
- **Linux (instalación nativa):** detén el servicio y cambia la contraseña:
  `sudo systemctl stop mssql-server` y luego `sudo /opt/mssql/bin/mssql-conf set-sa-password`.
- **Docker:** la contraseña se fija al crear el contenedor. Si no la recuerdas, lo más simple
  es crear un contenedor nuevo (sección 4) y volver a ejecutar `python instalar.py`.

### (Opcional) No usar sa para la aplicación

`sa` puede hacer cualquier cosa, por eso en un sistema publicado conviene que la aplicación
use un usuario con permisos limitados. Después de crear la base de datos (con `sa`), puedes
ejecutar esto en SSMS cambiando la contraseña:

```sql
CREATE LOGIN beitshalom_app WITH PASSWORD = '<ESCRIBE_AQUI_UNA_CONTRASEÑA_SEGURA>';
USE BeitShalomDB;
CREATE USER beitshalom_app FOR LOGIN beitshalom_app;
ALTER ROLE db_datareader ADD MEMBER beitshalom_app;
ALTER ROLE db_datawriter ADD MEMBER beitshalom_app;
```

Luego en `.env`: `DB_USER=beitshalom_app` y su contraseña. (Para volver a ejecutar
`crear-bd` se necesita un usuario administrador como `sa`).

### ¿Y si queremos una sola base de datos para todo el grupo?

Es posible (una computadora o un servidor en la nube tiene SQL Server y los demás cambian
`DB_SERVER` a su dirección), pero hay que abrir el puerto 1433, crear un usuario por persona
y la base depende de que esa computadora esté encendida. **Para la clase se recomienda que
cada uno tenga su base local.**

---

## 3. Cómo compartir el proyecto

### Opción A (recomendada): GitHub

Quien tiene el proyecto (una sola vez):

1. Crear un repositorio **privado** en <https://github.com/new> (sin README).
2. En la carpeta `FundacionBeitShalom`, abrir una terminal y ejecutar:

   ```bash
   git init
   git add .
   git commit -m "Sistema de Registro de Colaboradores - Fundación Beit Shalom"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/FundacionBeitShalom.git
   git push -u origin main
   ```

   El archivo `.gitignore` ya evita que se suban `venv/` y `.env`.
3. En GitHub: *Settings* → *Collaborators* → *Add people* e invitar a cada compañero.

Cada compañero:

```bash
git clone https://github.com/TU_USUARIO/FundacionBeitShalom.git
```

Para trabajar en equipo: antes de empezar, `git pull`; al terminar, `git add .`,
`git commit -m "qué cambiaste"` y `git push`.

### Opción B: archivo ZIP

Comparte el archivo `FundacionBeitShalom_para_compartir.zip` (Drive, Teams, WhatsApp…).
Ya viene **sin** `venv/` y **sin** `.env`, y trae `GUIA_DE_INSTALACION.pdf` con el paso a paso.
Cada compañero lo descomprime y sigue esa guía (o la sección 4).

---

## 4. Lo que debe hacer cada compañero

### En Windows (como en la guía del profesor)

1. Instalar:
   - **Python 3.11 o superior**, recomendado 3.13 o 3.14 (en el instalador marcar *Add python.exe to PATH*).
   - **SQL Server 2022 o 2025, Developer o Express** y **SQL Server Management Studio (SSMS)**.
   - **ODBC Driver 18 for SQL Server** (página de descargas de Microsoft).
   - **Visual Studio Code**.
2. Activar el modo mixto y el usuario `sa` (sección 2).
3. Abrir la carpeta `FundacionBeitShalom` en VS Code y, en la terminal:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   python -m pip install -r requirements.txt
   python instalar.py
   flask --app app run --debug
   ```

   Si PowerShell no deja activar el entorno, ejecuta una vez:
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

   En `instalar.py`, pulsa Enter en *Elige 1 o 2* (opción 2: usuario `sa`) y escribe la
   contraseña de tu `sa`.

### En Linux o Mac (con Docker)

1. Instalar Python 3.11 o superior, Docker y el controlador **ODBC Driver 18 for SQL Server**
   (Mac: `brew install msodbcsql18`; Linux: paquete `msodbcsql18` de tu distribución).
2. Crear el SQL Server en Docker (solo la primera vez). Cambia `TuClave.Segura2026` por tu
   propia contraseña: mínimo 8 caracteres con mayúsculas, minúsculas y números (evita
   comillas, `!` y `$`):

   ```bash
   sudo docker run -d --name sqlserver -p 1433:1433 --restart unless-stopped -e 'ACCEPT_EULA=Y' -e 'MSSQL_SA_PASSWORD=TuClave.Segura2026' mcr.microsoft.com/mssql/server:2022-latest
   ```

   En Mac se escribe sin `sudo` y con `--platform linux/amd64` después de `--name sqlserver`.

3. En la carpeta del proyecto:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install -r requirements.txt
   python instalar.py
   flask --app app run --debug
   ```

   En `instalar.py` usa el usuario `sa` y la contraseña que pusiste en el paso 2.

### El asistente `instalar.py`

1. Comprueba Python, las librerías y el controlador ODBC.
2. Pregunta el servidor y la forma de conectarse, y **prueba la conexión**.
3. Crea **tu** `.env` (con una clave secreta nueva).
4. Crea la base de datos `BeitShalomDB` (scripts `sql/01` y `sql/02`).
5. Crea tu usuario del panel administrativo (tu propia contraseña).
6. Opcionalmente carga datos de demostración.

Al terminar, abre <http://127.0.0.1:5000> (sitio) y <http://127.0.0.1:5000/admin> (panel).

---

## 5. Uso diario

1. Encender SQL Server:
   - Windows: normalmente arranca solo.
   - Docker: `sudo systemctl start docker` y `sudo docker start sqlserver`
     (con `--restart unless-stopped` el contenedor arranca solo cuando Docker inicia;
     para que Docker inicie con la computadora: `sudo systemctl enable docker`).
2. Activar el entorno virtual (`.\venv\Scripts\Activate` o `source venv/bin/activate`).
3. `flask --app app run --debug`.

Para comprobar todo: `pytest -v` (las pruebas contra SQL Server se omiten si está apagado).

---

## 6. Problemas frecuentes

| Mensaje o síntoma | Causa | Solución |
|---|---|---|
| La página dice **"Servicio no disponible"** | SQL Server está apagado | Enciéndelo (sección 5) y recarga la página. |
| `Login timeout expired` | SQL Server apagado o servidor mal escrito | Revisa que esté encendido y el valor `DB_SERVER`. |
| `Login failed for user 'sa'` | Contraseña de `sa` incorrecta | Corrige `DB_PASSWORD` o ejecuta otra vez `python instalar.py`. |
| `Can't open lib 'ODBC Driver 18 for SQL Server'` | Falta el controlador ODBC | Instálalo (o usa `DB_DRIVER=ODBC Driver 17 for SQL Server` si tienes el 17). |
| `ModuleNotFoundError: No module named 'flask'` | El entorno virtual no está activo | Actívalo y ejecuta `python -m pip install -r requirements.txt`. |
| "El formulario expiró" | El formulario estuvo abierto mucho tiempo | Recarga la página. |
