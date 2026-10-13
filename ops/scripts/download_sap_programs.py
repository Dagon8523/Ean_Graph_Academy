import json
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from src.config.settings import get_settings
from src.domain.program_models import SapProgramRecord
from src.integrations.sap_odata.client import SapProgramsClient

OUTPUT_PATH = Path("data/raw/programas/programas_sap.json")
TEMP_PATH = Path("data/raw/programas/programas_sap.tmp.json")


def main() -> None:
    settings = get_settings()
    settings.validate_sap_programs_ready()

    raw_records: list[dict[str, object]] = []
    valid_records: list[SapProgramRecord] = []
    validation_errors: list[str] = []

    print("Iniciando descarga completa de programas SAP...")

    with SapProgramsClient(settings) as client:
        for page_number, page in enumerate(
            client.iter_pages(page_size=settings.sap_odata_page_size),
            start=1,
        ):
            print(f"Página {page_number}: {len(page.items)} registros")

            raw_records.extend(page.items)

            for position, item in enumerate(
                page.items,
                start=len(raw_records) - len(page.items) + 1,
            ):
                try:
                    valid_records.append(SapProgramRecord.model_validate(item))
                except ValidationError as exc:
                    validation_errors.append(f"Registro {position}: {exc}")

    print(f"\nRegistros descargados: {len(raw_records)}")
    print(f"Registros válidos: {len(valid_records)}")
    print(f"Registros inválidos: {len(validation_errors)}")

    if validation_errors:
        print("\nPrimeros errores:")
        for error in validation_errors[:10]:
            print(error)

        raise RuntimeError(
            "La descarga contiene registros inválidos. "
            "No se generó el archivo definitivo."
        )

    program_ids = [record.program_id for record in valid_records]
    unique_program_ids = set(program_ids)

    duplicate_ids = [
        program_id
        for program_id, quantity in Counter(program_ids).items()
        if quantity > 1
    ]

    statuses = Counter(record.snies_status or "SIN_ESTADO" for record in valid_records)

    with TEMP_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            raw_records,
            file,
            ensure_ascii=False,
            indent=2,
        )

    TEMP_PATH.replace(OUTPUT_PATH)

    print(f"IDs únicos HE_PRGRM: {len(unique_program_ids)}")
    print(f"IDs duplicados HE_PRGRM: {len(duplicate_ids)}")

    if duplicate_ids:
        print(
            "Primeros IDs duplicados:",
            duplicate_ids[:10],
        )

    print("\nEstados:")
    for status, quantity in sorted(statuses.items()):
        print(f"- {status}: {quantity}")

    print(f"\nArchivo generado: {OUTPUT_PATH}")
    print("Descarga completa SAP Programas: OK")


if __name__ == "__main__":
    main()
