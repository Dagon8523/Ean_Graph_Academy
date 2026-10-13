"""Calcula candidatos semánticos y opcionalmente crea relaciones."""

import argparse
import json
import csv
import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from neo4j import GraphDatabase

from src.config.settings import get_settings


MODEL = "intfloat/multilingual-e5-small"
PIPELINE = "academic_similarity_v25_hybrid"
VERSIONS = {label: "academic_v1" for label in (
    "Formacion", "ProgramaOficial", "FormacionEANX", "ModuloEANX")}
VERSIONS["UnidadEstudio"] = "academic_v2_syllabus_v24"

KEYS = {
    "Formacion": "formacion_id",
    "ProgramaOficial": "programa_id",
    "UnidadEstudio": "unidad_id",
    "FormacionEANX": "eanx_id",
    "ModuloEANX": "modulo_id",
}

PAIRS = [
    ("Formacion", "UnidadEstudio"),
    ("Formacion", "ProgramaOficial"),
    ("FormacionEANX", "UnidadEstudio"),
    ("FormacionEANX", "ProgramaOficial"),
    ("FormacionEANX", "Formacion"),
    ("ModuloEANX", "UnidadEstudio"),
    ("ModuloEANX", "Formacion"),
]


def read_catalog(session, label):
    key = KEYS[label]
    query = f"""
    MATCH (n:{label})
    WHERE n.embedding IS NOT NULL
      AND coalesce(n.requiere_revision_contenido, false) = false
    RETURN
        n.{key} AS id,
        coalesce(
            n.titulo,
            n.nombre_unidad_estudio,
            n.nombre,
            n.snies_descripcion_abreviada,
            n.snies_distincion_genero
        ) AS nombre,
        n.embedding AS vector,
        n.embedding_model AS modelo,
        n.embedding_text_version AS version,
        n.embedding_text_hash AS hash,
        n.embedding_text AS texto,
        n.estado_relacion_programa AS estado_programa
    ORDER BY n.{key}
    """

    rows = [record.data() for record in session.run(query)]
    seen = set()

    for row in rows:
        if row["id"] is None or row["id"] in seen:
            raise ValueError(f"Llave nula o duplicada en {label}")
        seen.add(row["id"])

        vector = np.asarray(row["vector"], dtype=np.float32)
        if (
            vector.shape != (384,)
            or not np.isfinite(vector).all()
            or np.linalg.norm(vector) == 0
        ):
            raise ValueError(f"Vector inválido: {label}/{row['id']}")

        if row["modelo"] != MODEL or row["version"] != VERSIONS[label]:
            raise ValueError(
                f"Modelo o versión incompatible: {label}/{row['id']}"
            )
        if not row["hash"] or not row["texto"]:
            raise ValueError(f"Falta texto/hash de embedding: {label}/{row['id']}")
        if hashlib.sha256(row["texto"].encode("utf-8")).hexdigest() != row["hash"]:
            raise ValueError(f"Hash de texto inconsistente: {label}/{row['id']}")

    if not rows:
        return rows, np.empty((0, 384), dtype=np.float32)

    matrix = np.asarray(
        [row["vector"] for row in rows],
        dtype=np.float32,
    )
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    return rows, matrix


def cosine_candidates(source_rows, source_matrix, target_rows,
               target_matrix, top_k, threshold):
    result = []
    if not source_rows or not target_rows:
        return result

    # Ranking inverso: señal de revisión, no prueba de equivalencia.
    reverse = {}
    for start in range(0, len(target_rows), 64):
        scores = target_matrix[start:start + 64] @ source_matrix.T
        for offset, similarities in enumerate(scores):
            indexes = np.argsort(-similarities, kind="stable")[:top_k]
            reverse[start + offset] = {int(index): rank for rank, index in enumerate(indexes, 1)}

    # Evita construir una matriz de similitud de todos los pares.
    for start in range(0, len(source_rows), 64):
        scores = source_matrix[start:start + 64] @ target_matrix.T

        for offset, similarities in enumerate(scores):
            source = source_rows[start + offset]
            # Orden estable: desempates por el orden de ID del catálogo.
            indexes = np.argsort(
                -similarities,
                kind="stable",
            )[:top_k]

            for rank, index in enumerate(indexes, start=1):
                score = float(np.clip(similarities[index], -1, 1))
                if score < threshold:
                    continue

                target = target_rows[index]
                result.append({
                    "origen_id": source["id"],
                    "destino_id": target["id"],
                    "origen_nombre": source["nombre"],
                    "destino_nombre": target["nombre"],
                    "similitud": score,
                    "ranking": rank,
                    "origen_text_hash": source["hash"],
                    "destino_text_hash": target["hash"],
                    "origen_version": source["version"],
                    "destino_version": target["version"],
                    "ranking_inverso": reverse[int(index)].get(start + offset),
                    "reciproca_top_k": start + offset in reverse[int(index)],
                    "margen_top1_top2": float(similarities[indexes[0]] - similarities[indexes[1]])
                        if len(indexes) > 1 else None,
                    "origen_texto": source["texto"][:1500],
                    "destino_texto": target["texto"][:1500],
                    "origen_estado_programa": source.get("estado_programa"),
                    "destino_estado_programa": target.get("estado_programa"),
                })

    return result


