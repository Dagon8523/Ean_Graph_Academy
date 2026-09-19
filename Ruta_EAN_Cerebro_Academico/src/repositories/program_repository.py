from collections.abc import Iterable

from neo4j import Driver, GraphDatabase

from src.config.settings import Settings

UPSERT_PROGRAMS_QUERY = """
UNWIND $rows AS row

MERGE (p:ProgramaOficial {
    programa_id: row.programa_id
})

SET p += row,
    p.actualizado_en = datetime()

MERGE (f:FuenteDatos {
    fuente_id: 'sap_programas_oficiales'
})

ON CREATE SET
    f.nombre = 'SAP Datasphere - Programas oficiales',
    f.creado_en = datetime()

SET f.actualizado_en = datetime()

MERGE (p)-[:PROVIENE_DE]->(f)

RETURN count(p) AS procesados
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

    def upsert_programs(
        self,
        rows: Iterable[dict],
        batch_size: int = 250,
    ) -> int:
        batch: list[dict] = []
        total_processed = 0

        for row in rows:
            batch.append(row)

            if len(batch) >= batch_size:
                total_processed += self._write_batch(batch)
                batch = []

        if batch:
            total_processed += self._write_batch(batch)

        return total_processed

    def _write_batch(self, rows: list[dict]) -> int:
        with self.driver.session(database=self.settings.neo4j_database) as session:
            result = session.run(
                UPSERT_PROGRAMS_QUERY,
                rows=rows,
            )
            record = result.single()

        if record is None:
            return 0

        return int(record["procesados"])
