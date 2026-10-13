"""Genera embeddings académicos locales para los cinco catálogos."""

import argparse
import hashlib
import re
import unicodedata

import numpy as np
from neo4j import GraphDatabase

from src.config.settings import get_settings


MODEL_NAME = "intfloat/multilingual-e5-small"
TEXT_VERSION = "academic_v1"
UNIT_TEXT_VERSION = "academic_v2_syllabus_v24"

CATALOGS = [
    ("ProgramaOficial", "programa_id"),
    ("UnidadEstudio", "unidad_id"),
    ("Formacion", "formacion_id"),
    ("FormacionEANX", "eanx_id"),
    ("ModuloEANX", "modulo_id"),
]


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def combine(values):
    result = []
    seen = set()

    for value in values:
        value = clean(value)
        comparison = value.casefold()

        if value and comparison not in seen:
            seen.add(comparison)
            result.append(value)

    return "\n".join(result)


def meaningful_lesson(value):
    value = clean(value)
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    ).casefold()

    generic = (
        "presentacion",
        "nuestro experto",
        "nuestra experta",
        "reglas de juego",
        "foro de discusion",
        "evaluacion",
        "autoevaluacion",
        "inicio ruta",
        "contenido",
    )

    return bool(value) and not any(
        normalized.startswith(prefix)
        for prefix in generic
    )


def text_for(label, properties, lessons):
    p = properties

    if label == "ProgramaOficial":
        # Regla del proyecto: solo estos dos campos SNIES.
        return combine([
            p.get("snies_descripcion_abreviada"),
            p.get("snies_distincion_genero"),
        ])

    if label == "UnidadEstudio":
        if p.get("requiere_revision_contenido"):
            return ""
        # La reconstrucción v24 ya depuró el texto y retiró duraciones.
        # No reconstruirlo desde campos que pueden contener otra versión.
        if p.get("esquema_identidad") == "fuente_v24":
            return clean(p.get("texto_semantico"))
        return combine([
            p.get("nombre_unidad_estudio"),
            p.get("descripcion_unidad"),
            p.get("resultado_aprendizaje_unidad"),
            p.get("contenidos_unidad"),
            p.get("competencia_programa"),
        ])

    if label == "Formacion":
        # Excluye códigos, períodos y áreas administrativas.
        return combine([
            p.get("nombre"),
        ])

    if label == "FormacionEANX":
        return combine([
            p.get("titulo"),
            p.get("descripcion"),
            p.get("palabras_clave"),
        ])

    if label == "ModuloEANX":
        return combine([
            p.get("nombre"),
            p.get("descripcion"),
            *[
                lesson.get("nombre")
                for lesson in lessons
                if meaningful_lesson(lesson.get("nombre"))
            ],
        ])

    raise ValueError(f"Catálogo no soportado: {label}")


def encode_texts(model, texts, batch_size):
    """Fragmenta textos largos y combina sus vectores normalizados."""
    tokenizer = model.tokenizer
    budget = model.max_seq_length - 16

    if budget < 32:
        raise ValueError("Longitud máxima del modelo inesperada")

    chunks = []
    owner_ranges = []

    for text in texts:
        tokens = tokenizer.encode(
            text,
            add_special_tokens=False,
        )

        if not tokens:
            raise ValueError("El texto no produjo tokens")

        first = len(chunks)

        for start in range(0, len(tokens), budget):
            chunk = tokenizer.decode(
                tokens[start:start + budget],
                skip_special_tokens=True,
            )
            chunks.append(f"passage: {chunk}")

        owner_ranges.append((first, len(chunks)))

    vectors = model.encode(
        chunks,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    output = []

    for first, last in owner_ranges:
        vector = np.mean(vectors[first:last], axis=0)
        norm = np.linalg.norm(vector)

        if (
            vector.shape != (384,)
            or not np.isfinite(vector).all()
            or norm == 0
        ):
            raise ValueError("Embedding inválido")

        output.append((vector / norm).tolist())

    return output


def read_catalog(session, label, key, limit):
    # Los nombres de etiquetas y llaves provienen de CATALOGS.
    invalid = session.run(
        f"MATCH (n:{label}) "
        f"RETURN count(n) - count(DISTINCT n.{key}) AS invalid"
    ).single()["invalid"]

    if invalid:
        raise ValueError(
            f"{label}: hay llaves nulas o duplicadas en {key}"
        )

    query = f"MATCH (n:{label}) "
    if label == "UnidadEstudio":
        query += "WHERE coalesce(n.requiere_revision_contenido, false) = false "

    if label == "ModuloEANX":
        query += """
        OPTIONAL MATCH (n)-[:TIENE_LECCION]->(l:LeccionEANX)
        WITH n, l ORDER BY l.posicion
        WITH n, collect({
            nombre: l.nombre,
            posicion: l.posicion
        }) AS lessons
        """
    else:
        query += "WITH n, [] AS lessons "

    query += (
        f"RETURN n.{key} AS id, properties(n) AS props, lessons "
        f"ORDER BY n.{key}"
    )

    if limit is not None:
        query += " LIMIT $limit"

    rows = []
    empty = 0

    for record in session.run(query, limit=limit):
        text = text_for(
            label,
            record["props"],
            record["lessons"],
        )

        if not text:
            empty += 1
            continue

        rows.append({
            "id": record["id"],
            "text": text,
            "hash": hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest(),
        })

    return rows, empty


def write_catalog(session, model, label, key, rows, batch_size):
    eligibility = (
        "WHERE coalesce(n.requiere_revision_contenido, false) = false"
        if label == "UnidadEstudio" else ""
    )
    query = f"""
    UNWIND $rows AS row
    MATCH (n:{label} {{{key}: row.id}})
    {eligibility}
    SET n.embedding = row.vector,
        n.embedding_text = row.text,
        n.embedding_text_hash = row.hash,
        n.embedding_model = $model,
        n.embedding_dimensions = 384,
        n.embedding_text_version = $version,
        n.embedding_updated_at = datetime()
    RETURN count(n) AS updated
    """

    total = 0

    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]

        vectors = encode_texts(
            model,
            [row["text"] for row in batch],
            batch_size,
        )

        writes = [
            {**row, "vector": vector}
            for row, vector in zip(
                batch,
                vectors,
                strict=True,
            )
        ]

        def save(tx):
            record = tx.run(
                query,
                rows=writes,
                model=MODEL_NAME,
                version=UNIT_TEXT_VERSION if label == "UnidadEstudio" else TEXT_VERSION,
            ).single()
            # Lanzar dentro de la transacción para revertir un lote incompleto.
            if record["updated"] != len(batch):
                raise RuntimeError(f"Escritura incompleta en {label}; lote revertido")
            return record["updated"]

        updated = session.execute_write(save)

        if updated != len(batch):
            raise RuntimeError(
                f"Escritura incompleta en {label}: "
                f"{updated}/{len(batch)}"
            )

        total += updated
        print(
            f"{label}: {total}/{len(rows)}",
            flush=True,
        )

    return total