STOP = set('de del la las el los en y o a un una unos unas por para con al que se su sus '
           'curso cursos modulo modulos leccion lecciones experiencia experiencias proyecto '
           'practico avance introduccion fundamentos aprendizaje unidad estudio contenidos '
           'empresas empresa organizacion organizacional organizacionales herramientas tipos '
           'gestion desarrollo aplicacion aplicada aplicado nivel primero segundo'.split())


def terms(text):
    text = unicodedata.normalize('NFKD', str(text or '')).lower()
    text = ''.join(c for c in text if not unicodedata.combining(c))
    words = re.findall(r'[a-z][a-z0-9+#]*', text)
    # Prefijos permiten variaciones como climático/climática; son heurísticos.
    return {w[:6] if len(w) > 6 else w for w in words if w not in STOP and len(w) > 2}


def generic_module(name):
    text = unicodedata.normalize('NFKD', str(name or '')).lower()
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'^\s*(?:modulo\s*)?\d+\s*[:.-]?\s*', '', text).strip()
    return bool(re.match(r'^(presentacion|bienvenida|inicio ruta|evaluacion|autoevaluacion|'
                         r'nuestro experto|nuestra experta|reglas de juego|foro de discusion)\b', text))


def group_catalog(rows, matrix):
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[row['hash']].append(i)
    selected, indexes = [], []
    for _, positions in sorted(groups.items(), key=lambda item: rows[item[1][0]]['id']):
        index = positions[0]
        row = dict(rows[index])
        row['ids_grupo'] = [rows[i]['id'] for i in positions]
        selected.append(row)
        indexes.append(index)
    return selected, matrix[indexes] if indexes else np.empty((0, 384), dtype=np.float32)


def hybrid_candidates(source_rows, source_matrix, target_rows, target_matrix, top_k, threshold):
    if not source_rows or not target_rows:
        return []
    st = [terms(r['nombre']) for r in source_rows]
    tt = [terms(r['nombre']) for r in target_rows]
    sc = [terms(r['texto']) for r in source_rows]
    tc = [terms(r['texto']) for r in target_rows]
    df = Counter(t for tokens in st + tt for t in tokens)
    weights = {t: float(np.log(1 + (len(st) + len(tt)) / (1 + count))) for t, count in df.items()}
    index = defaultdict(set)
    for j, tokens in enumerate(tt):
        for token in tokens:
            index[token].add(j)
    selected = []
    for start in range(0, len(source_rows), 64):
        scores = source_matrix[start:start + 64] @ target_matrix.T
        for offset, similarities in enumerate(scores):
            i = start + offset
            # Recuperación semántica amplia + títulos coincidentes fuera del top-50.
            pool = set(map(int, np.argsort(-similarities, kind='stable')[:50]))
            for token in st[i]:
                pool.update(index[token])
            ranked = []
            for j in sorted(pool):
                cosine = float(np.clip(similarities[j], -1, 1))
                if cosine < threshold:
                    continue
                shared = st[i] & tt[j]
                title_content = (st[i] & tc[j]) | (tt[j] & sc[i])
                if not shared and len(title_content) < 2:
                    continue
                union = st[i] | tt[j]
                overlap = sum(weights[t] for t in shared) / max(sum(weights[t] for t in union), 1e-9)
                coverage = len(title_content) / max(len(union), 1)
                coverage = min(coverage, 1)
                score = .55 * cosine + .35 * overlap + .10 * coverage
                ranked.append((score, j, cosine, overlap, coverage, sorted(shared or title_content)))
            ranked.sort(key=lambda x: (-x[0], target_rows[x[1]]['id']))
            for rank, (score, j, cosine, overlap, coverage, anchors) in enumerate(ranked[:top_k], 1):
                source, target = source_rows[i], target_rows[j]
                selected.append({'origen_id': source['id'], 'destino_id': target['id'],
                    'origen_nombre': source['nombre'], 'destino_nombre': target['nombre'],
                    'similitud': cosine, 'puntaje_hibrido': score, 'coincidencia_titulos': overlap,
                    'cobertura_terminos': coverage, 'terminos_compartidos': ' | '.join(anchors),
                    'ranking': rank, 'ranking_inverso': None, 'reciproca_top_k': False,
                    'margen_top1_top2': ranked[0][0] - ranked[1][0] if len(ranked) > 1 else None,
                    'origen_text_hash': source['hash'], 'destino_text_hash': target['hash'],
                    'origen_version': source['version'], 'destino_version': target['version'],
                    'origen_texto': source['texto'][:1500], 'destino_texto': target['texto'][:1500],
                    'origen_estado_programa': source.get('estado_programa'),
                    'destino_estado_programa': target.get('estado_programa'),
                    'origen_ids_grupo': json.dumps(source.get('ids_grupo', [source['id']])),
                    'destino_ids_grupo': json.dumps(target.get('ids_grupo', [target['id']]))})
    return selected


