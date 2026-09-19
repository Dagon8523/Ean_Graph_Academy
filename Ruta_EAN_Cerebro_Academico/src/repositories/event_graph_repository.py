from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Self

from neo4j import Driver, GraphDatabase

from src.config.settings import Settings
from src.integrations.sap_events.models import SapEventRecord

UPSERT_EVENTS_QUERY = """
UNWIND $rows AS row

MERGE (evento:Evento {evento_id: row.evento.evento_id})
SET evento += row.evento

FOREACH (_ IN CASE WHEN row.formacion IS NULL THEN [] ELSE [1] END |
    MERGE (formacion:Formacion {formacion_id: row.formacion.formacion_id})
    SET formacion += row.formacion
    MERGE (formacion)-[:TIENE_EVENTO]->(evento)
)

FOREACH (_ IN CASE WHEN row.grupo IS NULL THEN [] ELSE [1] END |
    MERGE (grupo:GrupoFormacion {id: row.grupo.id})
    SET grupo += row.grupo
    MERGE (evento)-[:PERTENECE_A_GRUPO]->(grupo)
)

FOREACH (_ IN CASE WHEN row.metodo IS NULL THEN [] ELSE [1] END |
    MERGE (metodo:MetodoFormacion {id: row.metodo.id})
    SET metodo += row.metodo
    MERGE (evento)-[:USA_METODO]->(metodo)
)

FOREACH (_ IN CASE WHEN row.sede IS NULL THEN [] ELSE [1] END |
    MERGE (sede:Sede {id: row.sede.id})
    SET sede += row.sede
    MERGE (evento)-[:OCURRE_EN]->(sede)
)
FOREACH (_ IN CASE WHEN row.oferente IS NULL THEN [] ELSE [1] END |
    MERGE (oferente:Oferente {id: row.oferente.id})
    SET oferente += row.oferente
    MERGE (evento)-[:GESTIONADO_POR]->(oferente)
)

FOREACH (_ IN CASE WHEN row.facultad IS NULL THEN [] ELSE [1] END |
    MERGE (facultad:Facultad {id: row.facultad.id})
    SET facultad += row.facultad
    MERGE (evento)-[:ADSCRITO_A]->(facultad)
)

FOREACH (_ IN CASE WHEN row.centro_costos IS NULL THEN [] ELSE [1] END |
    MERGE (centro:CentroCostos {id: row.centro_costos.id})
    SET centro += row.centro_costos
    MERGE (evento)-[:IMPUTADO_A]->(centro)
)

RETURN count(*) AS processed
"""


class EventGraphRepository:
    """Crea o actualiza eventos y dimensiones en Neo4j."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.driver: Driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_user,
                settings.neo4j_password.get_secret_value(),
            ),
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        self.close()

    def close(self) -> None:
        self.driver.close()

    def verify_connectivity(self) -> None:
        self.driver.verify_connectivity()

    def upsert_events(
        self,
        events: Sequence[SapEventRecord],
    ) -> int:
        """Inserta o actualiza un lote mediante MERGE."""

        if not events:
            return 0

        rows = [self._serialize_event(event) for event in events]

        with self.driver.session(database=self.settings.neo4j_database) as session:
            record = session.run(
                UPSERT_EVENTS_QUERY,
                rows=rows,
            ).single()

        if record is None:
            return 0

        return int(record["processed"])

    @classmethod
    def _serialize_event(
        cls,
        event: SapEventRecord,
    ) -> dict[str, Any]:
        """Convierte el contrato SAP en parámetros compatibles con Neo4j."""

        return {
            "evento": {
                "evento_id": event.event_id,
                "tipo_objeto": event.event_object_type,
                "codigo_corto": event.event_short_code,
                "nombre": event.event_name,
                "fecha_inicio": event.event_start_date,
                "fecha_fin": event.event_end_date,
                "duracion_dias": event.duration_days,
                "duracion_horas": cls._decimal(event.duration_hours),
                "capacidad_minima": event.minimum_capacity,
                "capacidad_maxima": event.maximum_capacity,
                "capacidad_optima": event.optimal_capacity,
                "precio_externo": cls._decimal(event.external_price),
                "moneda_precio_externo": event.external_price_currency,
                "precio_interno": cls._decimal(event.internal_price),
                "moneda_precio_interno": event.internal_price_currency,
                "costo": cls._decimal(event.cost),
                "moneda_costo": event.cost_currency,
                "permite_evaluacion": event.assessment_code,
                "publicado": event.published_code,
                "tipo_publicacion": event.publication_type,
                "estado_sap": event.sap_status,
                "eliminado": event.is_deleted,
                "idioma": event.language_code,
                "area_control": event.controlling_area,
                "sector": event.sector,
                "canal_distribucion": event.distribution_channel,
                "seguimiento": event.follow_up_code,
                "total_participaciones": event.total_participations,
                "fuente": "SAP_DATASPHERE",
            },
            "formacion": cls._optional_node(
                event.training_id,
                {
                    "tipo_objeto": event.training_object_type,
                    "nombre_corto": event.training_short_name,
                    "nombre": event.training_name,
                    "texto_semantico": event.semantic_text,
                },
                id_property="formacion_id",
            ),
            "grupo": cls._optional_node(
                event.training_group_id,
                {
                    "nombre_corto": event.training_group_short_name,
                    "nombre": event.training_group_name,
                },
            ),
            "metodo": cls._optional_node(
                event.training_method_id,
                {
                    "nombre_corto": event.training_method_short_name,
                    "nombre_singular": event.training_method_singular_name,
                    "nombre": event.training_method_name,
                },
            ),
            "sede": cls._optional_node(
                event.location_id,
                {
                    "nombre_corto": event.location_short_name,
                    "nombre": event.location_name,
                },
            ),
            "oferente": cls._optional_node(
                event.provider_id,
                {
                    "tipo_objeto": event.provider_object_type,
                    "nombre_corto": event.provider_short_name,
                    "nombre": event.provider_name,
                    "proceso": event.provider_process,
                    "nivel_1": event.provider_level_1,
                    "nivel_2": event.provider_level_2,
                    "nivel_3": event.provider_level_3,
                },
            ),
            "facultad": cls._optional_node(
                event.faculty_id,
                {
                    "nombre_corto": event.faculty_short_name,
                    "nombre": event.faculty_name,
                    "proceso": event.faculty_process,
                    "nivel_1": event.faculty_level_1,
                    "nivel_2": event.faculty_level_2,
                    "nivel_3": event.faculty_level_3,
                },
            ),
            "centro_costos": cls._optional_node(
                event.cost_center_id,
                {
                    "nombre_corto": event.cost_center_short_name,
                    "nombre_medio": event.cost_center_medium_name,
                    "nombre": event.cost_center_name,
                    "linea_negocio": event.cost_center_business_line,
                    "gerencia": event.cost_center_management,
                },
            ),
        }

    @staticmethod
    def _optional_node(
        node_id: str | None,
        properties: dict[str, Any],
        *,
        id_property: str = "id",
    ) -> dict[str, Any] | None:
        """Construye un nodo opcional eliminando propiedades nulas."""

        if node_id is None:
            return None

        return {
            id_property: node_id,
            **{key: value for key, value in properties.items() if value is not None},
        }

    @staticmethod
    def _decimal(value: Decimal | None) -> float | None:
        """Convierte Decimal a un tipo almacenable en Neo4j."""

        if value is None:
            return None

        return float(value)