def main():
    parser = argparse.ArgumentParser(
        description="Genera embeddings de los catálogos académicos."
    )
    parser.add_argument(
        "--model-path",
        default=(
            "/home/dagon/BD_Grafos_EAN/models/"
            "multilingual-e5-small"
        ),
    )
    parser.add_argument(
        "--catalog",
        choices=[label for label, _ in CATALOGS],
        help="Procesa únicamente el catálogo seleccionado.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Máximo de nodos por catálogo para una prueba.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Genera y guarda vectores; reemplaza los existentes.",
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit debe ser positivo")

    if args.batch_size < 1:
        parser.error("--batch-size debe ser positivo")

    settings = get_settings()
    selected = [
        (label, key)
        for label, key in CATALOGS
        if args.catalog is None or label == args.catalog
    ]

    prepared = []

    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(
            settings.neo4j_user,
            settings.neo4j_password.get_secret_value(),
        ),
    ) as driver:
        driver.verify_connectivity()

        with driver.session(
            database=settings.neo4j_database
        ) as session:
            for label, key in selected:
                if label == "UnidadEstudio":
                    excluded = session.run(
                        "MATCH (n:UnidadEstudio) "
                        "WHERE n.requiere_revision_contenido = true "
                        "RETURN count(n) AS total"
                    ).single()["total"]
                    print(f"UnidadEstudio: excluidas_por_conflicto={excluded}", flush=True)
                rows, empty = read_catalog(
                    session,
                    label,
                    key,
                    args.limit,
                )
                prepared.append((label, key, rows))

                print(
                    f"{label}: preparados={len(rows)}, "
                    f"sin_texto={empty}",
                    flush=True,
                )

            if not args.write:
                print(
                    "Validación OK. "
                    "No se generaron ni guardaron vectores."
                )
                return

            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(
                args.model_path,
                device="cpu",
                local_files_only=True,
                trust_remote_code=False,
            )

            if model.get_sentence_embedding_dimension() != 384:
                raise ValueError(
                    "El modelo no tiene 384 dimensiones"
                )

            if any(label == "UnidadEstudio" for label, _ in selected):
                # Evitar que una versión en revisión conserve un vector anterior.
                session.run("""
                    MATCH (n:UnidadEstudio)
                    WHERE n.requiere_revision_contenido = true
                    REMOVE n.embedding, n.embedding_text, n.embedding_text_hash,
                           n.embedding_model, n.embedding_dimensions,
                           n.embedding_text_version, n.embedding_updated_at
                """).consume()

            total = 0

            for label, key, rows in prepared:
                total += write_catalog(
                    session,
                    model,
                    label,
                    key,
                    rows,
                    args.batch_size,
                )

    print(f"Embeddings procesados: {total}")
    print("Embeddings académicos: OK")


if __name__ == "__main__":
    main()
