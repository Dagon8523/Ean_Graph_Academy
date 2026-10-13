"""Read-only repository for the explicitly documented OfertaLaboral schema."""
from neo4j import GraphDatabase, READ_ACCESS

COUNT = 'MATCH (o:OfertaLaboral) RETURN count(o) AS total'
SEARCH = '''
MATCH (o:OfertaLaboral)
WHERE coalesce(o.requiere_revision, false) = false
WITH o, toLower(coalesce(o.titulo, '') + ' ' + coalesce(o.cargo, '') + ' ' +
     coalesce(o.detalle, '') + ' ' + coalesce(o.texto_busqueda, '')) AS texto
WITH o, size([term IN $terms WHERE texto CONTAINS term]) AS coincidencias
WHERE coincidencias > 0
RETURN o.oferta_id AS oferta_id, o.titulo AS titulo, o.cargo AS cargo,
       o.empresa AS empresa, o.ciudad AS ciudad, o.experiencia AS experiencia,
       o.educacion AS educacion, o.salario AS salario, o.fecha AS fecha,
       coalesce(o.vigencia, 'NO_VERIFICADA') AS vigencia,
       o.fuente AS fuente, coincidencias
ORDER BY coincidencias DESC, oferta_id
LIMIT $limit
'''


class JobOfferRepository:
    def __init__(self, settings):
        self.settings = settings
        self.driver = GraphDatabase.driver(settings.neo4j_uri, auth=(
            settings.neo4j_user, settings.neo4j_password.get_secret_value()))

    def search(self, terms, limit=5):
        with self.driver.session(database=self.settings.neo4j_database,
                                 default_access_mode=READ_ACCESS) as session:
            count = session.run(COUNT).single()['total']
            if not count:
                return [], 'NOT_LOADED'
            rows = session.run(SEARCH, terms=terms, limit=limit).data()
        return rows, 'AVAILABLE' if rows else 'NO_MATCHES'

    def close(self):
        self.driver.close()