def candidates(source_rows, source_matrix, target_rows, target_matrix, top_k, threshold):
    forward = hybrid_candidates(source_rows, source_matrix, target_rows, target_matrix, top_k, threshold)
    reverse = hybrid_candidates(target_rows, target_matrix, source_rows, source_matrix, top_k, threshold)
    ranks = {(row['destino_id'], row['origen_id']): row['ranking'] for row in reverse}
    for row in forward:
        rank = ranks.get((row['origen_id'], row['destino_id']))
        row['ranking_inverso'] = rank
        row['reciproca_top_k'] = rank is not None
    return forward


def save_batch(tx, source_label, target_label, rows, args):
    source_key = KEYS[source_label]
    target_key = KEYS[target_label]

    query = f"""
    UNWIND $rows AS row
    MATCH (a:{source_label} {{{source_key}: row.origen_id}})
    MATCH (b:{target_label} {{{target_key}: row.destino_id}})
    WHERE a.embedding_text_hash = row.origen_text_hash
      AND b.embedding_text_hash = row.destino_text_hash
      AND a.embedding_text_version = row.origen_version
      AND b.embedding_text_version = row.destino_version
      AND a.embedding_model = $modelo AND b.embedding_model = $modelo
      AND a.embedding IS NOT NULL AND b.embedding IS NOT NULL
      AND coalesce(a.requiere_revision_contenido, false) = false
      AND coalesce(b.requiere_revision_contenido, false) = false
    MERGE (a)-[r:RELACIONADA_SEMANTICAMENTE {{
        pipeline: $pipeline
    }}]->(b)
    SET
        r.similitud = row.similitud,
        r.ranking = row.ranking,
        r.modelo = $modelo,
        r.metodo = 'coseno_y_terminos',
        r.puntaje_hibrido = row.puntaje_hibrido,
        r.origen_version_texto = row.origen_version,
        r.destino_version_texto = row.destino_version,
        r.validada = true,
        r.naturaleza = 'afinidad_tematica',
        r.metodo_validacion = 'revision_csv',
        r.umbral = $threshold,
        r.top_k = $top_k,
        r.origen_text_hash = row.origen_text_hash,
        r.destino_text_hash = row.destino_text_hash,
        r.fecha_calculo = datetime()
    RETURN count(r) AS procesadas
    """

    count = tx.run(
        query,
        rows=rows,
        pipeline=PIPELINE,
        modelo=MODEL,
        threshold=args.threshold,
        top_k=args.top_k,
    ).single()["procesadas"]
    if count != len(rows):
        raise RuntimeError("Candidatos cambiaron o faltan nodos; lote revertido.")
    return count


