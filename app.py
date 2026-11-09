import os
import sqlite3
import unicodedata
from datetime import date

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   url_for)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "jugadores.db"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-de-desarrollo")

# Datos de identificación que se muestran en el footer
DATOS = {
    "curso": "Desarrollo para front ed",
    "nombre": "Coral Martinez Sanchez",
    "codigo": "225385497",
    "correo": "per0126@hotmail.com",
}

TITULOS = ["Sin título", "CM", "FM", "IM", "GM"]

SEMILLA = [
    ("Magnus Carlsen", "Noruega", 2830, "GM"),
    ("Hikaru Nakamura", "Estados Unidos", 2794, "GM"),
    ("Judit Polgár", "Hungría", 2735, "GM"),
    ("Ana López", "México", 1850, "CM"),
    ("Luis Hernández", "México", 1420, "Sin título"),
]


def normalizar(texto):
    """Minúsculas y sin acentos, para comparar búsquedas."""
    base = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea la tabla y, si está vacía, inserta datos de ejemplo."""
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            pais TEXT NOT NULL,
            rating INTEGER NOT NULL,
            titulo TEXT NOT NULL DEFAULT 'Sin título',
            fecha_registro TEXT NOT NULL
        )"""
    )
    if db.execute("SELECT COUNT(*) FROM jugadores").fetchone()[0] == 0:
        hoy = date.today().isoformat()
        db.executemany(
            "INSERT INTO jugadores (nombre, pais, rating, titulo, fecha_registro) "
            "VALUES (?, ?, ?, ?, ?)",
            [(n, p, r, t, hoy) for n, p, r, t in SEMILLA],
        )
    db.commit()
    db.close()


def leer_formulario():
    """Devuelve (datos, errores) a partir del formulario."""
    nombre = request.form.get("nombre", "").strip()
    pais = request.form.get("pais", "").strip()
    titulo = request.form.get("titulo", "Sin título")
    rating_txt = request.form.get("rating", "").strip()
    errores = []

    if not nombre:
        errores.append("El nombre es obligatorio.")
    if not pais:
        errores.append("El país es obligatorio.")
    if titulo not in TITULOS:
        errores.append("Título no válido.")
    try:
        rating = int(rating_txt)
        if not 0 <= rating <= 3000:
            errores.append("El rating debe estar entre 0 y 3000.")
    except ValueError:
        rating = None
        errores.append("El rating debe ser un número entero.")

    datos = {"nombre": nombre, "pais": pais, "rating": rating_txt, "titulo": titulo}
    if not errores:
        datos["rating"] = rating
    return datos, errores


@app.context_processor
def inyectar_datos():
    return {"datos": DATOS}


# ---- Consultar todos los registros ----
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    filas = get_db().execute("SELECT * FROM jugadores ORDER BY rating DESC").fetchall()
    if q:
        # Búsqueda sin distinguir mayúsculas ni acentos
        buscado = normalizar(q)
        filas = [f for f in filas
                 if buscado in normalizar(f["nombre"]) or buscado in normalizar(f["pais"])]
    return render_template("index.html", jugadores=filas, q=q)


# ---- Consultar un registro individual ----
@app.route("/jugador/<int:jid>")
def detalle(jid):
    fila = get_db().execute("SELECT * FROM jugadores WHERE id = ?", (jid,)).fetchone()
    if fila is None:
        abort(404)
    return render_template("detalle.html", j=fila)


# ---- Agregar ----
@app.route("/jugador/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        datos, errores = leer_formulario()
        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("form.html", j=datos, titulos=TITULOS,
                                   accion="Agregar jugador")
        db = get_db()
        cur = db.execute(
            "INSERT INTO jugadores (nombre, pais, rating, titulo, fecha_registro) "
            "VALUES (?, ?, ?, ?, ?)",
            (datos["nombre"], datos["pais"], datos["rating"], datos["titulo"],
             date.today().isoformat()),
        )
        db.commit()
        flash("Jugador agregado correctamente.", "ok")
        return redirect(url_for("detalle", jid=cur.lastrowid))
    vacio = {"nombre": "", "pais": "", "rating": "", "titulo": "Sin título"}
    return render_template("form.html", j=vacio, titulos=TITULOS,
                           accion="Agregar jugador")


# ---- Editar ----
@app.route("/jugador/<int:jid>/editar", methods=["GET", "POST"])
def editar(jid):
    db = get_db()
    fila = db.execute("SELECT * FROM jugadores WHERE id = ?", (jid,)).fetchone()
    if fila is None:
        abort(404)
    if request.method == "POST":
        datos, errores = leer_formulario()
        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("form.html", j=datos, titulos=TITULOS,
                                   accion="Editar jugador")
        db.execute(
            "UPDATE jugadores SET nombre=?, pais=?, rating=?, titulo=? WHERE id=?",
            (datos["nombre"], datos["pais"], datos["rating"], datos["titulo"], jid),
        )
        db.commit()
        flash("Jugador actualizado.", "ok")
        return redirect(url_for("detalle", jid=jid))
    return render_template("form.html", j=fila, titulos=TITULOS,
                           accion="Editar jugador")


# ---- Eliminar ----
@app.route("/jugador/<int:jid>/eliminar", methods=["POST"])
def eliminar(jid):
    db = get_db()
    cur = db.execute("DELETE FROM jugadores WHERE id = ?", (jid,))
    db.commit()
    if cur.rowcount == 0:
        abort(404)
    flash("Jugador eliminado.", "ok")
    return redirect(url_for("index"))


@app.errorhandler(404)
def no_encontrado(_e):
    return render_template("404.html"), 404


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
