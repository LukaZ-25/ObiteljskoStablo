import os
import sys
import socket
import threading
import webbrowser

import sqlite3
from flask import Flask, request, jsonify, render_template
from collections import deque

if getattr(sys, "frozen", False):
    # Kada radi kao zapakirani .exe (PyInstaller)
    EXE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, "_MEIPASS", EXE_DIR)
else:
    # Kada radi kao obična Python skripta
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = EXE_DIR

app = Flask(
    __name__,
    template_folder=os.path.join(BUNDLE_DIR, "templates"),
    static_folder=os.path.join(BUNDLE_DIR, "static"),
)
DB_PATH = os.path.join(EXE_DIR, "obitelj.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS persons (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT,
                gender TEXT CHECK(gender IN ('M', 'F')),
                birth_year INTEGER,
                death_year INTEGER,
                father_id TEXT REFERENCES persons(id) ON DELETE SET NULL,
                mother_id TEXT REFERENCES persons(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS partnerships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person1_id INTEGER NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
                person2_id INTEGER NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
                note TEXT
            );
        """)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/persons", methods=["GET"])
def get_persons():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM persons").fetchall()
        persons = [dict(r) for r in rows]
        return jsonify(persons)
    pass


@app.route("/api/person", methods=["POST"])
def add_person():
    data = request.get_json()
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO persons (first_name, last_name, gender, birth_year, death_year, father_id, mother_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("first_name"),
                data.get("last_name"),
                data.get("gender"),
                data.get("birth_year"),
                data.get("death_year"),
                data.get("father_id"),
                data.get("mother_id")
            ),
        )
        new_id = cursor.lastrowid
        return jsonify({"id": new_id}), 201
    # Vrati ID nove osobe i status 201: return jsonify({"id": cursor.lastrowid}), 201
    pass


@app.route("/api/person/<int:person_id>", methods=["PUT"])
def update_person(person_id):
    data = request.get_json()
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE persons
            SET first_name = ?, last_name = ?, gender = ?, birth_year = ?, death_year = ?, father_id = ?, mother_id = ?
            WHERE id = ?
            """,
            (
                data.get("first_name"),
                data.get("last_name"),
                data.get("gender"),
                data.get("birth_year"),
                data.get("death_year"),
                data.get("father_id"),
                data.get("mother_id"),
                person_id
            ),
        )
        new_id = cursor.lastrowid
        if cursor.rowcount == 0:
            return jsonify({"error": "osoba nije pronađena"}), 404
        return jsonify({"updated": person_id}), 200
    pass


@app.route("/api/person/<int:person_id>/children", methods=["GET"])
def get_person_children(person_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM persons WHERE father_id = ? OR mother_id = ?",
            (person_id, person_id)
        ).fetchall()
        return jsonify([dict (r) for r in rows])
    pass


@app.route("/api/person/<int:person_id>", methods=["DELETE"])
def delete_person(person_id):
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM persons WHERE id = ?",
            (person_id,)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "osoba nije pronađena"}), 404
        return jsonify({"deleted": person_id}), 200
    pass


