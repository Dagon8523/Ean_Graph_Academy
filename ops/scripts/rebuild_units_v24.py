"""Depura syllabus y reconstruye SOLO UnidadEstudio; diagnóstico por defecto."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pickle
import re
import unicodedata

SEMANTIC = ('nombre_unidad_estudio', 'descripcion_unidad',
            'resultado_aprendizaje_unidad', 'contenidos_unidad', 'competencia_programa')
IDENTITY = ('codigo_plan_estudios', 'codigo_unidad_estudio', 'anio', 'modalidad')


def norm(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    return ' '.join(''.join(c for c in text if not unicodedata.combining(c)).lower().split())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def source(record):
    return (str(record.get('folder_breadcrumb') or ''), Path(str(record.get('file_path') or '')).name,
            str(record.get('sheet_name') or ''), str(record.get('fila_origen') or ''))


def prepare(records):
    groups, review, sources = defaultdict(list), [], set()
    for record in records:
        if not isinstance(record, dict) or not norm(record.get('nombre_unidad_estudio')):
            raise ValueError('Registro inválido o sin nombre.')
        origin = source(record)
        if not origin[1] or not origin[2] or origin in sources:
            raise ValueError('Origen incompleto o repetido: revisar archivo, hoja y fila.')
        sources.add(origin)
        complete = all(norm(record.get(k)) for k in IDENTITY[:2])
        key = tuple(norm(record.get(k)) for k in IDENTITY) if complete else ('fuente', *origin)
        groups[key].append(record)
    rows, collapsed = [], 0
    for key, group in sorted(groups.items()):
        group = sorted(group, key=source)
        signatures = {tuple(norm(x.get(k)) for k in SEMANTIC +
                      ('creditos_academicos', 'nivel', 'tipo_unidad_estudio')) for x in group}
        conflict = len(signatures) > 1
        incomplete = not all(norm(group[0].get(k)) for k in IDENTITY[:2])
        if conflict or incomplete:
            review.append({'motivo': 'versiones_en_conflicto' if conflict else 'identidad_incompleta',
                           'identidad': key, 'registros': group})
        batches = [[x] for x in group] if conflict else [group]
        collapsed += 0 if conflict else len(group) - 1
        for items in batches:
            record = min(items, key=source)
            row = {k: v for k, v in record.items() if isinstance(v, (str, int, float, bool))}
            row.pop('file_path', None)
            for k in IDENTITY[:2]:
                row[k] = str(record.get(k) or '').strip().upper()
            parts, seen = [], set()
            for k in SEMANTIC:
                value = str(record.get(k) or '').strip()
                # Retirar duraciones de encabezados; conservar los temas numerados.
                if k == 'contenidos_unidad':
                    value = '\n'.join(line for line in value.splitlines()
                                      if not re.fullmatch(r'\s*\d+(?:[.,]\d+)?\s+semanas\s*', line, re.I))
                if value and norm(value) not in seen:
                    parts.append(value)
                    seen.add(norm(value))
            row.update(unidad_id=digest(['syllabus_source_v24', *source(record)]),
                       llave_natural='|'.join(source(record)), codigo_programa=row['codigo_plan_estudios'],
                       nombre_normalizado=norm(record['nombre_unidad_estudio']),
                       texto_semantico='\n\n'.join(parts),
                       huella_contenido=digest(parts), busqueda_semantica_disponible=bool(parts),
                       archivo_origen=Path(str(record.get('file_path') or '')).name,
                       carpeta_origen=record.get('folder_breadcrumb') or '',
                       hoja_origen=record.get('sheet_name') or '',
                       programa_origen=record.get('programa') or '',
                       tipo_hoja=record.get('sheet_type') or '', origen='SYLLABUS_JSON',
                       fuentes_json=json.dumps([{'archivo': x.get('file_path'),
                           'hoja': x.get('sheet_name'), 'fila': x.get('fila_origen'),
                           'celdas': x.get('celdas_origen')} for x in items], ensure_ascii=False))
            row.update(requiere_revision_identidad=incomplete,
                       requiere_revision_contenido=conflict,
                       estado_revision='conflicto_contenido' if conflict else
                           ('identidad_incompleta' if incomplete else 'sin_conflictos'),
                       estado_relacion_programa='pendiente_revision' if incomplete or conflict else 'sin_coincidencia_exacta',
                       grupo_versiones=digest(key) if conflict else '',
                       cantidad_fuentes=len(items), esquema_identidad='fuente_v24')
            if conflict:
                row['texto_semantico_revision'] = row['texto_semantico']
                row['texto_semantico'] = None
                row['busqueda_semantica_disponible'] = False
            rows.append(row)
    rows.sort(key=lambda x: x['unidad_id'])
    return rows, review, collapsed


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def replace(tx, rows, snapshot):
    current = {r['id']: (list(r['labels']), dict(r['props'])) for r in tx.run(
        'MATCH (u:UnidadEstudio) RETURN elementId(u) AS id, labels(u) AS labels, properties(u) AS props')}
    previous = {x['id']: (x['labels'], x['props']) for x in snapshot}
    if current != previous:
        raise RuntimeError('Cambiaron las unidades después del respaldo; volver a ejecutar.')
    tx.run('MATCH (u:UnidadEstudio) DETACH DELETE u').consume()
    for offset in range(0, len(rows), 100):
        tx.run('UNWIND $rows AS row CREATE (u:UnidadEstudio) SET u = row, '
               'u.actualizado_en = datetime()', rows=rows[offset:offset + 100]).consume()
    record = tx.run('MATCH (u:UnidadEstudio) MATCH (p:ProgramaOficial) '
                    'WHERE p.codigo_programa = u.codigo_programa AND u.requiere_revision_identidad = false AND u.requiere_revision_contenido = false '
                    'MERGE (p)-[r:CONTIENE_UNIDAD]->(u) '
                    "SET r.metodo='codigo_programa_exacto', r.validada=true, "
                    "r.actualizado_en=datetime(), u.estado_relacion_programa='vinculada' RETURN count(r) AS total").single()
    return record['total']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--out-dir', type=Path, default=Path('data/processed/reconstruccion_unidades_v24'))
    parser.add_argument('--write', action='store_true', help='Respalda y reemplaza SOLO UnidadEstudio.')
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding='utf-8'))
    if not isinstance(records, list):
        raise ValueError('Se esperaba una lista JSON.')
    rows, review, collapsed = prepare(records)
    if not rows or len({r['unidad_id'] for r in rows}) != len(rows):
        raise ValueError('Catálogo vacío o identificadores repetidos.')
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = {'entrada': len(records), 'unidades_listas': len(rows),
               'duplicados_identicos_consolidados': collapsed,
               'registros_pendientes': sum(len(x['registros']) for x in review),
               'grupos_revision': dict(Counter(x['motivo'] for x in review)),
               'catalogo_sha256': digest(rows)}
    assert summary['entrada'] == len(rows) + collapsed
    summary['versiones_con_contenido_en_revision'] = sum(r['requiere_revision_contenido'] for r in rows)
    summary['unidades_con_identidad_incompleta'] = sum(r['requiere_revision_identidad'] for r in rows)
    save_json(args.out_dir / 'catalogo_listo.json', rows)
    save_json(args.out_dir / 'pendientes_revision.json', review)
    save_json(args.out_dir / 'resumen.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not args.write:
        print('Diagnóstico OK. No se conectó ni se modificó Neo4j.')
        return
    from neo4j import GraphDatabase
    from src.config.settings import get_settings
    settings = get_settings()
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user,
                              settings.neo4j_password.get_secret_value())) as driver:
        driver.verify_connectivity()
        with driver.session(database=settings.neo4j_database) as session:
            nodes = [dict(r) for r in session.run('MATCH (u:UnidadEstudio) '
                     'RETURN elementId(u) AS id, labels(u) AS labels, properties(u) AS props')]
            if any(set(x['labels']) != {'UnidadEstudio'} for x in nodes):
                raise RuntimeError('Existen unidades con etiquetas adicionales; revisar antes de reemplazar.')
            rels = [dict(r) for r in session.run('MATCH (a)-[r]->(b) '
                    'WHERE a:UnidadEstudio OR b:UnidadEstudio RETURN '
                    'elementId(a) AS inicio, elementId(b) AS fin, type(r) AS tipo, '
                    'properties(r) AS props, labels(a) AS labels_inicio, '
                    'labels(b) AS labels_fin, properties(a) AS props_inicio, '
                    'properties(b) AS props_fin')]
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = args.out_dir / ('respaldo_' + stamp + '.pickle')
            # Pickle conserva tipos Neo4j (fechas, puntos); usar sólo copias propias.
            with backup.open('xb') as file:
                pickle.dump({'nodes': nodes, 'relationships': rels}, file)
            save_json(backup.with_suffix('.json'), {'nodes': nodes, 'relationships': rels})
            print('Respaldo:', backup)
            count = session.execute_write(replace, rows, nodes)
            print(f'Reconstrucción OK: {len(rows)} unidades; {count} relaciones programa–unidad.')
            print('Embeddings pendientes de regenerar. Las versiones conflictivas no se habilitan para embeddings.')


if __name__ == '__main__':
    main()
