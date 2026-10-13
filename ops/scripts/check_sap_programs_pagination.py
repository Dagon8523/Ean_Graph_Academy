from src.config.settings import get_settings
from src.domain.program_models import SapProgramRecord
from src.integrations.sap_odata.client import SapProgramsClient


def extract_ids(items: list[dict[str, object]]) -> list[str]:
    records = [SapProgramRecord.model_validate(item) for item in items]
    return [record.program_id for record in records]


def main() -> None:
    settings = get_settings()
    page_size = 100

    with SapProgramsClient(settings) as client:
        first_page = client.fetch_page(
            page_size=page_size,
            skip=0,
        )
        second_page = client.fetch_page(
            page_size=page_size,
            skip=page_size,
        )

    first_ids = extract_ids(first_page.items)
    second_ids = extract_ids(second_page.items)

    repeated_ids = sorted(set(first_ids) & set(second_ids))

    print(f"Página 1: {len(first_ids)} registros")
    print(f"Página 2: {len(second_ids)} registros")
    print(f"IDs únicos página 1: {len(set(first_ids))}")
    print(f"IDs únicos página 2: {len(set(second_ids))}")
    print(f"IDs repetidos entre páginas: {len(repeated_ids)}")

    if first_ids:
        print(f"Primer ID página 1: {first_ids[0]}")
        print(f"Último ID página 1: {first_ids[-1]}")

    if second_ids:
        print(f"Primer ID página 2: {second_ids[0]}")
        print(f"Último ID página 2: {second_ids[-1]}")

    if first_ids == second_ids:
        raise RuntimeError("SAP parece ignorar $skip: ambas páginas son idénticas")

    if repeated_ids:
        print(
            "\nADVERTENCIA: existen IDs repetidos entre las páginas. "
            "Esto puede indicar duplicados legítimos o paginación inestable."
        )
        print("Primeros IDs repetidos:", repeated_ids[:10])

    print("\nPrueba de paginación SAP: OK")


if __name__ == "__main__":
    main()
