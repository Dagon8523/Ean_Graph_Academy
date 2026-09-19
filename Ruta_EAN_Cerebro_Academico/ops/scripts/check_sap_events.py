import asyncio

from src.config.settings import get_settings
from src.integrations.sap_events.client import (
    SapODataClient,
)


async def execute() -> None:
    settings = get_settings()
    settings.validate_sap_events_ready()

    events = []

    async with SapODataClient(settings) as client:
        async for event in client.iter_events():
            events.append(event)

            if len(events) >= 10:
                break

    print(f"Eventos validados: {len(events)}")

    for event in events[:3]:
        print(
            {
                "evento_id": event.event_id,
                "formacion_id": event.training_id,
                "nombre_formacion": event.training_name,
                "oferente_id": event.provider_id,
                "fecha_inicio": event.event_start_date,
                "eliminado": event.is_deleted,
            }
        )

    print("Prueba SAP Eventos: OK")


def main() -> None:
    asyncio.run(execute())


if __name__ == "__main__":
    main()
