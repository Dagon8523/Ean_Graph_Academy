"""Crea el índice de búsqueda EAN X sin modificar los índices existentes."""
from neo4j import GraphDatabase
from src.config.settings import get_settings


def main():
    settings = get_settings()
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user,
                              settings.neo4j_password.get_secret_value())) as driver:
        with driver.session(database=settings.neo4j_database) as session:
            session.run("""
                CREATE FULLTEXT INDEX eanx_busqueda_fulltext_idx IF NOT EXISTS
                FOR (n:FormacionEANX|ModuloEANX)
                ON EACH [n.titulo, n.nombre, n.descripcion, n.embedding_text]
            """).consume()
            session.run("CALL db.awaitIndexes(300)").consume()
            print("Índice EAN X: listo")


if __name__ == "__main__":
    main()
