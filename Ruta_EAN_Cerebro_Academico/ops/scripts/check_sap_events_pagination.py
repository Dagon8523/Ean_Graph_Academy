from __future__ import annotations

import asyncio

from src.config.settings import get_settings
from src.integrations.sap_events.client import SapODataClient


async def execute() -> None:
    settings = get_settings()

    pages = []

    async with SapODataClient(settings) as client:
        async for page in client.iter_pages():
            pages.append(page)

            print(f"Página {len(pages)}: {page.item_count} registros")

            if len(pages) == 2:
                break

    if len(pages) < 2:
        raise RuntimeError(
            "SAP no entregó dos páginas. Debe revisarse la paginación mediante $skip."
        )

    first_page_ids = {event.event_id for event in pages[0].items}
    second_page_ids = {event.event_id for event in pages[1].items}

    repeated_ids = first_page_ids & second_page_ids

    print()
    print(f"IDs únicos página 1: {len(first_page_ids)}")
    print(f"IDs únicos página 2: {len(second_page_ids)}")
    print(f"IDs repetidos entre páginas: {len(repeated_ids)}")

    if pages[0].items:
        print(f"Primer ID página 1: {pages[0].items[0].event_id}")
        print(f"Último ID página 1: {pages[0].items[-1].event_id}")

    if pages[1].items:
        print(f"Primer ID página 2: {pages[1].items[0].event_id}")
        print(f"Último ID página 2: {pages[1].items[-1].event_id}")

    if repeated_ids:
        sample = sorted(repeated_ids)[:10]
        raise RuntimeError(
            f"Se encontraron EVENTO_ID repetidos entre páginas: {sample}"
        )

    print()
    print("Prueba de paginación SAP Eventos: OK")


def main() -> None:
    asyncio.run(execute())


if __name__ == "__main__":
    main()
