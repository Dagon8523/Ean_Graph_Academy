import hashlib
import json
from pathlib import Path, PureWindowsPath

UNITS_PATH = Path("data/raw/unidades/unidades_estudio.json")


def normalize_component(value: object) -> str:
    if value is None:
        return ""

    return " ".join(str(value).strip().lower().split())


def extract_filename(file_path: object) -> str:
    if not file_path:
        return ""

    return PureWindowsPath(str(file_path)).name


def build_natural_key(unit: dict) -> str:
    components = [
        unit.get("folder_breadcrumb"),
        extract_filename(unit.get("file_path")),
        unit.get("sheet_name"),
        unit.get("codigo_plan_estudios"),
        unit.get("codigo_unidad_estudio"),
        unit.get("anio"),
    ]

    return "|".join(normalize_component(component) for component in components)


def build_unit_id(unit: dict) -> str:
    natural_key = build_natural_key(unit)
    content_fingerprint = build_content_fingerprint(unit)

    identity = f"{natural_key}|{content_fingerprint}"

    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def build_content_fingerprint(unit: dict) -> str:
    semantic_fields = [
        unit.get("descripcion_unidad"),
        unit.get("resultado_aprendizaje_unidad"),
        unit.get("contenidos_unidad"),
        unit.get("competencia_programa"),
        unit.get("estrategias_pedagogicas"),
        unit.get("esquema_calificacion"),
        unit.get("bibliografia_obligatoria"),
        unit.get("bibliografia_complementaria"),
    ]

    normalized_content = "|".join(
        normalize_component(value) for value in semantic_fields
    )

    return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()


def main() -> None:
    with UNITS_PATH.open(encoding="utf-8") as file:
        units = json.load(file)

    if not isinstance(units, list):
        raise TypeError("unidades_estudio.json no contiene una lista")

    natural_keys = [build_natural_key(unit) for unit in units]
    unit_ids = [build_unit_id(unit) for unit in units]

    unique_natural_keys = set(natural_keys)
    unique_unit_ids = set(unit_ids)

    duplicated_keys = sorted(
        {key for key in natural_keys if natural_keys.count(key) > 1}
    )

    empty_natural_keys = sum(not key.replace("|", "") for key in natural_keys)

    print(f"Unidades totales: {len(units)}")
    print(f"Llaves naturales únicas: {len(unique_natural_keys)}")
    print(f"Identificadores SHA-256 únicos: {len(unique_unit_ids)}")
    print(f"Llaves naturales completamente vacías: {empty_natural_keys}")
    print(f"Llaves naturales duplicadas: {len(duplicated_keys)}")

    if duplicated_keys:
        print("\nLlaves académicas compartidas por versiones diferentes:")
        for key in duplicated_keys[:10]:
            print(f"- {key}")

    if len(unique_unit_ids) != len(units):
        raise RuntimeError(
            "Existen registros con la misma llave académica y el mismo contenido"
        )

    print("\nIdentificación versionada de unidades: OK")
    print("Cada contenido académico diferente conserva su propia identidad.")
    print(f"Primer unidad_id: {unit_ids[0]}")


if __name__ == "__main__":
    main()
