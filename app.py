"""Servidor Flask de registro de asistentes para Cumbre Digital MX 2026."""

import os
import re
import uuid

import psycopg
from dotenv import load_dotenv
from flask import Flask, abort, g, redirect, render_template, request, url_for
from psycopg.rows import dict_row

# En local lee DATABASE_URL desde .env; en Render no hay .env y se usa la variable de entorno.
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Falta la variable de entorno DATABASE_URL. "
        "En local copia .env.example a .env y pon tu cadena de conexión de Supabase; "
        "en Render agrégala en Environment."
    )

AREAS = ["Tecnología", "Marketing", "Negocios", "Emprendimiento"]
REGEX_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
LONGITUD_MAXIMA = 150

app = Flask(__name__)


# ---------- Base de datos ----------

def obtener_bd():
    """Devuelve la conexión a PostgreSQL de la petición actual (una por petición)."""
    if "bd" not in g:
        g.bd = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    return g.bd


@app.teardown_appcontext
def cerrar_bd(_error):
    """Cierra la conexión al terminar la petición."""
    bd = g.pop("bd", None)
    if bd is not None:
        bd.close()


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
        # En minúsculas para que el email único no distinga mayúsculas
        "email": request.form.get("email", "").strip().lower(),
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
        id_asistente = bd.execute(
            "INSERT INTO asistentes (numero_registro, nombre, email, empresa, area_interes) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (f"TEMP-{uuid.uuid4().hex}", datos["nombre"], datos["email"],
             datos["empresa"], datos["area"]),
        ).fetchone()["id"]
        numero_registro = f"REG-{id_asistente:04d}"
        bd.execute(
            "UPDATE asistentes SET numero_registro = %s WHERE id = %s",
            (numero_registro, id_asistente),
        )
        bd.commit()
    except psycopg.errors.UniqueViolation as error:
        bd.rollback()
        if error.diag.constraint_name == "asistentes_email_key":
            return mostrar_formulario(
                datos,
                {"email": "Este email ya está registrado."},
                "Ya existe un registro con este email.",
                409,
            )
        return mostrar_formulario(
            datos, None, "No se pudo guardar el registro. Revisa los datos e inténtalo de nuevo.", 400
        )
    except psycopg.Error:
        bd.rollback()
        return mostrar_formulario(
            datos, None, "Ocurrió un error al guardar tu registro. Inténtalo de nuevo en unos minutos.", 500
        )

    # Patrón Post/Redirect/Get: recargar la confirmación no duplica el registro
    return redirect(url_for("confirmacion", numero_registro=numero_registro))


@app.get("/confirmacion/<numero_registro>")
def confirmacion(numero_registro):
    asistente = obtener_bd().execute(
        "SELECT numero_registro, nombre FROM asistentes WHERE numero_registro = %s",
        (numero_registro,),
    ).fetchone()
    if asistente is None:
        abort(404)
    return render_template("confirmacion.html", asistente=asistente)


@app.get("/admin")
def admin():
    bd = obtener_bd()
    asistentes = bd.execute(
        "SELECT numero_registro, nombre, email, empresa, area_interes AS area, "
        "to_char(fecha_registro, 'YYYY-MM-DD HH24:MI') AS fecha_registro "
        "FROM asistentes ORDER BY id DESC"
    ).fetchall()
    conteo_por_area = {
        fila["area"]: fila["total"]
        for fila in bd.execute(
            "SELECT area_interes AS area, COUNT(*) AS total "
            "FROM asistentes GROUP BY area_interes"
        ).fetchall()
    }
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


@app.errorhandler(psycopg.OperationalError)
def error_de_conexion(_error):
    """Fallo al conectar con la base de datos (por ejemplo, Supabase no responde)."""
    return mostrar_formulario(
        error_general="No pudimos conectar con la base de datos. Inténtalo de nuevo en unos minutos.",
        codigo=503,
    )


if __name__ == "__main__":
    app.run(debug=True)
