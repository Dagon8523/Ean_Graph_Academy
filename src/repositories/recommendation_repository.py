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
    node.codigo_snies AS snies_codigo,
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

WITH node, score
WHERE coalesce(node.requiere_revision_contenido, false) = false
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
    program.codigo_snies AS snies_codigo,
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


SEARCH_UNITS_QUERY = """
CALL db.index.fulltext.queryNodes('unidad_busqueda_fulltext_idx', $search_query)
YIELD node, score
WITH node, score
WHERE coalesce(node.requiere_revision_contenido, false) = false
OPTIONAL MATCH (p:ProgramaOficial)-[:CONTIENE_UNIDAD]->(node)
RETURN node.unidad_id AS unidad_id, node.nombre_unidad_estudio AS nombre,
       node.estado_relacion_programa AS estado_programa,
       score, collect(p { .programa_id, .codigo_programa,
       nombre: p.snies_descripcion_abreviada }) AS programas
ORDER BY score DESC, unidad_id LIMIT $limit
"""

SEARCH_EANX_QUERY = """
CALL db.index.fulltext.queryNodes('eanx_busqueda_fulltext_idx', $search_query)
YIELD node, score
WITH node, score
WHERE node:FormacionEANX OR (node:ModuloEANX AND NOT
 coalesce(node.nombre, '') =~ '(?i)^(\\\\s*(m[oó]dulo\\\\s*)?[0-9]+\\\\s*[:.-]?\\\\s*)?(presentaci[oó]n|bienvenida|evaluaci[oó]n|autoevaluaci[oó]n|inicio ruta|reglas de juego|nuestro experto|nuestra experta|foro de discusi[oó]n).*')
OPTIONAL MATCH (curso:FormacionEANX)-[:TIENE_MODULO]->(node)
RETURN CASE WHEN node:FormacionEANX THEN 'FormacionEANX' ELSE 'ModuloEANX' END AS tipo,
       CASE WHEN node:FormacionEANX THEN node.eanx_id ELSE node.modulo_id END AS id,
       coalesce(node.titulo, node.nombre) AS nombre, node.descripcion AS descripcion,
       score, collect(curso { .eanx_id, .titulo }) AS cursos_contenedores
ORDER BY score DESC, id LIMIT $limit
"""

SEMANTIC_PATHS_QUERY = """
UNWIND $seeds AS seed
MATCH (matched)
WHERE (seed.tipo = 'UnidadEstudio' AND matched:UnidadEstudio AND matched.unidad_id = seed.id)
   OR (seed.tipo = 'ProgramaOficial' AND matched:ProgramaOficial AND matched.programa_id = seed.id)
   OR (seed.tipo = 'Formacion' AND matched:Formacion AND matched.formacion_id = seed.id)
   OR (seed.tipo = 'FormacionEANX' AND matched:FormacionEANX AND matched.eanx_id = seed.id)
   OR (seed.tipo = 'ModuloEANX' AND matched:ModuloEANX AND matched.modulo_id = seed.id)
WITH matched, seed
WHERE coalesce(matched.requiere_revision_contenido, false) = false
MATCH (a)
WHERE a = matched OR (seed.tipo IN labels(a)
 AND a.embedding_text_hash = matched.embedding_text_hash
 AND a.embedding_model = matched.embedding_model
 AND a.embedding_text_version = matched.embedding_text_version)
MATCH path = (a)-[:RELACIONADA_SEMANTICAMENTE*1..2]-(b)
WHERE all(n IN nodes(path) WHERE coalesce(n.requiere_revision_contenido, false) = false)
  AND all(r IN relationships(path) WHERE r.validada = true
    AND r.pipeline = 'academic_similarity_v25_hybrid'
    AND r.origen_text_hash = startNode(r).embedding_text_hash
    AND r.destino_text_hash = endNode(r).embedding_text_hash
    AND r.origen_version_texto = startNode(r).embedding_text_version
    AND r.destino_version_texto = endNode(r).embedding_text_version)
  AND a <> b
WITH DISTINCT path, seed, matched, a, length(path) AS saltos
RETURN seed AS origen, saltos, a <> matched AS usa_representante_textual,
 [n IN nodes(path) | {
   tipo: head([label IN labels(n) WHERE label IN
    ['UnidadEstudio','ProgramaOficial','Formacion','FormacionEANX','ModuloEANX']]),
   id: CASE WHEN n:UnidadEstudio THEN n.unidad_id
            WHEN n:ProgramaOficial THEN n.programa_id
            WHEN n:Formacion THEN n.formacion_id
            WHEN n:FormacionEANX THEN n.eanx_id
            WHEN n:ModuloEANX THEN n.modulo_id END,
   nombre: coalesce(n.nombre_unidad_estudio,n.titulo,n.nombre,n.snies_descripcion_abreviada),
   estado_programa: n.estado_relacion_programa
 }] AS nodos,
 [r IN relationships(path) | {
   similitud: r.similitud, puntaje_hibrido: r.puntaje_hibrido,
   naturaleza: r.naturaleza, validada: r.validada
 }] AS conexiones
ORDER BY saltos, seed.tipo, seed.id LIMIT $limit
"""

