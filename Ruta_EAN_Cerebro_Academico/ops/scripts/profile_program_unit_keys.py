import json
from pathlib import Path

PROGRAMS_PATH = Path("data/raw/programas/programas_sap.json")
UNITS_PATH = Path("data/raw/unidades/unidades_estudio.json")
MATCHED_UNITS_PATH = Path("data/raw/unidades/unidades_con_programa.json")


def load_list(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise TypeError(f"{path} no contiene una lista JSON")

    return payload


def normalize_code(value: object) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip().upper()
    return normalized or None


def top_level_values(
    rows: list[dict],
    field: str,
) -> list[list[str]]:
    result: list[list[str]] = []

    for row in rows:
        value = normalize_code(row.get(field))
        result.append([value] if value else [])

    return result


def associated_snies_values(
    rows: list[dict],
) -> list[list[str]]:
    result: list[list[str]] = []

    for row in rows:
        associated = row.get("programas_asociados") or []
        values: list[str] = []

        if isinstance(associated, list):
            for program in associated:
                if not isinstance(program, dict):
                    continue

                value = normalize_code(program.get("snies_codigo"))
                if value:
                    values.append(value)

        result.append(values)

    return result


def calculate_match(
    unit_values: list[list[str]],
    program_values: set[str],
) -> tuple[int, int, int]:
    rows_with_code = 0
    matched_rows = 0
    matched_distinct_codes: set[str] = set()

    for values in unit_values:
        if not values:
            continue

        rows_with_code += 1
        matches = set(values) & program_values

        if matches:
            matched_rows += 1
            matched_distinct_codes.update(matches)

    return (
        rows_with_code,
        matched_rows,
        len(matched_distinct_codes),
    )


def main() -> None:
    programs = load_list(PROGRAMS_PATH)
    units = load_list(UNITS_PATH)
    matched_units = load_list(MATCHED_UNITS_PATH)

    program_fields = [
        "HE_PRGRM",
        "HE_PRGRMT",
        "SNIES_CODIGO",
    ]

    unit_candidates = {
        "codigo_plan_estudios": top_level_values(
            units,
            "codigo_plan_estudios",
        ),
        "codigo_unidad_estudio": top_level_values(
            units,
            "codigo_unidad_estudio",
        ),
        "programas_asociados.snies_codigo": (associated_snies_values(matched_units)),
    }

    print(f"Programas SAP: {len(programs)}")
    print(f"Unidades: {len(units)}")
    print(f"Unidades enriquecidas: {len(matched_units)}")

    print("\nCampos con 'codigo' encontrados en unidades:")
    unit_code_fields = sorted(
        {key for row in units for key in row if "codigo" in key.lower()}
    )

    for field in unit_code_fields:
        print(f"- {field}")

    print("\nMatriz de coincidencias exactas:")
    print(
        "campo_unidad | campo_programa | filas_con_codigo | filas_match | codigos_match"
    )

    for unit_field, values_by_row in unit_candidates.items():
        for program_field in program_fields:
            program_values = {
                value
                for row in programs
                if (value := normalize_code(row.get(program_field)))
            }

            (
                rows_with_code,
                matched_rows,
                matched_codes,
            ) = calculate_match(
                values_by_row,
                program_values,
            )

            print(
                f"{unit_field} | {program_field} | "
                f"{rows_with_code} | {matched_rows} | "
                f"{matched_codes}"
            )


if __name__ == "__main__":
    main()
