"""Servidor Flask de registro de asistentes para Cumbre Digital MX 2026."""

import os
import re
import sqlite3
import uuid

from flask import Flask, abort, g, redirect, render_template, request, url_for

# Ruta de la base de datos: por defecto evento.db en la raíz del proyecto.
# Se puede cambiar con la variable de entorno RUTA_BD (útil en Render con disco persistente).
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_BD = os.environ.get("RUTA_BD", os.path.join(DIRECTORIO_BASE, "evento.db"))

AREAS = ["Tecnología", "Marketing", "Negocios", "Emprendimiento"]
REGEX_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
LONGITUD_MAXIMA = 150

app = Flask(__name__)


# ---------- Base de datos ----------

def obtener_bd():
    """Devuelve la conexión a SQLite de la petición actual (una por petición)."""
    if "bd" not in g:
        g.bd = sqlite3.connect(RUTA_BD)
        g.bd.row_factory = sqlite3.Row
    return g.bd


@app.teardown_appcontext
def cerrar_bd(_error):
    """Cierra la conexión al terminar la petición."""
    bd = g.pop("bd", None)
    if bd is not None:
        bd.close()


def inicializar_bd():
    """Crea la tabla de asistentes si todavía no existe."""
    areas_sql = ", ".join(f"'{area}'" for area in AREAS)
    with sqlite3.connect(RUTA_BD) as bd:
        bd.execute(f"""
            CREATE TABLE IF NOT EXISTS asistentes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_registro TEXT    NOT NULL UNIQUE,
                nombre          TEXT    NOT NULL,
                email           TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                empresa         TEXT    NOT NULL,
                area            TEXT    NOT NULL CHECK (area IN ({areas_sql})),
                fecha_registro  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


# ---------- Validación ----------

def validar_registro(datos):
    """Valida los datos del formulario; regresa un diccionario campo -> mensaje de error."""
    errores = {}

    if not datos["nombre"]:
        errores["nombre"] = "El nombre completo es obligatorio."
    elif len(datos["nombre"]) > LONGITUD_MAXIMA:
        errores["nombre"] = f"El nombre no puede tener más de {LONGITUD_MAXIMA} caracteres."

    if not datos["email"]:
        errores["email"] = "El email es obligatorio."
    elif len(datos["email"]) > LONGITUD_MAXIMA or not REGEX_EMAIL.match(datos["email"]):
        errores["email"] = "El email no tiene un formato válido."

    if not datos["empresa"]:
        errores["empresa"] = "La empresa u organización es obligatoria."
    elif len(datos["empresa"]) > LONGITUD_MAXIMA:
        errores["empresa"] = f"La empresa no puede tener más de {LONGITUD_MAXIMA} caracteres."

    if datos["area"] not in AREAS:
        errores["area"] = "Selecciona un área de interés."

    return errores


def mostrar_formulario(datos=None, errores=None, error_general=None, codigo=200):
    """Renderiza el formulario conservando lo que el usuario ya escribió."""
    datos = datos or {"nombre": "", "email": "", "empresa": "", "area": ""}
    return render_template(
        "index.html",
        datos=datos,
        errores=errores or {},
        error_general=error_general,
        areas=AREAS,
    ), codigo


# ---------- Rutas ----------

@app.get("/")
def inicio():
    return mostrar_formulario()


@app.post("/registro")
def registro():
    datos = {
        "nombre": request.form.get("nombre", "").strip(),
        "email": request.form.get("email", "").strip(),
        "empresa": request.form.get("empresa", "").strip(),
        "area": request.form.get("area", "").strip(),
    }

    errores = validar_registro(datos)
    if errores:
        return mostrar_formulario(
            datos, errores, "Por favor corrige los campos marcados antes de continuar.", 400
        )

    bd = obtener_bd()
    try:
        # Se inserta con un número temporal y, en la misma transacción,
        # se reemplaza por REG-0001, REG-0002... derivado del id consecutivo.
        cursor = bd.execute(
            "INSERT INTO asistentes (numero_registro, nombre, email, empresa, area) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"TEMP-{uuid.uuid4().hex}", datos["nombre"], datos["email"],
             datos["empresa"], datos["area"]),
        )
        numero_registro = f"REG-{cursor.lastrowid:04d}"
        bd.execute(
            "UPDATE asistentes SET numero_registro = ? WHERE id = ?",
            (numero_registro, cursor.lastrowid),
        )
        bd.commit()
    except sqlite3.IntegrityError as error:
        bd.rollback()
        if "asistentes.email" in str(error):
            return mostrar_formulario(
                datos,
                {"email": "Este email ya está registrado."},
                "Ya existe un registro con este email.",
                409,
            )
        return mostrar_formulario(
            datos, None, "No se pudo guardar el registro. Revisa los datos e inténtalo de nuevo.", 400
        )
    except sqlite3.Error:
        bd.rollback()
        return mostrar_formulario(
            datos, None, "Ocurrió un error al guardar tu registro. Inténtalo de nuevo en unos minutos.", 500
        )

    # Patrón Post/Redirect/Get: recargar la confirmación no duplica el registro
    return redirect(url_for("confirmacion", numero_registro=numero_registro))


@app.get("/confirmacion/<numero_registro>")
def confirmacion(numero_registro):
    asistente = obtener_bd().execute(
        "SELECT numero_registro, nombre FROM asistentes WHERE numero_registro = ?",
        (numero_registro,),
    ).fetchone()
    if asistente is None:
        abort(404)
    return render_template("confirmacion.html", asistente=asistente)


@app.get("/admin")
def admin():
    bd = obtener_bd()
    asistentes = bd.execute(
        "SELECT numero_registro, nombre, email, empresa, area, fecha_registro "
        "FROM asistentes ORDER BY id DESC"
    ).fetchall()
    conteo_por_area = dict(
        bd.execute("SELECT area, COUNT(*) FROM asistentes GROUP BY area").fetchall()
    )
    return render_template(
        "admin.html", asistentes=asistentes, conteo_por_area=conteo_por_area, areas=AREAS
    )


@app.get("/salud")
def salud():
    return "ok"


@app.errorhandler(404)
def no_encontrado(_error):
    return mostrar_formulario(
        error_general="La página o el número de registro que buscas no existe.", codigo=404
    )


# La tabla se crea al importar el módulo, así funciona con `python app.py` y con gunicorn.
inicializar_bd()

if __name__ == "__main__":
    app.run(debug=True)
