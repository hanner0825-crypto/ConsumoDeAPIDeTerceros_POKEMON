"""Backend Flask: intermediario con PokéAPI + CRUD de Pokémon favoritos (SQLite)."""
import sqlite3

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

POKEAPI_URL = "https://pokeapi.co/api/v2/pokemon"
DB_PATH = "pokemon.db"

app = Flask(__name__)
CORS(app)  # permite que el frontend (otro origen) consuma este backend


# ---------------------------------------------------------------- Base de datos
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS favoritos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pokemon_id INTEGER NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                apodo TEXT,
                nota TEXT
            )
            """
        )


# ---------------------------------------------------------------- Utilidades
def consultar_pokemon(identificador):
    """Consulta PokéAPI y devuelve un dict simplificado, o None si no existe."""
    resp = requests.get(f"{POKEAPI_URL}/{str(identificador).lower().strip()}", timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    d = resp.json()
    return {
        "id": d["id"],
        "nombre": d["name"],
        "tipos": [t["type"]["name"] for t in d["types"]],
        "altura_m": d["height"] / 10,
        "peso_kg": d["weight"] / 10,
        "imagen": d["sprites"]["other"]["official-artwork"]["front_default"]
        or d["sprites"]["front_default"],
        "estadisticas": {s["stat"]["name"]: s["base_stat"] for s in d["stats"]},
    }


def error(mensaje, codigo):
    return jsonify({"error": mensaje}), codigo


# ---------------------------------------------------------------- Intermediario PokéAPI
@app.get("/api/pokemon")
def listar_pokemon():
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    try:
        resp = requests.get(POKEAPI_URL, params={"limit": limit, "offset": offset}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return error("No se pudo consultar PokéAPI", 502)
    datos = resp.json()
    return jsonify(
        {
            "total": datos["count"],
            "resultados": [
                {"id": int(r["url"].rstrip("/").split("/")[-1]), "nombre": r["name"]}
                for r in datos["results"]
            ],
        }
    )


@app.get("/api/pokemon/<identificador>")
def obtener_pokemon(identificador):
    try:
        pokemon = consultar_pokemon(identificador)
    except requests.RequestException:
        return error("No se pudo consultar PokéAPI", 502)
    if pokemon is None:
        return error("Pokémon no encontrado", 404)
    return jsonify(pokemon)


# ---------------------------------------------------------------- CRUD de favoritos
@app.get("/api/favoritos")
def listar_favoritos():
    with get_db() as conn:
        filas = conn.execute("SELECT * FROM favoritos ORDER BY id").fetchall()
    return jsonify([dict(f) for f in filas])


@app.get("/api/favoritos/<int:fav_id>")
def obtener_favorito(fav_id):
    with get_db() as conn:
        fila = conn.execute("SELECT * FROM favoritos WHERE id = ?", (fav_id,)).fetchone()
    if fila is None:
        return error("Favorito no encontrado", 404)
    return jsonify(dict(fila))


@app.post("/api/favoritos")
def crear_favorito():
    datos = request.get_json(silent=True) or {}
    identificador = datos.get("pokemon")  # nombre o número del Pokémon
    if not identificador:
        return error("El campo 'pokemon' (nombre o número) es obligatorio", 400)

    try:
        pokemon = consultar_pokemon(identificador)
    except requests.RequestException:
        return error("No se pudo consultar PokéAPI", 502)
    if pokemon is None:
        return error("Ese Pokémon no existe en PokéAPI", 404)

    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO favoritos (pokemon_id, nombre, apodo, nota) VALUES (?, ?, ?, ?)",
                (pokemon["id"], pokemon["nombre"], datos.get("apodo"), datos.get("nota")),
            )
            nuevo_id = cur.lastrowid
    except sqlite3.IntegrityError:
        return error("Ese Pokémon ya está en favoritos", 409)

    return jsonify({"id": nuevo_id, **pokemon_a_fila(pokemon, datos)}), 201


def pokemon_a_fila(pokemon, datos):
    return {
        "pokemon_id": pokemon["id"],
        "nombre": pokemon["nombre"],
        "apodo": datos.get("apodo"),
        "nota": datos.get("nota"),
    }


@app.put("/api/favoritos/<int:fav_id>")
def actualizar_favorito(fav_id):
    datos = request.get_json(silent=True) or {}
    with get_db() as conn:
        fila = conn.execute("SELECT * FROM favoritos WHERE id = ?", (fav_id,)).fetchone()
        if fila is None:
            return error("Favorito no encontrado", 404)
        apodo = datos.get("apodo", fila["apodo"])
        nota = datos.get("nota", fila["nota"])
        conn.execute("UPDATE favoritos SET apodo = ?, nota = ? WHERE id = ?", (apodo, nota, fav_id))
    return obtener_favorito(fav_id)


@app.delete("/api/favoritos/<int:fav_id>")
def eliminar_favorito(fav_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM favoritos WHERE id = ?", (fav_id,))
    if cur.rowcount == 0:
        return error("Favorito no encontrado", 404)
    return jsonify({"mensaje": "Favorito eliminado"})


@app.get("/")
def inicio():
    return jsonify(
        {
            "mensaje": "API Pokémon con Flask",
            "rutas": [
                "GET /api/pokemon",
                "GET /api/pokemon/<nombre_o_id>",
                "GET|POST /api/favoritos",
                "GET|PUT|DELETE /api/favoritos/<id>",
            ],
        }
    )


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)