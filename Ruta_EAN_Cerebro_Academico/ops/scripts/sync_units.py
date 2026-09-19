import json
from pathlib import Path

from src.config.settings import get_settings
from src.domain.unit_models import UnitStudyRecord
from src.repositories.unit_repository import (
    UnitRepository,
)

UNITS_PATH = Path("data/raw/unidades/unidades_estudio.json")


def main() -> None:
    with UNITS_PATH.open(encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise TypeError("unidades_estudio.json no contiene una lista")

    records = [UnitStudyRecord.model_validate(item) for item in payload]

    rows = [record.to_neo4j_row() for record in records]

    unit_ids = {row["unidad_id"] for row in rows}

    if len(unit_ids) != len(rows):
        raise RuntimeError("Existen unidades_id duplicados")

    searchable = sum(bool(row["busqueda_semantica_disponible"]) for row in rows)

    print(f"Unidades preparadas: {len(rows)}")
    print(f"Unidades con texto semántico: {searchable}")
    print(f"Unidades sin texto semántico: {len(rows) - searchable}")

    repository = UnitRepository(get_settings())

    try:
        repository.verify_connectivity()
        print("Conexión Neo4j: OK")

        processed = repository.upsert_units(
            rows,
            batch_size=100,
        )

        relationships = repository.create_program_relationships()
    finally:
        repository.close()

    print(f"Unidades procesadas: {processed}")
    print(f"Relaciones programa–unidad: {relationships}")
    print("Sincronización de unidades: OK")


if __name__ == "__main__":
    main()
