import json
from pathlib import Path

from src.config.settings import get_settings
from src.domain.program_models import SapProgramRecord
from src.repositories.program_repository import (
    ProgramRepository,
)

PROGRAMS_PATH = Path("data/raw/programas/programas_sap.json")


def load_programs() -> list[dict]:
    with PROGRAMS_PATH.open(encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise TypeError("programas_sap.json no contiene una lista")

    return payload


def to_neo4j_row(
    record: SapProgramRecord,
) -> dict:
    return {
        "programa_id": record.program_id,
        "codigo_programa": record.program_code,
        "codigo_snies": record.snies_code,
        "descripcion_abreviada": (record.snies_short_description),
        "distincion_genero": (record.snies_gender_distinction),
        "snies_descripcion_abreviada": (record.snies_short_description),
        "snies_distincion_genero": (record.snies_gender_distinction),
        "texto_semantico": record.semantic_text or None,
        "busqueda_semantica_disponible": bool(record.semantic_text),
        "estado": record.snies_status,
        "facultad": record.snies_faculty,
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


def main() -> None:
    settings = get_settings()
    raw_programs = load_programs()

    records = [SapProgramRecord.model_validate(item) for item in raw_programs]

    rows = [to_neo4j_row(record) for record in records]

    searchable = sum(row["busqueda_semantica_disponible"] for row in rows)

    print(f"Programas preparados: {len(rows)}")
    print(f"Programas con texto semántico: {searchable}")
    print(f"Programas sin texto semántico: {len(rows) - searchable}")

    repository = ProgramRepository(settings)

    try:
        repository.verify_connectivity()
        print("Conexión Neo4j: OK")

        processed = repository.upsert_programs(
            rows,
            batch_size=250,
        )
    finally:
        repository.close()

    print(f"Programas procesados: {processed}")
    print("Sincronización SAP Programas: OK")


if __name__ == "__main__":
    main()
