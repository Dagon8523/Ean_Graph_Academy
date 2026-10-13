"""Descarga exploratoria de ofertas SAP; no escribe en Neo4j."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

from src.config.settings import get_settings
from src.integrations.sap_odata.client import SapProgramsClient

ENTITY_URL = (
    'https://eandsdev02.us10.hcs.cloud.sap/api/v1/datasphere/'
    'consumption/analytical/ARQ_INFO_COMPOSITES/'
    '3_AM_DP_OFEMP_01/_3_AM_DP_OFEMP_01'
)
FIELDS = (
    'ID,TITULO,CARGO,CARGOS,DETALLE,HABILIDAD,CATEGORIA,EXPERIENCIA,'
    'PROFESION,NIVEL_DE_EDUCACIÓN,NOMBRE_EMPRESA,SECTOR,CIUDAD_NORMALIZADA,'
    'FECHA,SALARIO,TIPO_DE_CONTRATO,TIPO_DE_PUESTO,VACANTES'
)
MULTIPLE = {'CARGOS', 'PROFESION'}


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')



def consolidate(rows):
    groups, missing = {}, []
    for row in rows:
        key = str(row.get('ID') or '').strip()
        if not key:
            missing.append(row)
            continue
        groups.setdefault(key, []).append(row)
    offers, conflicts = [], []
    for key, members in groups.items():
        variants = {}
        for field in FIELDS.split(','):
            values = {}
            for row in members:
                value = row.get(field)
                if value is not None and value != '':
                    values[json.dumps(value, sort_keys=True, ensure_ascii=False)] = value
            variants[field] = list(values.values())
        disagreements = {
            field: values for field, values in variants.items()
            if len(values) > 1 and field not in MULTIPLE | {'HABILIDAD', 'CATEGORIA', 'ID'}
        }
        skills = {}
        for row in members:
            name = row.get('HABILIDAD')
            if name:
                pair = (name, row.get('CATEGORIA'))
                skills[pair] = {'nombre': name, 'categoria': row.get('CATEGORIA')}
        offer = {
            'oferta_id': key,
            'filas_origen': len(members),
            'valores_fuente': variants,
            'habilidades': list(skills.values()),
            'requiere_revision': bool(disagreements),
            'vigencia': 'NO_VERIFICADA',
        }
        offers.append(offer)
        if disagreements:
            conflicts.append({'oferta_id': key, 'variantes_por_campo': disagreements})
    return offers, {'conflictos': conflicts, 'filas_sin_id': missing}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entity-url', default=ENTITY_URL)
    parser.add_argument('--page-size', type=int, default=20)
    parser.add_argument('--pages', type=int, default=2, help='Límite de páginas para explorar.')
    parser.add_argument('--out-dir', type=Path, default=Path('data/raw/mercado_laboral'))
    args = parser.parse_args()
    if not 1 <= args.page_size <= 1000 or not 1 <= args.pages <= 10000:
        parser.error('page-size debe estar entre 1 y 1000; pages entre 1 y 10000.')
    origin = urlsplit(args.entity_url)
    if origin.scheme != 'https' or not origin.netloc or origin.username or origin.password or origin.query or origin.fragment:
        parser.error('Usar una URL HTTPS de entidad sin credenciales, parámetros ni fragmento.')
    settings = get_settings().model_copy(update={'sap_programs_entity_url': args.entity_url})
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = args.out_dir / ('extraccion_' + stamp)
    folder.mkdir(parents=True, exist_ok=False)
    rows, pages, seen_pages, seen_rows = [], [], set(), set()
    next_url, skip, ended, duplicates = None, 0, False, 0
    try:
        with SapProgramsClient(settings) as client:
            for number in range(1, args.pages + 1):
                request_url = next_url or args.entity_url + '?' + urlencode({
                    '$select': FIELDS, '$top': args.page_size, '$skip': skip,
                })
                page = client.fetch_page(url=request_url)
                if any(not isinstance(row, dict) for row in page.items):
                    raise ValueError('La respuesta contiene filas que no son objetos.')
                digest = signature(page.items)
                if page.items and digest in seen_pages:
                    raise ValueError('SAP repitió una página completa. Extracción detenida.')
                seen_pages.add(digest)
                write_json(folder / f'pagina_{number:05d}.json', {'value': page.items})
                for row in page.items:
                    row_digest = signature(row)
                    if row_digest in seen_rows:
                        duplicates += 1
                    else:
                        seen_rows.add(row_digest)
                        rows.append(row)
                pages.append({'pagina': number, 'filas': len(page.items), 'next_link': bool(page.next_link)})
                print(f'Página {number}: {len(page.items)} filas', flush=True)
                skip += len(page.items)
                if page.next_link:
                    candidate = urljoin(request_url, page.next_link)
                    parsed = urlsplit(candidate)
                    if (parsed.scheme, parsed.netloc) != (origin.scheme, origin.netloc) or parsed.username or parsed.password:
                        raise ValueError('nextLink cambia el origen o contiene credenciales.')
                    next_url = candidate
                else:
                    next_url = None
                    if len(page.items) < args.page_size:
                        ended = True
                        break
    except Exception:
        write_json(folder / 'estado_error.json', {'estado': 'INTERRUMPIDA', 'paginas_guardadas': pages})
        print('Extracción interrumpida; páginas previas conservadas en:', folder)
        raise
    offers, audit = consolidate(rows)
    write_json(folder / 'filas_ofertas.json', {'value': rows})
    write_json(folder / 'ofertas_consolidadas.json', {'ofertas': offers})
    write_json(folder / 'auditoria.json', audit)
    summary = {
        'filas_distintas': len(rows), 'duplicados_observados': duplicates,
        'ofertas_distintas': len(offers), 'ofertas_con_variantes_en_revision': len(audit['conflictos']),
        'filas_sin_id': len(audit['filas_sin_id']), 'paginas': pages,
        'fin_observado': ended, 'limite_paginas_alcanzado': not ended,
        'paginacion_estable_verificada': False,
        'catalogo_completo_verificado': False,
        'nota': 'Sin ordenamiento: explorar y auditar antes de una carga completa. La última oferta puede estar incompleta.',
    }
    write_json(folder / 'resumen.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('Archivos:', folder)
    print('No se escribió en Neo4j. La vigencia de las ofertas no está verificada.')


if __name__ == '__main__':
    main()