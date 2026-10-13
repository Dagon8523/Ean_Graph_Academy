"""Browse the official catalog using registered modality and level, not topic alone."""
from neo4j import GraphDatabase, READ_ACCESS

QUERY = '''
MATCH (p:ProgramaOficial)
OPTIONAL MATCH (p)-[:TIENE_MODALIDAD]->(m:Modalidad)
OPTIONAL MATCH (p)-[:TIENE_NIVEL]->(n:NivelFormacion)
WITH p, coalesce(p.modalidad, m.nombre, '') AS modalidad,
        coalesce(p.nivel_formacion, n.nombre, '') AS nivel
WHERE ($modality = '' OR toLower(modalidad) CONTAINS $modality)
  AND ($level = '' OR
       ($level = 'pregrado' AND toLower(nivel) =~ '.*(pregrado|universitari|profesional|tecn[oó]log|t[eé]cnic).*'
         AND NOT toLower(nivel) =~ '.*(especial|maestr|doctor|posgrado).*') OR
       ($level = 'posgrado' AND toLower(nivel) =~ '.*(posgrado|especial|maestr|doctor).*'))
RETURN DISTINCT p.programa_id AS programa_id, p.codigo_snies AS snies_codigo,
       p.snies_descripcion_abreviada AS descripcion_abreviada,
       p.snies_distincion_genero AS distincion_genero,
       p.estado AS estado, modalidad, nivel AS nivel_formacion,
       'FILTROS_DE_CATALOGO' AS origen
ORDER BY descripcion_abreviada, programa_id
LIMIT $limit
'''


class ConversationCatalogRepository:
    def __init__(self, settings):
        self.settings = settings
        self.driver = GraphDatabase.driver(settings.neo4j_uri, auth=(
            settings.neo4j_user, settings.neo4j_password.get_secret_value()))

    def browse(self, modality='', level='', limit=8):
        with self.driver.session(database=self.settings.neo4j_database,
                                 default_access_mode=READ_ACCESS) as session:
            rows = session.run(QUERY, modality=modality, level=level, limit=limit).data()
        unique = {}
        for row in rows:
            key = (row.get('snies_codigo'), row.get('descripcion_abreviada'),
                   row.get('modalidad'), row.get('nivel_formacion'))
            unique.setdefault(key, row)
        return list(unique.values())

    def close(self):
        self.driver.close()
