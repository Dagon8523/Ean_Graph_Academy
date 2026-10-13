"""Sincroniza programas oficiales desde SAP Datasphere OData hacia Neo4j."""

from __future__ import annotations

import argparse

from neo4j.exceptions import Neo4jError
from pydantic import ValidationError

from src.config.settings import get_settings
from src.domain.program_models import SapProgramRecord
from src.integrations.sap_odata.client import SapProgramsClient
from src.repositories.program_repository import ProgramRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sincronización de programas oficiales SAP Datasphere OData hacia Neo4j."
        ),
    )

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Lee y valida SAP OData sin escribir en Neo4j.",
    )

    mode.add_argument(
        "--write",
        action="store_true",
        help="Crea o actualiza los programas en Neo4j.",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Cantidad máxima de páginas OData que se procesarán.",
    )

    parser.add_argument(
        "--max-programs",
        type=int,
        default=None,
        help="Cantidad máxima de programas que se procesarán.",
    )

    return parser


def to_neo4j_row(
    record: SapProgramRecord,
) -> dict:
    return {
        "programa_id": record.program_id,
        "codigo_programa": record.program_code,
        "codigo_snies": record.snies_code,
        "descripcion_abreviada": record.snies_short_description,
        "distincion_genero": record.snies_gender_distinction,
        "snies_descripcion_abreviada": (record.snies_short_description),
        "snies_distincion_genero": (record.snies_gender_distinction),
        "texto_semantico": record.semantic_text or None,
        "busqueda_semantica_disponible": bool(record.semantic_text),
        "estado": record.snies_status,
        "fecha_aprobacion_rc": record.snies_approval_date,
        "vigencia_rnrc_anos": (record.snies_rnrc_validity_years),
        "vigencia_ac_anos": (record.snies_ac_validity_years),
        "facultad_snies": record.snies_faculty,
        "modalidad": record.snies_modality,
        "nivel_formacion": record.snies_education_level,
        "school": record.snies_school,
        "tipo_programa": record.snies_program_type,
        "tipo_programa_global": (record.snies_global_program_type),
        "ubicacion": record.location,
        "centro_costos": record.cost_center,
        "variante_programa": record.program_variant,
        "unidad_programa": record.program_unit,
        "tipo_objeto_programa": record.program_type,
        "creditos_minimos": record.minimum_credits,
        "creditos_maximos": record.maximum_credits,
        "creditos_optimos": record.optimal_credits,
        "creditos_maximos_snies": (record.maximum_snies_credits),
        "duracion_estudios": record.study_duration,
        "intensidad": record.intensity,
        "origen": "SAP_DATASPHERE",
    }


def execute(
    *,
    write: bool,
    max_pages: int | None,
    max_programs: int | None,
) -> dict[str, int | bool | None]:
    settings = get_settings()
    settings.validate_sap_programs_ready()

    pages_read = 0
    programs_read = 0
    programs_valid = 0
    programs_written = 0
    programs_searchable = 0
    total_reported: int | None = None

    program_ids: set[str] = set()

    repository: ProgramRepository | None = None

    try:
        if write:
            repository = ProgramRepository(settings)
            repository.verify_connectivity()
            print("Conexión Neo4j: OK")

        with SapProgramsClient(settings) as client:
            for page in client.iter_pages(page_size=settings.sap_odata_page_size):
                pages_read += 1

                if page.total_count is not None:
                    total_reported = page.total_count

                items = page.items

                if max_programs is not None:
                    remaining = max_programs - programs_read

                    if remaining <= 0:
                        break

                    items = items[:remaining]

                rows: list[dict] = []

                for position, item in enumerate(
                    items,
                    start=programs_read + 1,
                ):
                    try:
                        record = SapProgramRecord.model_validate(item)
                    except ValidationError as error:
                        raise ValueError(
                            f"Programa SAP inválido en posición {position}: {error}"
                        ) from error

                    if record.program_id in program_ids:
                        raise ValueError(
                            "HE_PRGRM duplicado recibido desde SAP: "
                            f"{record.program_id}"
                        )

                    program_ids.add(record.program_id)

                    row = to_neo4j_row(record)
                    rows.append(row)

                    programs_valid += 1

                    if row["busqueda_semantica_disponible"]:
                        programs_searchable += 1

                programs_read += len(items)

                if repository is not None and rows:
                    programs_written += repository.upsert_programs(
                        rows,
                        batch_size=250,
                    )

                print(
                    f"Página {pages_read}: "
                    f"leídos={len(items)}, "
                    f"válidos={len(rows)}, "
                    f"escritos={programs_written}"
                )

                if max_programs is not None and programs_read >= max_programs:
                    break

                if max_pages is not None and pages_read >= max_pages:
                    break

    finally:
        if repository is not None:
            repository.close()

    return {
        "sap_total_reported": total_reported,
        "pages_read": pages_read,
        "programs_read": programs_read,
        "programs_valid": programs_valid,
        "programs_unique": len(program_ids),
        "programs_searchable": programs_searchable,
        "programs_written": programs_written,
        "write_executed": write,
    }


def print_result(
    result: dict[str, int | bool | None],
) -> None:
    print()
    print("=== RESULTADO DE SINCRONIZACIÓN ===")
    print(f"Total informado por SAP: {result['sap_total_reported']}")
    print(f"Páginas procesadas: {result['pages_read']}")
    print(f"Programas leídos: {result['programs_read']}")
    print(f"Programas válidos: {result['programs_valid']}")
    print(f"Programas únicos: {result['programs_unique']}")
    print(f"Con texto semántico: {result['programs_searchable']}")
    print(f"Programas escritos: {result['programs_written']}")
    print(
        "Escritura en Neo4j: "
        + ("EJECUTADA" if result["write_executed"] else "NO EJECUTADA")
    )


def main() -> int:
    arguments = build_parser().parse_args()

    try:
        result = execute(
            write=arguments.write,
            max_pages=arguments.max_pages,
            max_programs=arguments.max_programs,
        )
    except (
        Neo4jError,
        ValueError,
        RuntimeError,
        TypeError,
    ) as error:
        print(f"Sincronización: ERROR ({type(error).__name__})")
        print(str(error))
        return 1

    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
