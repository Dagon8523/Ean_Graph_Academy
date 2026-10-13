import json
from collections import defaultdict
from pathlib import Path

from ops.scripts.profile_unit_identifiers import (
    build_natural_key,
)

UNITS_PATH = Path("data/raw/unidades/unidades_estudio.json")


def compact(value: object, limit: int = 300) -> str:
    text = repr(value)

    if len(text) <= limit:
        return text

    return text[:limit] + "... [TRUNCADO]"


def main() -> None:
    with UNITS_PATH.open(encoding="utf-8") as file:
        units = json.load(file)

    if not isinstance(units, list):
        raise TypeError("unidades_estudio.json no contiene una lista")

    groups: dict[str, list[dict]] = defaultdict(list)

    for unit in units:
        groups[build_natural_key(unit)].append(unit)

    duplicated_groups = {
        key: records for key, records in groups.items() if len(records) > 1
    }

    print(f"Grupos duplicados encontrados: {len(duplicated_groups)}")

    for natural_key, records in duplicated_groups.items():
        print("\n" + "=" * 70)
        print(f"Llave: {natural_key}")
        print(f"Cantidad: {len(records)}")
        print(
            "Registros completamente idénticos: "
            f"{all(record == records[0] for record in records[1:])}"
        )

        all_fields = sorted({field for record in records for field in record})

        differing_fields = []

        for field in all_fields:
            values = [record.get(field) for record in records]

            if any(value != values[0] for value in values[1:]):
                differing_fields.append(field)

        print(f"Campos diferentes: {len(differing_fields)}")

        for field in differing_fields:
            print(f"\nCampo: {field}")

            for position, record in enumerate(
                records,
                start=1,
            ):
                print(f"  Registro {position}: {compact(record.get(field))}")


if __name__ == "__main__":
    main()
