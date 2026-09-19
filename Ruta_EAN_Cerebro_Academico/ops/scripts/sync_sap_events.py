"""Sincroniza eventos de Educación Continuada con Neo4j."""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from neo4j.exceptions import Neo4jError

from src.config.settings import get_settings
from src.integrations.sap_events.client import SapODataClient
from src.integrations.sap_events.exceptions import SapODataError
from src.repositories.event_graph_repository import EventGraphRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sincronización de eventos SAP de Educación Continuada hacia Neo4j."
        ),
    )

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Lee y valida SAP sin escribir en Neo4j.",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Crea o actualiza los eventos en Neo4j.",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Cantidad máxima de páginas que se procesarán.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Cantidad máxima de eventos que se procesarán.",
    )

    return parser


async def execute(
    *,
    write: bool,
    max_pages: int | None,
    max_events: int | None,
) -> dict[str, int | bool | None]:
    settings = get_settings()

    pages_read = 0
    events_read = 0
    events_written = 0
    events_current = 0
    events_deleted = 0
    total_reported: int | None = None
    formation_ids: set[str] = set()

    repository: EventGraphRepository | None = None

    try:
        if write:
            repository = EventGraphRepository(settings)
            repository.verify_connectivity()
            print("Conexión Neo4j: OK")

        async with SapODataClient(settings) as sap_client:
            async for page in sap_client.iter_pages():
                pages_read += 1

                if page.total_count is not None:
                    total_reported = page.total_count

                events = page.items

                if max_events is not None:
                    remaining = max_events - events_read

                    if remaining <= 0:
                        break

                    events = events[:remaining]

                events_read += len(events)

                for event in events:
                    if event.training_id:
                        formation_ids.add(event.training_id)

                    if event.is_current_on(datetime.now(UTC).date()):
                        events_current += 1

                    if event.is_deleted:
                        events_deleted += 1

                if repository is not None:
                    events_written += repository.upsert_events(events)

                print(
                    f"Página {pages_read}: "
                    f"leídos={len(events)}, "
                    f"escritos={events_written}"
                )

                if max_events is not None and events_read >= max_events:
                    break

                if max_pages is not None and pages_read >= max_pages:
                    break
    finally:
        if repository is not None:
            repository.close()

    return {
        "sap_total_reported": total_reported,
        "pages_read": pages_read,
        "events_read": events_read,
        "events_written": events_written,
        "formations_unique": len(formation_ids),
        "events_current": events_current,
        "events_deleted": events_deleted,
        "write_executed": write,
    }


def print_result(result: dict[str, int | bool | None]) -> None:
    print()
    print("=== RESULTADO DE SINCRONIZACIÓN ===")
    print(f"Total informado por SAP: {result['sap_total_reported']}")
    print(f"Páginas procesadas: {result['pages_read']}")
    print(f"Eventos leídos: {result['events_read']}")
    print(f"Eventos escritos: {result['events_written']}")
    print(f"Formaciones únicas: {result['formations_unique']}")
    print(f"Eventos vigentes: {result['events_current']}")
    print(f"Eventos eliminados en SAP: {result['events_deleted']}")
    print(
        "Escritura en Neo4j: "
        + ("EJECUTADA" if result["write_executed"] else "NO EJECUTADA")
    )


def main() -> int:
    arguments = build_parser().parse_args()

    try:
        result = asyncio.run(
            execute(
                write=arguments.write,
                max_pages=arguments.max_pages,
                max_events=arguments.max_events,
            )
        )
    except (SapODataError, Neo4jError, ValueError) as error:
        print(f"Sincronización: ERROR ({type(error).__name__})")
        print(str(error))
        return 1

    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
