"""Opt-in import of audited SAP consolidated offers into a NEW chat schema."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from neo4j import GraphDatabase

from src.services.conversation_model import ConversationSettings

QUERY = '''
UNWIND $rows AS row
MERGE (o:OfertaLaboral {oferta_id: row.oferta_id})
SET o += row
'''
FIELDS = {'TITULO': 'titulo', 'CARGO': 'cargo', 'DETALLE': 'detalle',
          'NOMBRE_EMPRESA': 'empresa', 'CIUDAD_NORMALIZADA': 'ciudad',
          'EXPERIENCIA': 'experiencia', 'NIVEL_DE_EDUCACIÓN': 'educacion',
          'SALARIO': 'salario', 'FECHA': 'fecha'}


def rows_from(source):
    rows = []
    seen = set()
    skipped = 0
    for offer in source['ofertas']:
        identifier = str(offer.get('oferta_id', '')).strip()
        if not identifier or identifier in seen or offer.get('requiere_revision'):
            skipped += 1
            continue
        seen.add(identifier)
        row = {'oferta_id': identifier, 'fuente': 'SAP Datasphere · extracción exploratoria',
               'vigencia': 'NO_VERIFICADA', 'requiere_revision': False,
               'actualizado_en': datetime.now(timezone.utc).isoformat()}
        values = offer['valores_fuente']
        if any(len(values.get(key, [])) > 1 for key in FIELDS):
            skipped += 1
            continue
        for source_key, target in FIELDS.items():
            candidates = values.get(source_key, [])
            row[target] = str(candidates[0])[:4000] if candidates else None
        # Keep professions and skills as textual evidence; no invented graph edges.
        terms = [str(v) for v in values.get('PROFESION', []) + values.get('CARGOS', [])]
        terms += [str(v.get('nombre', '')) for v in offer.get('habilidades', [])]
        row['texto_busqueda'] = ' '.join(terms)[:8000]
        rows.append(row)
    return rows, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path, help='ofertas_consolidadas.json')
    parser.add_argument('--apply', action='store_true', help='Write after reviewing dry-run counts')
    args = parser.parse_args()
    rows, skipped = rows_from(json.loads(args.file.read_text(encoding='utf-8')))
    print(json.dumps({'importables': len(rows), 'omitidas': skipped,
                      'vigencia': 'NO_VERIFICADA', 'escritura': args.apply}, ensure_ascii=False))
    if not args.apply:
        return
    settings = ConversationSettings()
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user,
                               settings.neo4j_password.get_secret_value())) as driver:
        with driver.session(database=settings.neo4j_database) as session:
            session.run('CREATE CONSTRAINT oferta_chat_id IF NOT EXISTS '
                        'FOR (o:OfertaLaboral) REQUIRE o.oferta_id IS UNIQUE').consume()
            for start in range(0, len(rows), 500):
                session.execute_write(lambda tx, batch: tx.run(QUERY, rows=batch).consume(),
                                      rows[start:start + 500])
    print('Carga finalizada. No se crearon relaciones académicas ni se validó vigencia.')


if __name__ == '__main__':
    main()
