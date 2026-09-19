from collections.abc import Iterable

from neo4j import Driver, GraphDatabase

from src.config.settings import Settings

UPSERT_UNITS_QUERY = """
UNWIND $rows AS row

MERGE (u:UnidadEstudio {
    unidad_id: row.unidad_id
})

SET u += row,
    u.actualizado_en = datetime()

MERGE (f:FuenteDatos {
    fuente_id: 'syllabus_unidades_estudio'
})

ON CREATE SET
    f.nombre = 'Syllabus - Unidades de estudio',
    f.creado_en = datetime()

SET f.actualizado_en = datetime()

MERGE (u)-[:PROVIENE_DE]->(f)

RETURN count(u) AS procesados
"""


CREATE_PROGRAM_RELATIONSHIPS_QUERY = """
MATCH (u:UnidadEstudio)
WHERE u.codigo_programa IS NOT NULL
  AND trim(u.codigo_programa) <> ''

MATCH (p:ProgramaOficial {
    codigo_programa: u.codigo_programa
})

MERGE (p)-[r:CONTIENE_UNIDAD]->(u)

SET r.metodo = 'codigo_programa_exacto',
    r.validada = true,
    r.actualizado_en = datetime()

RETURN count(r) AS relaciones
"""


class UnitRepository:
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

    def upsert_units(
        self,
        rows: Iterable[dict],
        batch_size: int = 100,
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
            record = session.run(
                UPSERT_UNITS_QUERY,
                rows=rows,
            ).single()

        return int(record["procesados"]) if record else 0

    def create_program_relationships(self) -> int:
        with self.driver.session(database=self.settings.neo4j_database) as session:
            record = session.run(CREATE_PROGRAM_RELATIONSHIPS_QUERY).single()

        return int(record["relaciones"]) if record else 0