CONTINUING_BY_IDS_QUERY = SEARCH_CONTINUING_EDUCATION_QUERY.replace(
    "CALL db.index.fulltext.queryNodes(\n    'formacion_busqueda_fulltext_idx',\n    $search_query\n)\nYIELD node, score",
    "MATCH (node:Formacion) WHERE node.formacion_id IN $ids WITH node, 0.0 AS score",
)

PROGRAMS_FOR_UNITS_QUERY = (
    "UNWIND $units AS item MATCH (node:UnidadEstudio) "
    "WHERE node.unidad_id = item.unidad_id "
    "AND coalesce(node.requiere_revision_contenido, false) = false "
    "WITH node, item.score AS score MATCH (program"
    + SEARCH_PROGRAMS_BY_UNITS_QUERY.split("MATCH (program", 1)[1]
)

CONTAINERS_QUERY = """
UNWIND $nodes AS seed
MATCH (p:ProgramaOficial)-[:CONTIENE_UNIDAD]->(u:UnidadEstudio)
WHERE seed.tipo = 'UnidadEstudio' AND u.unidad_id = seed.id
  AND coalesce(u.requiere_revision_contenido, false) = false
RETURN DISTINCT 'CONTIENE_UNIDAD' AS relacion,
 {tipo:'ProgramaOficial',id:p.programa_id,nombre:p.snies_descripcion_abreviada} AS origen,
 {tipo:'UnidadEstudio',id:u.unidad_id,nombre:u.nombre_unidad_estudio} AS destino
UNION
UNWIND $nodes AS seed
MATCH (c:FormacionEANX)-[:TIENE_MODULO]->(m:ModuloEANX)
WHERE seed.tipo = 'ModuloEANX' AND m.modulo_id = seed.id
RETURN DISTINCT 'TIENE_MODULO' AS relacion,
 {tipo:'FormacionEANX',id:c.eanx_id,nombre:c.titulo} AS origen,
 {tipo:'ModuloEANX',id:m.modulo_id,nombre:m.nombre} AS destino
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

    def search_units(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._execute_search(SEARCH_UNITS_QUERY, query=query, limit=limit)

    def search_programs_for_units(self, units: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
        if not units:
            return []
        with self.driver.session(database=self.settings.neo4j_database) as session:
            return [r.data() for r in session.run(PROGRAMS_FOR_UNITS_QUERY,
                units=[{"unidad_id": u["unidad_id"], "score": u["score"]} for u in units], limit=limit)]

    def search_eanx(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._execute_search(SEARCH_EANX_QUERY, query=query, limit=limit)

    def find_semantic_paths(self, seeds: list[dict[str, str]], limit: int = 50) -> list[dict[str, Any]]:
        if not seeds:
            return []
        with self.driver.session(database=self.settings.neo4j_database) as session:
            return [r.data() for r in session.run(SEMANTIC_PATHS_QUERY, seeds=seeds, limit=limit)]

    def get_continuing_education_by_ids(self, ids: list[str], limit: int = 50) -> list[dict[str, Any]]:
        if not ids:
            return []
        with self.driver.session(database=self.settings.neo4j_database) as session:
            return [r.data() for r in session.run(CONTINUING_BY_IDS_QUERY, ids=ids, limit=limit)]

    def find_containers(self, nodes: list[dict[str, str]]) -> list[dict[str, Any]]:
        if not nodes:
            return []
        with self.driver.session(database=self.settings.neo4j_database) as session:
            return [r.data() for r in session.run(CONTAINERS_QUERY, nodes=nodes)]

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