def export_reports(out_dir, prepared, catalogs, args):
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows, summaries = [], []
    for source, target, rows in prepared:
        all_rows.extend({"origen_tipo": source, "destino_tipo": target,
                         **row, "decision": "PENDIENTE"} for row in rows)
        scores = [row["similitud"] for row in rows]
        covered = len({row["origen_id"] for row in rows})
        count = len(catalogs[source][0])
        summaries.append({"origen": source, "destino": target,
            "candidatos": len(rows), "origenes_con_candidato": covered,
            "origenes_sin_candidato": count - covered,
            "reciprocos_top_k": sum(row["reciproca_top_k"] for row in rows),
            "percentiles_similitud": np.quantile(scores, [0, .25, .5, .75, 1]).tolist() if scores else []})
    fields = ["origen_tipo", "destino_tipo", "origen_id", "destino_id",
              "origen_nombre", "destino_nombre", "similitud", "ranking",
              "puntaje_hibrido", "coincidencia_titulos", "cobertura_terminos", "terminos_compartidos",
              "origen_ids_grupo", "destino_ids_grupo",
              "ranking_inverso", "reciproca_top_k", "margen_top1_top2",
              "origen_version", "destino_version", "origen_text_hash", "destino_text_hash",
              "origen_estado_programa", "destino_estado_programa", "origen_texto", "destino_texto", "decision"]
    with (out_dir / "candidatos_revision.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)
    summary = {"pipeline": PIPELINE, "modelo": MODEL, "umbral_no_calibrado": args.threshold,
               "top_k": args.top_k, "catalogos_agrupados_por_texto": {k: len(v[0]) for k, v in catalogs.items()},
               "heuristica_no_calibrada": "0.55 coseno + 0.35 coincidencia de títulos + 0.10 cobertura; no es probabilidad",
               "pool_semantico": 50,
               "pares": summaries, "total_candidatos": len(all_rows)}
    (out_dir / "resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Reportes: {out_dir / 'candidatos_revision.csv'} y {out_dir / 'resumen.json'}")


def approved_rows(review, prepared):
    current = {(source, target, row['origen_id'], row['destino_id']): row
               for source, target, rows in prepared for row in rows}
    approved, seen = {}, set()
    for row in review:
        decision = (row.get('decision') or '').strip().upper()
        if decision not in {'PENDIENTE', 'APROBAR', 'RECHAZAR'}:
            raise ValueError('Decisión inválida; usar PENDIENTE, APROBAR o RECHAZAR.')
        if decision != 'APROBAR':
            continue
        key = tuple(row.get(k) for k in ('origen_tipo', 'destino_tipo', 'origen_id', 'destino_id'))
        if key in seen or key not in current:
            raise ValueError('Candidato aprobado repetido o fuera del cálculo actual.')
        seen.add(key)
        fresh = current[key]
        for field in ('origen_text_hash', 'destino_text_hash', 'origen_version', 'destino_version'):
            if row.get(field) != fresh[field]:
                raise ValueError('El texto cambió desde la revisión; generar un reporte nuevo.')
        approved.setdefault(key[:2], []).append(fresh)
    return [(source, target, rows) for (source, target), rows in approved.items()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed/semantic_v25"))
    parser.add_argument("--review-file", type=Path, help="CSV revisado; sólo escribe filas con decision=APROBAR.")
    args = parser.parse_args()

    if args.top_k < 1:
        parser.error("--top-k debe ser positivo")
    if not -1 <= args.threshold <= 1:
        parser.error("--threshold debe estar entre -1 y 1")
    if args.write and not args.review_file:
        parser.error("--write requiere --review-file con las filas revisadas.")
    review = []
    if args.review_file:
        if args.review_file.resolve() == (args.out_dir / 'candidatos_revision.csv').resolve():
            parser.error('Guardar la revisión con otro nombre, por ejemplo candidatos_revisados.csv.')
        with args.review_file.open(encoding='utf-8-sig', newline='') as file:
            review = list(csv.DictReader(file))

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
            catalogs = {
                label: read_catalog(session, label)
                for label in KEYS
            }
            for label, (rows, _) in catalogs.items():
                print(f"{label}: {len(rows)} embeddings compatibles", flush=True)
            for label, (rows, matrix) in list(catalogs.items()):
                if label == 'ModuloEANX':
                    keep = [i for i, row in enumerate(rows) if not generic_module(row['nombre'])]
                    print(f'ModuloEANX: {len(rows) - len(keep)} módulos genéricos excluidos')
                    rows, matrix = [rows[i] for i in keep], matrix[keep]
                catalogs[label] = group_catalog(rows, matrix)
                print(f'{label}: {len(catalogs[label][0])} grupos de texto para comparar')

            prepared = []
            for source_label, target_label in PAIRS:
                source_rows, source_matrix = catalogs[source_label]
                target_rows, target_matrix = catalogs[target_label]

                rows = candidates(
                    source_rows,
                    source_matrix,
                    target_rows,
                    target_matrix,
                    args.top_k,
                    args.threshold,
                )
                prepared.append((source_label, target_label, rows))

                print(
                    f"\n{source_label} → {target_label}: "
                    f"{len(rows)} candidatos",
                    flush=True,
                )
                preview = sorted(
                    rows,
                    key=lambda row: row["puntaje_hibrido"],
                    reverse=True,
                )[:5]

                print(json.dumps(
                    [{k: row[k] for k in ('origen_nombre', 'destino_nombre',
                      'similitud', 'ranking', 'ranking_inverso', 'reciproca_top_k')}
                     for row in preview],
                    ensure_ascii=False,
                    indent=2,
                ))

            export_reports(args.out_dir, prepared, catalogs, args)
            if not args.write:
                print("\nRevisión terminada. No se escribió en Neo4j.")
                return

            prepared = approved_rows(review, prepared)

            total = 0
            for source_label, target_label, rows in prepared:
                for start in range(0, len(rows), 100):
                    batch = rows[start:start + 100]
                    count = session.execute_write(
                        save_batch,
                        source_label,
                        target_label,
                        batch,
                        args,
                    )
                    if count != len(batch):
                        raise RuntimeError("Escritura incompleta")
                    total += count

            print(f"\nRelaciones procesadas: {total}")


if __name__ == "__main__":
    main()
