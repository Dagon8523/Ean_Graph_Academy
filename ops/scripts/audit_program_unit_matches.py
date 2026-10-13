import json
from collections import Counter, defaultdict
from pathlib import Path

PROGRAMS_PATH = Path("data/raw/programas/programas_sap.json")
UNITS_PATH = Path("data/raw/unidades/unidades_estudio.json")
OUTPUT_PATH = Path("data/processed/auditoria_programas_unidades.json")


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


def main() -> None:
    programs = load_list(PROGRAMS_PATH)
    units = load_list(UNITS_PATH)

    programs_by_code: dict[str, list[dict]] = defaultdict(list)

    for program in programs:
        code = normalize_code(program.get("HE_PRGRMT"))
        if code:
            programs_by_code[code].append(program)

    matched_units: list[dict] = []
    unmatched_units: list[dict] = []
    units_without_code: list[dict] = []
    ambiguous_units: list[dict] = []

    for unit in units:
        plan_code = normalize_code(unit.get("codigo_plan_estudios"))

        unit_summary = {
            "codigo_plan_estudios": plan_code,
            "codigo_unidad_estudio": unit.get("codigo_unidad_estudio"),
            "nombre_unidad_estudio": unit.get("nombre_unidad_estudio"),
            "programa": unit.get("programa"),
            "anio": unit.get("anio"),
            "modalidad": unit.get("modalidad"),
            "sheet_name": unit.get("sheet_name"),
        }

        if not plan_code:
            units_without_code.append(unit_summary)
            continue

        matching_programs = programs_by_code.get(
            plan_code,
            [],
        )

        if not matching_programs:
            unmatched_units.append(unit_summary)
            continue

        if len(matching_programs) > 1:
            unit_summary["programas_encontrados"] = [
                {
                    "HE_PRGRM": program.get("HE_PRGRM"),
                    "HE_PRGRMT": program.get("HE_PRGRMT"),
                    "SNIES_CODIGO": program.get("SNIES_CODIGO"),
                    "SNIES_DESCRIPCION_ABREVIADA": (
                        program.get("SNIES_DESCRIPCION_ABREVIADA")
                    ),
                }
                for program in matching_programs
            ]
            ambiguous_units.append(unit_summary)
            continue

        program = matching_programs[0]

        unit_summary["programa_encontrado"] = {
            "HE_PRGRM": program.get("HE_PRGRM"),
            "HE_PRGRMT": program.get("HE_PRGRMT"),
            "SNIES_CODIGO": program.get("SNIES_CODIGO"),
            "SNIES_DESCRIPCION_ABREVIADA": program.get("SNIES_DESCRIPCION_ABREVIADA"),
        }
        matched_units.append(unit_summary)

    unmatched_code_counts = Counter(
        unit["codigo_plan_estudios"] for unit in unmatched_units
    )

    duplicated_program_codes = {
        code: [program.get("HE_PRGRM") for program in matching_programs]
        for code, matching_programs in programs_by_code.items()
        if len(matching_programs) > 1
    }

    report = {
        "resumen": {
            "programas_sap": len(programs),
            "codigos_programa_distintos": len(programs_by_code),
            "unidades_totales": len(units),
            "unidades_match_exacto": len(matched_units),
            "unidades_sin_match": len(unmatched_units),
            "unidades_sin_codigo": len(units_without_code),
            "unidades_match_ambiguo": len(ambiguous_units),
            "codigos_programa_duplicados_sap": len(duplicated_program_codes),
        },
        "codigos_programa_duplicados_sap": (duplicated_program_codes),
        "codigos_no_encontrados": [
            {
                "codigo_plan_estudios": code,
                "cantidad_unidades": quantity,
            }
            for code, quantity in (unmatched_code_counts.most_common())
        ],
        "unidades_sin_match": unmatched_units,
        "unidades_sin_codigo": units_without_code,
        "unidades_match_ambiguo": ambiguous_units,
        "unidades_match_exacto": matched_units,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("Resumen de relación programa–unidad:")
    for key, value in report["resumen"].items():
        print(f"- {key}: {value}")

    print(f"\nReporte generado: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
