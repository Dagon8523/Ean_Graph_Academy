from collections import Counter

from pydantic import ValidationError

from src.config.settings import get_settings
from src.domain.program_models import SapProgramRecord
from src.integrations.sap_odata.client import SapProgramsClient


def main() -> None:
    settings = get_settings()

    print("Validando configuración SAP...")
    settings.validate_sap_programs_ready()
    print("Configuración SAP: OK")

    with SapProgramsClient(settings) as client:
        page = client.fetch_page(page_size=100)

    print(f"Registros recibidos: {len(page.items)}")
    print(f"Conteo OData: {page.total_count}")
    print(f"Tiene siguiente página: {bool(page.next_link)}")

    if not page.items:
        raise RuntimeError("SAP OData respondió sin registros")

    print("\nColumnas recibidas:")
    for column in sorted(page.items[0].keys()):
        print(f"- {column}")

    valid_records: list[SapProgramRecord] = []
    validation_errors: list[str] = []

    for position, item in enumerate(page.items, start=1):
        try:
            valid_records.append(SapProgramRecord.model_validate(item))
        except ValidationError as exc:
            validation_errors.append(f"Registro {position}: {exc}")

    print(f"\nRegistros válidos: {len(valid_records)}")
    print(f"Registros inválidos: {len(validation_errors)}")

    if validation_errors:
        print("\nPrimeros errores:")
        for error in validation_errors[:5]:
            print(error)

    if not valid_records:
        raise RuntimeError("No fue posible validar ningún programa")

    statuses = Counter(record.snies_status or "SIN_ESTADO" for record in valid_records)

    print("\nEstados en la muestra:")
    for status, quantity in sorted(statuses.items()):
        print(f"- {status}: {quantity}")

    first = valid_records[0]

    print("\nPrimer programa validado:")
    print(f"- programa_id: {first.program_id}")
    print(f"- codigo_programa SAP: {first.program_code}")
    print(f"- codigo_SNIES: {first.snies_code}")
    print(f"- descripción abreviada: {first.snies_short_description}")
    print(f"- distinción de género: {first.snies_gender_distinction}")
    print(f"- texto semántico: {first.semantic_text!r}")

    print("\nPrueba SAP Programas: OK")


if __name__ == "__main__":
    main()
