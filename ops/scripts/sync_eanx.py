"""Carga cursos, módulos y lecciones de EAN X en Neo4j."""

import argparse
import hashlib
import json
from pathlib import Path

from neo4j import GraphDatabase
from src.config.settings import get_settings


def identifier(*parts):
    text = json.dumps(parts, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prepare(payload):
    courses, modules, lessons = [], [], []
    seen_courses, seen_modules, seen_lessons = set(), set(), set()

    for course in payload["cursos"]:
        course_id = str(course["course_id"]).strip()
        if not course_id or course_id in seen_courses:
            raise ValueError(f"Identificador de curso inválido o repetido: {course_id}")
        seen_courses.add(course_id)

        text_parts = [
            course.get("titulo"),
            course.get("descripcion"),
            course.get("tematicas_palabras_clave"),
        ]

        courses.append({
            "eanx_id": course_id,
            "titulo": course.get("titulo"),
            "descripcion": course.get("descripcion"),
            "palabras_clave": course.get("tematicas_palabras_clave"),
            "precio_cop": course.get("precio_cop"),
            "duracion_visible": course.get("duracion_visible"),
            "url_curso_probable": course.get("url_curso_probable"),
            "instructor": course.get("instructor"),
            "texto_semantico": "\n\n".join(
                str(value).strip() for value in text_parts if value
            ),
            "origen": "EANX_JSON",
        })

        for module in course.get("modulos", []):
            module_id = identifier(course_id, module["posicion"])
            if module_id in seen_modules:
                raise ValueError(f"Posición de módulo repetida en {course_id}")
            seen_modules.add(module_id)

            modules.append({
                "modulo_id": module_id,
                "eanx_id": course_id,
                "posicion": module["posicion"],
                "nombre": module.get("nombre"),
                "descripcion": module.get("descripcion"),
                "texto_semantico": "\n\n".join(
                    str(value).strip()
                    for value in [
                        course.get("titulo"),
                        module.get("nombre"),
                        module.get("descripcion"),
                    ] if value
                ),
                "origen": "EANX_JSON",
            })

            for lesson in module.get("lecciones", []):
                lesson_id = identifier(
                    module_id, lesson.get("id") or lesson["posicion"]
                )
                if lesson_id in seen_lessons:
                    raise ValueError(f"Lección repetida en módulo {module_id}")
                seen_lessons.add(lesson_id)

                lessons.append({
                    "leccion_id": lesson_id,
                    "modulo_id": module_id,
                    "id_origen": lesson.get("id"),
                    "posicion": lesson["posicion"],
                    "nombre": lesson.get("nombre"),
                    "tipo_original": lesson.get("tipo_original"),
                    "tipo_normalizado": lesson.get("tipo_normalizado"),
                    "origen": "EANX_JSON",
                })

    return courses, modules, lessons


QUERIES = [
    """
    UNWIND $rows AS row
    MERGE (c:FormacionEANX {eanx_id: row.eanx_id})
    SET c += row, c.actualizado_en = datetime()
    RETURN count(c) AS procesados
    """,
    """
    UNWIND $rows AS row
    MATCH (c:FormacionEANX {eanx_id: row.eanx_id})
    MERGE (m:ModuloEANX {modulo_id: row.modulo_id})
    SET m += row, m.actualizado_en = datetime()
    MERGE (c)-[:TIENE_MODULO]->(m)
    RETURN count(m) AS procesados
    """,
    """
    UNWIND $rows AS row
    MATCH (m:ModuloEANX {modulo_id: row.modulo_id})
    MERGE (l:LeccionEANX {leccion_id: row.leccion_id})
    SET l += row, l.actualizado_en = datetime()
    MERGE (m)-[:TIENE_LECCION]->(l)
    RETURN count(l) AS procesados
    """,
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        default="data/raw/eanx/eanx_contenido_cursos.json",
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    payload = json.loads(Path(args.file).read_text(encoding="utf-8-sig"))
    groups = prepare(payload)

    for label, rows in zip(
        ["FormacionEANX", "ModuloEANX", "LeccionEANX"], groups
    ):
        print(f"{label}: {len(rows)} registros preparados")

    if not args.write:
        print("Validación OK. No se escribió en Neo4j.")
        return

    settings = get_settings()
    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(
            settings.neo4j_user,
            settings.neo4j_password.get_secret_value(),
        ),
    ) as driver:
        driver.verify_connectivity()
        with driver.session(database=settings.neo4j_database) as session:
            constraints = [
                ("eanx_curso_id_unique", "FormacionEANX", "eanx_id"),
                ("eanx_modulo_id_unique", "ModuloEANX", "modulo_id"),
                ("eanx_leccion_id_unique", "LeccionEANX", "leccion_id"),
            ]
            for name, label, property_name in constraints:
                session.run(
                    f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE"
                ).consume()

            for query, rows in zip(QUERIES, groups):
                processed = 0
                for start in range(0, len(rows), 100):
                    record = session.execute_write(
                        lambda tx, batch: tx.run(
                            query, rows=batch
                        ).single(),
                        rows[start:start + 100],
                    )
                    processed += record["procesados"]
                if processed != len(rows):
                    raise RuntimeError(
                        f"Carga incompleta: {processed}/{len(rows)}"
                    )
                print(f"Procesados: {processed}")

    print("Carga EAN X: OK")


if __name__ == "__main__":
    main()
