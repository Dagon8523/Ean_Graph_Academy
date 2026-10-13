"""Read-only diagnosis. No properties or credentials are printed."""
import json
from neo4j import GraphDatabase, READ_ACCESS
from src.services.conversation_model import ConversationSettings


def main():
    s = ConversationSettings()
    with GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user,
                               s.neo4j_password.get_secret_value())) as driver:
        with driver.session(database=s.neo4j_database, default_access_mode=READ_ACCESS) as session:
            for title, query in (
                ('labels', 'CALL db.labels() YIELD label RETURN label ORDER BY label'),
                ('oferta_chat', 'MATCH (o:OfertaLaboral) RETURN count(o) AS total'),
                ('indexes', 'SHOW INDEXES YIELD name, state RETURN name, state'),
            ):
                print(title, json.dumps(session.run(query).data(), ensure_ascii=False))


if __name__ == '__main__':
    main()
