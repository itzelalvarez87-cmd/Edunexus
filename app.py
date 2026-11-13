from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "edunexus-clave-local-cambiar")

DB = "aprende_mas.db"


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL DEFAULT '',
                clave TEXT NOT NULL,
                avatar TEXT DEFAULT '🎓',
                puntos INTEGER DEFAULT 0,
                aciertos INTEGER DEFAULT 0,
                retos INTEGER DEFAULT 0,
                usuario TEXT,
                nivel TEXT DEFAULT 'Preparatoria',
                record INTEGER DEFAULT 0
            )
        """)

        columnas = {
            fila["name"]
            for fila in conn.execute("PRAGMA table_info(usuarios)").fetchall()
        }

        if "usuario" not in columnas:
            conn.execute("ALTER TABLE usuarios ADD COLUMN usuario TEXT")

        if "nivel" not in columnas:
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN nivel TEXT DEFAULT 'Preparatoria'"
            )

        if "record" not in columnas:
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN record INTEGER DEFAULT 0"
            )

        if "avatar" not in columnas:
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN avatar TEXT DEFAULT '🎓'"
            )

        if "puntos" not in columnas:
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN puntos INTEGER DEFAULT 0"
            )

        if "aciertos" not in columnas:
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN aciertos INTEGER DEFAULT 0"
            )

        if "retos" not in columnas:
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN retos INTEGER DEFAULT 0"
            )

        if "correo" not in columnas:
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN correo TEXT DEFAULT ''"
            )

        # Asignar usuario a cuentas antiguas que no tenían ese campo.
        conn.execute("""
            UPDATE usuarios
            SET usuario = LOWER(REPLACE(nombre, ' ', '_'))
            WHERE usuario IS NULL OR usuario = ''
        """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS indice_usuario_unico
            ON usuarios(usuario)
        """)


init_db()


def respuesta_error(mensaje, codigo=400):
    return jsonify({"status": "error", "mensaje": mensaje}), codigo


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/api/registro", methods=["POST"])
def registro_api():
    data = request.get_json(silent=True) or {}

    nombre = str(data.get("nombre", "")).strip()
    usuario = str(data.get("usuario", "")).strip().lower()
    correo = str(data.get("correo", "")).strip().lower()
    clave = str(data.get("clave", ""))
    nivel = str(data.get("nivel", "Preparatoria")).strip()
    avatar = str(data.get("avatar", "🎓")).strip()

    if not nombre or not usuario or not clave:
        return respuesta_error("Completa los campos obligatorios.")

    if len(usuario) < 3:
        return respuesta_error("El usuario debe tener al menos 3 caracteres.")

    if len(clave) < 4:
        return respuesta_error("La contraseña debe tener al menos 4 caracteres.")

    if nivel not in ["Secundaria", "Preparatoria"]:
        nivel = "Preparatoria"

    if not avatar:
        avatar = "🎓"

    clave_segura = generate_password_hash(clave)

    try:
        with conectar() as conn:
            conn.execute("""
                INSERT INTO usuarios
                (nombre, usuario, correo, clave, avatar, nivel)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, usuario, correo, clave_segura, avatar, nivel))

        return jsonify({
            "status": "ok",
            "mensaje": "¡Cuenta creada! Ya puedes iniciar sesión."
        })

    except sqlite3.IntegrityError:
        return respuesta_error("Ese nombre de usuario ya está registrado.")


@app.route("/api/login", methods=["POST"])
def login_api():
    data = request.get_json(silent=True) or {}

    usuario = str(data.get("usuario", "")).strip().lower()
    clave = str(data.get("clave", ""))

    if not usuario or not clave:
        return respuesta_error("Escribe tu usuario y contraseña.")

    with conectar() as conn:
        cuenta = conn.execute(
            "SELECT * FROM usuarios WHERE usuario = ?",
            (usuario,)
        ).fetchone()

        if not cuenta:
            return respuesta_error("Usuario o contraseña incorrectos.", 401)

        clave_guardada = cuenta["clave"]

        # Compatibilidad con cuentas antiguas que guardaban la contraseña
        # sin cifrar: si coincide, se actualiza a un hash seguro.
        try:
            valida = check_password_hash(clave_guardada, clave)
        except (ValueError, TypeError):
            valida = False

        if not valida and clave_guardada == clave:
            valida = True
            conn.execute(
                "UPDATE usuarios SET clave = ? WHERE id = ?",
                (generate_password_hash(clave), cuenta["id"])
            )

        if not valida:
            return respuesta_error("Usuario o contraseña incorrectos.", 401)

        session["usuario_id"] = cuenta["id"]

        perfil = conn.execute("""
            SELECT id, nombre, usuario, correo, avatar, nivel,
                   puntos, aciertos, retos, record
            FROM usuarios
            WHERE id = ?
        """, (cuenta["id"],)).fetchone()

    return jsonify({
        "status": "ok",
        "mensaje": "¡Bienvenido a EduNexus!",
        "perfil": dict(perfil)
    })


@app.route("/api/perfil", methods=["GET"])
def perfil_api():
    if "usuario_id" not in session:
        return respuesta_error("Inicia sesión para continuar.", 401)

    with conectar() as conn:
        perfil = conn.execute("""
            SELECT id, nombre, usuario, correo, avatar, nivel,
                   puntos, aciertos, retos, record
            FROM usuarios
            WHERE id = ?
        """, (session["usuario_id"],)).fetchone()

    if not perfil:
        session.clear()
        return respuesta_error("La cuenta no existe.", 404)

    return jsonify({"status": "ok", "perfil": dict(perfil)})


@app.route("/api/resultado", methods=["POST"])
def guardar_resultado():
    if "usuario_id" not in session:
        return respuesta_error("Inicia sesión para guardar tu resultado.", 401)

    data = request.get_json(silent=True) or {}

    try:
        aciertos = int(data.get("aciertos", 0))
        total = int(data.get("total", 0))
    except (ValueError, TypeError):
        return respuesta_error("El resultado enviado no es válido.")

    if total < 1 or aciertos < 0 or aciertos > total:
        return respuesta_error("Revisa el número de respuestas.")

    materia = str(data.get("materia", "General")).strip()
    puntos = aciertos * 5
    porcentaje = round((aciertos / total) * 100)

    with conectar() as conn:
        conn.execute("""
            UPDATE usuarios
            SET puntos = puntos + ?,
                aciertos = aciertos + ?,
                retos = retos + 1,
                record = MAX(record, ?)
            WHERE id = ?
        """, (puntos, aciertos, porcentaje, session["usuario_id"]))

    return jsonify({
        "status": "ok",
        "mensaje": "Resultado guardado.",
        "puntos_ganados": puntos,
        "porcentaje": porcentaje,
        "materia": materia
    })


@app.route("/api/records", methods=["GET"])
def records_api():
    with conectar() as conn:
        usuarios = conn.execute("""
            SELECT nombre, usuario, avatar, puntos, aciertos, retos, record
            FROM usuarios
            ORDER BY record DESC, puntos DESC, nombre ASC
            LIMIT 20
        """).fetchall()

    return jsonify({
        "status": "ok",
        "records": [dict(fila) for fila in usuarios]
    })


@app.route("/api/logout", methods=["POST"])
def logout_api():
    session.clear()
    return jsonify({"status": "ok", "mensaje": "Sesión cerrada."})

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)