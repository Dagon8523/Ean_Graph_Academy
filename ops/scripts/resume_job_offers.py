"""Continúa una extracción por offset y conserva sus páginas originales."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode

from ops.scripts.sap_job_offers import (
    ENTITY_URL, FIELDS, consolidate, signature,
)
from src.config.settings import get_settings
from src.integrations.sap_odata.client import SapProgramsClient


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def load_pages(folder, page_size):
    paths = sorted(folder.glob("pagina_*.json"))
    if not paths:
        raise ValueError("La carpeta no contiene páginas.")
    pages, rows, hashes = [], [], set()
    for number, path in enumerate(paths, 1):
        if path.name != f"pagina_{number:05d}.json":
            raise ValueError("Faltan páginas o la numeración no es consecutiva.")
        items = json.loads(path.read_text(encoding="utf-8"))["value"]
        if len(items) > page_size:
            raise ValueError("El tamaño indicado no coincide con las páginas.")
        if number < len(paths) and len(items) != page_size:
            raise ValueError("Hay una página corta antes de la última.")
        digest = signature(items)
        if items and digest in hashes:
            raise ValueError("Hay páginas completas repetidas.")
        hashes.add(digest)
        pages.append(items)
        rows.extend(items)
    return pages, rows, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--pages", type=int, default=100,
                        help="Máximo de páginas adicionales.")
    args = parser.parse_args()
    if args.page_size < 1 or args.pages < 1:
        parser.error("Los tamaños deben ser positivos.")

    pages, rows, hashes = load_pages(args.folder, args.page_size)
    previous = json.loads(
        (args.folder / "resumen.json").read_text(encoding="utf-8")
    )
    if any(p.get("next_link") for p in previous.get("paginas", [])):
        raise ValueError("Esta continuación requiere paginación sin nextLink.")

    settings = get_settings().model_copy(
        update={"sap_programs_entity_url": ENTITY_URL}
    )
    ended = len(pages[-1]) < args.page_size
    failure = None
    checks = []

    def fetch(client, skip):
        url = ENTITY_URL + "?" + urlencode({
            "$select": FIELDS, "$top": args.page_size, "$skip": skip,
        })
        return client.fetch_page(url=url)

    if not ended:
        with SapProgramsClient(settings) as client:
            # Comprueba que los extremos guardados no se hayan desplazado.
            for index in sorted({0, len(pages) - 1}):
                current = fetch(client, index * args.page_size)
                if current.items != pages[index]:
                    raise ValueError(
                        f"La página {index + 1} cambió; no se mezclaron datos."
                    )
                checks.append(index + 1)

            try:
                for _ in range(args.pages):
                    number = len(pages) + 1
                    page = fetch(client, len(rows))
                    if page.next_link:
                        raise ValueError("SAP devolvió nextLink; revisar continuación.")
                    digest = signature(page.items)
                    if page.items and digest in hashes:
                        raise ValueError("SAP repitió una página completa.")
                    path = args.folder / f"pagina_{number:05d}.json"
                    if path.exists():
                        raise ValueError(f"La página {number} ya existe.")
                    save(path, {"value": page.items})
                    hashes.add(digest)
                    pages.append(page.items)
                    rows.extend(page.items)
                    print(f"Página {number}: {len(page.items)} filas", flush=True)
                    if len(page.items) < args.page_size:
                        ended = True
                        break
            except Exception as exc:
                failure = exc

    unique = {signature(row): row for row in rows}
    offers, audit = consolidate(list(unique.values()))
    summary = {
        "filas_distintas": len(unique),
        "duplicados_observados": len(rows) - len(unique),
        "ofertas_distintas": len(offers),
        "ofertas_con_variantes_en_revision": len(audit["conflictos"]),
        "filas_sin_id": len(audit["filas_sin_id"]),
        "paginas": [
            {"pagina": i, "filas": len(items), "next_link": False}
            for i, items in enumerate(pages, 1)
        ],
        "fin_observado": ended,
        "limite_paginas_alcanzado": not ended and failure is None,
        "extraccion_interrumpida": failure is not None,
        "paginas_recomprobadas": checks,
        "paginacion_estable_verificada": False,
        "catalogo_completo_verificado": False,
        "nota": "Offset sin ordenamiento; vigencia y cobertura no verificadas.",
    }
    save(args.folder / "filas_ofertas.json", {"value": list(unique.values())})
    save(args.folder / "ofertas_consolidadas.json", {"ofertas": offers})
    save(args.folder / "auditoria.json", audit)
    save(args.folder / "resumen.json", summary)
    print(json.dumps(
        {k: v for k, v in summary.items() if k != "paginas"},
        ensure_ascii=False, indent=2,
    ))
    print("No se modificó Neo4j.")
    if failure:
        raise failure


if __name__ == "__main__":
    main()
