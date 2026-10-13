import re
import unicodedata
from collections.abc import Iterable
from typing import Any

from neo4j import Driver, GraphDatabase, Transaction

from src.config.settings import Settings

UPSERT_PROGRAMS_QUERY = """
UNWIND $rows AS row

MERGE (p:ProgramaOficial {
    programa_id: row.programa_id
})

SET p += row,
    p.actualizado_en = datetime()

REMOVE
    p.modalidad_id,
    p.nivel_formacion_id,
    p.tipo_programa_id

RETURN count(p) AS procesados
"""


SYNC_MODALITIES_QUERY = """
UNWIND $rows AS row

MATCH (p:ProgramaOficial {
    programa_id: row.programa_id
})

OPTIONAL MATCH (p)-[old:TIENE_MODALIDAD]->(:Modalidad)
DELETE old

WITH DISTINCT p, row

FOREACH (
    _ IN CASE
        WHEN row.modalidad_id IS NOT NULL THEN [1]
        ELSE []
    END |

    MERGE (m:Modalidad {
        modalidad_id: row.modalidad_id
    })

    ON CREATE SET
        m.creado_en = datetime()

    SET
        m.nombre = row.modalidad,
        m.origen = 'SAP_DATASPHERE',
        m.actualizado_en = datetime()

    MERGE (p)-[r:TIENE_MODALIDAD]->(m)

    SET
        r.actualizado_en = datetime()
)
"""


SYNC_LEVELS_QUERY = """
UNWIND $rows AS row

MATCH (p:ProgramaOficial {
    programa_id: row.programa_id
})

OPTIONAL MATCH (p)-[old:TIENE_NIVEL]->(:NivelFormacion)
DELETE old

WITH DISTINCT p, row

FOREACH (
    _ IN CASE
        WHEN row.nivel_formacion_id IS NOT NULL THEN [1]
        ELSE []
    END |

    MERGE (n:NivelFormacion {
        nivel_id: row.nivel_formacion_id
    })

    ON CREATE SET
        n.creado_en = datetime()

    SET
        n.nombre = row.nivel_formacion,
        n.origen = 'SAP_DATASPHERE',
        n.actualizado_en = datetime()

    MERGE (p)-[r:TIENE_NIVEL]->(n)

    SET
        r.actualizado_en = datetime()
)
"""


SYNC_TYPES_QUERY = """
UNWIND $rows AS row

MATCH (p:ProgramaOficial {
    programa_id: row.programa_id
})

OPTIONAL MATCH (p)-[old:ES_TIPO]->(:TipoPrograma)
DELETE old

WITH DISTINCT p, row

FOREACH (
    _ IN CASE
        WHEN row.tipo_programa_id IS NOT NULL THEN [1]
        ELSE []
    END |

    MERGE (t:TipoPrograma {
        tipo_programa_id: row.tipo_programa_id
    })

    ON CREATE SET
        t.creado_en = datetime()

    SET
        t.nombre = row.tipo_programa_global,
        t.origen = 'SAP_DATASPHERE',
        t.actualizado_en = datetime()

    MERGE (p)-[r:ES_TIPO]->(t)

    SET
        r.actualizado_en = datetime()
)
"""


class ProgramRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.driver: Driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_user,
                settings.neo4j_password.get_secret_value(),
            ),
        )

    def close(self) -> None:
        self.driver.close()

    def verify_connectivity(self) -> None:
        self.driver.verify_connectivity()

    @staticmethod
    def _normalize_dimension_id(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        normalized = unicodedata.normalize(
            "NFKD",
            normalized,
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        normalized = normalized.lower()

        normalized = re.sub(
            r"[^a-z0-9]+",
            "-",
            normalized,
        )

        normalized = normalized.strip("-")

        return normalized or None

    @classmethod
    def _prepare_row(
        cls,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        prepared = dict(row)

        prepared["modalidad_id"] = cls._normalize_dimension_id(
            prepared.get("modalidad")
        )

        prepared["nivel_formacion_id"] = cls._normalize_dimension_id(
            prepared.get("nivel_formacion")
        )

        prepared["tipo_programa_id"] = cls._normalize_dimension_id(
            prepared.get("tipo_programa_global")
        )

        return prepared

    def upsert_programs(
        self,
        rows: Iterable[dict],
        batch_size: int = 250,
    ) -> int:
        batch: list[dict] = []
        total_processed = 0

        for row in rows:
            batch.append(self._prepare_row(row))

            if len(batch) >= batch_size:
                total_processed += self._write_batch(batch)
                batch = []

        if batch:
            total_processed += self._write_batch(batch)

        return total_processed

    def _write_batch(
        self,
        rows: list[dict],
    ) -> int:
        with self.driver.session(database=self.settings.neo4j_database) as session:
            return session.execute_write(
                self._write_batch_transaction,
                rows,
            )

    @staticmethod
    def _write_batch_transaction(
        transaction: Transaction,
        rows: list[dict],
    ) -> int:
        result = transaction.run(
            UPSERT_PROGRAMS_QUERY,
            rows=rows,
        )

        record = result.single()

        processed = int(record["procesados"]) if record is not None else 0

        transaction.run(
            SYNC_MODALITIES_QUERY,
            rows=rows,
        ).consume()

        transaction.run(
            SYNC_LEVELS_QUERY,
            rows=rows,
        ).consume()

        transaction.run(
            SYNC_TYPES_QUERY,
            rows=rows,
        ).consume()

        return processed
