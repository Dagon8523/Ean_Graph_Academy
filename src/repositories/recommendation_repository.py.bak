from __future__ import annotations

from typing import Any, Self

from neo4j import Driver, GraphDatabase

from src.config.settings import Settings

SEARCH_CONTINUING_EDUCATION_QUERY = """
CALL db.index.fulltext.queryNodes(
    'formacion_busqueda_fulltext_idx',
    $search_query
)
YIELD node, score

OPTIONAL MATCH (node)-[:TIENE_EVENTO]->(event:Evento)
WHERE event.eliminado = false

WITH
    node,
    score,
    max(event.fecha_fin) AS ultima_fecha,
    min(
        CASE
            WHEN event.fecha_inicio > date()
            THEN event.fecha_inicio
        END
    ) AS proxima_fecha,
    count(
        CASE
            WHEN event.fecha_inicio <= date()
             AND event.fecha_fin >= date()
            THEN 1
        END
    ) AS eventos_vigentes

RETURN
    node.formacion_id AS formacion_id,
    coalesce(
        node.nombre,
        node.nombre_corto,
        left(node.texto_semantico, 120)
    ) AS nombre,
    score,
    eventos_vigentes,
    toString(proxima_fecha) AS proxima_fecha,
    toString(ultima_fecha) AS ultima_fecha,
    CASE
        WHEN eventos_vigentes > 0
            THEN 'VIGENTE'
        WHEN proxima_fecha IS NOT NULL
            THEN 'PROXIMA'
        ELSE 'SIN_OFERTA_DISPONIBLE'
    END AS disponibilidad

ORDER BY score DESC
LIMIT $limit
"""


SEARCH_OFFICIAL_PROGRAMS_QUERY = """
CALL db.index.fulltext.queryNodes(
    'programa_busqueda_fulltext_idx',
    $search_query
)
YIELD node, score

RETURN
    node.programa_id AS programa_id,
    node.snies_codigo AS snies_codigo,
    node.snies_descripcion_abreviada AS descripcion_abreviada,
    node.snies_distincion_genero AS distincion_genero,
    node.estado AS estado,
    node.modalidad AS modalidad,
    node.nivel_formacion AS nivel_formacion,
    score,
    'COINCIDENCIA_DIRECTA' AS origen

ORDER BY score DESC
LIMIT $limit
"""


SEARCH_PROGRAMS_BY_UNITS_QUERY = """
CALL db.index.fulltext.queryNodes(
    'unidad_busqueda_fulltext_idx',
    $search_query
)
YIELD node, score

MATCH (program:ProgramaOficial)-[:CONTIENE_UNIDAD]->(node)

WITH
    program,
    max(score) AS score,
    collect(
        DISTINCT {
            unidad_id: node.unidad_id,
            nombre: node.nombre_unidad_estudio
        }
    )[0..5] AS unidades_coincidentes

RETURN
    program.programa_id AS programa_id,
    program.snies_codigo AS snies_codigo,
    program.snies_descripcion_abreviada AS descripcion_abreviada,
    program.snies_distincion_genero AS distincion_genero,
    program.estado AS estado,
    program.modalidad AS modalidad,
    program.nivel_formacion AS nivel_formacion,
    score,
    'COINCIDENCIA_POR_UNIDAD' AS origen,
    unidades_coincidentes

ORDER BY score DESC
LIMIT $limit
"""


class RecommendationRepository:
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

    def search_continuing_education(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self._execute_search(
            SEARCH_CONTINUING_EDUCATION_QUERY,
            query=query,
            limit=limit,
        )

    def search_official_programs(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self._execute_search(
            SEARCH_OFFICIAL_PROGRAMS_QUERY,
            query=query,
            limit=limit,
        )

    def search_programs_by_units(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self._execute_search(
            SEARCH_PROGRAMS_BY_UNITS_QUERY,
            query=query,
            limit=limit,
        )

    def _execute_search(
        self,
        cypher: str,
        *,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            return []

        if limit < 1:
            raise ValueError("El límite debe ser mayor que cero")

        with self.driver.session(database=self.settings.neo4j_database) as session:
            result = session.run(
                cypher,
                search_query=query,
                limit=limit,
            )

            return [record.data() for record in result]