@app.route("/api/partnership", methods=["POST"])
def add_partnership():
    data = request.get_json()
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO partnerships (person1_id, person2_id, note)
            VALUES (?, ?, ?)
            """,
            (
                data.get("person1_id"),
                data.get("person2_id"),
                data.get("note")
            ),
        )
        return jsonify({"id": cursor.lastrowid}), 201
    pass


@app.route("/api/partnership/<int:person_id>", methods=["DELETE"])
def delete_partnership(partnership_id):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM partnership WHERE partnership_id = ?", (partnership_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Parterstvo nije pronađeno"}), 404
        return jsonify({"deleted": partnership_id}), 200
    pass


@app.route("/api/tree", methods=["GET"])
def get_tree():
    with get_db() as conn:
        persons = conn.execute("SELECT * FROM persons").fetchall()
        partnerships = conn.execute("SELECT * FROM partnerships").fetchall()

    nodes = {}
    for p in persons:
        pid = str(p["id"])
        parents = []
        if p["father_id"]:
            parents.append(str(p["father_id"]))
        if p["mother_id"]:
            parents.append(str(p["mother_id"]))

        nodes[pid] = {
            "id": pid,
            "data": {
                "first name": p["first_name"] or "",
                "last name": p["last_name"] or "",
                "gender": p["gender"] or "M",
                "birth year": p["birth_year"] or "",
                "death year": p["death_year"] or ""
            },
            "rels": {
                "parents": parents,
                "spouses": [],
                "children": []
            }
        }

    for pid, node in nodes.items():
        for parent_id in node["rels"]["parents"]:
            if parent_id in nodes:
                nodes[parent_id]["rels"]["children"].append(pid)

    for part in partnerships:
        p1 = str(part["person1_id"])
        p2 = str(part["person2_id"])
        if p1 in nodes and p2 in nodes:
            if p2 not in nodes[p1]["rels"]["spouses"]:
                nodes[p1]["rels"]["spouses"].append(p2)
            if p1 not in nodes[p2]["rels"]["spouses"]:
                nodes[p2]["rels"]["spouses"].append(p1)

    return jsonify(list(nodes.values()))


@app.route("/api/tree/sync", methods=["POST"])
def sync_tree():
    tree_data = request.get_json()
    if not isinstance(tree_data, list):
        return jsonify({"error": "Očekivana je lista osoba"}), 400

    with get_db() as conn:
        # Privremeno gasimo provjeru stranih ključeva dok prepisujemo cijelo stablo
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute("DELETE FROM partnerships;")
        conn.execute("DELETE FROM persons;")

        # 1. Prepoznajemo tko je otac (M), a tko majka (F) za svaku osobu
        genders = {
            str(node["id"]): node.get("data", {}).get("gender", "M")
            for node in tree_data
        }

        # 2. Upisujemo sve osobe
        for node in tree_data:
            pid = str(node["id"])
            data = node.get("data", {})
            parents = node.get("rels", {}).get("parents", [])

            father_id = None
            mother_id = None
            for par_id in parents:
                par_id_str = str(par_id)
                if genders.get(par_id_str) == "F":
                    mother_id = par_id_str
                else:
                    father_id = par_id_str

            # Pretvaramo prazne stringove godina u None (NULL u bazi)
            birth_year = data.get("birth year") or None
            death_year = data.get("death year") or None

            conn.execute(
                """
                INSERT INTO persons (id, first_name, last_name, gender, birth_year, death_year, father_id, mother_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid,
                    data.get("first name") or "Nepoznato",
                    data.get("last name") or "",
                    genders[pid],
                    birth_year,
                    death_year,
                    father_id,
                    mother_id,
                ),
            )

        # 3. Upisujemo partnerstva (svaki par samo jednom)
        seen_pairs = set()
        for node in tree_data:
            p1 = str(node["id"])
            for spouse in node.get("rels", {}).get("spouses", []):
                p2 = str(spouse)
                pair = tuple(sorted([p1, p2]))
                if pair not in seen_pairs and p2 in genders:
                    seen_pairs.add(pair)
                    conn.execute(
                        "INSERT INTO partnerships (person1_id, person2_id) VALUES (?, ?)",
                        (pair[0], pair[1]),
                    )

        conn.execute("PRAGMA foreign_keys = ON;")

    return jsonify({"synced": len(tree_data)}), 200


@app.route("/api/full-tree", methods=["GET"])
def get_full_tree():
    with get_db() as conn:
        persons = [dict(r) for r in conn.execute("SELECT * FROM persons").fetchall()]
        partnerships = [dict(r) for r in conn.execute("SELECT * FROM partnerships").fetchall()]

    if not persons:
        return jsonify({"persons": [], "partnerships": []})

    # Pomoćne mape za brzi BFS prolaz
    person_map = {p["id"]: p for p in persons}
    children_map = {p["id"]: [] for p in persons}
    partners_map = {p["id"]: [] for p in persons}

    for p in persons:
        if p["father_id"] in children_map:
            children_map[p["father_id"]].append(p["id"])
        if p["mother_id"] in children_map:
            children_map[p["mother_id"]].append(p["id"])

    for part in partnerships:
        p1, p2 = part["person1_id"], part["person2_id"]
        if p1 in partners_map and p2 in partners_map:
            partners_map[p1].append(p2)
            partners_map[p2].append(p1)

    # BFS izračun generacija (kako je opisano u odjeljku 5 plana)
    generation = {}
    for start_id in person_map:
        if start_id in generation:
            continue
        generation[start_id] = 0
        queue = deque([start_id])

        while queue:
            curr = queue.popleft()
            g = generation[curr]

            # Roditelji idu jednu generaciju gore (g - 1)
            curr_p = person_map[curr]
            for par_id in (curr_p["father_id"], curr_p["mother_id"]):
                if par_id and par_id in person_map and par_id not in generation:
                    generation[par_id] = g - 1
                    queue.append(par_id)

            # Djeca idu jednu generaciju dolje (g + 1)
            for child_id in children_map[curr]:
                if child_id not in generation:
                    generation[child_id] = g + 1
                    queue.append(child_id)

            # Partner nasljeđuje istu generaciju (g)
            for partner_id in partners_map[curr]:
                if partner_id not in generation:
                    generation[partner_id] = g
                    queue.append(partner_id)

    # Normaliziramo da najstarija generacija uvijek počinje od 0
    min_gen = min(generation.values())
    for p in persons:
        p["generation"] = generation[p["id"]] - min_gen

    return jsonify({"persons": persons, "partnerships": partnerships})


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


if __name__ == "__main__":
    init_db()
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False)
