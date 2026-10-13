from pathlib import Path

from neo4j import GraphDatabase

from src.config.settings import get_settings

SCHEMA_PATH = Path("ops/schema/schema.cypher")


def load_statements() -> list[str]:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No existe el archivo de schema: {SCHEMA_PATH}")

    content = SCHEMA_PATH.read_text(encoding="utf-8")

    statements: list[str] = []

    for chunk in content.split(";"):
        lines = []

        for line in chunk.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("//"):
                continue

            lines.append(line)

        statement = "\n".join(lines).strip()

        if statement:
            statements.append(statement)

    return statements


def main() -> None:
    settings = get_settings()

    print("=" * 60)
    print("RUTA EAN - INICIALIZACIÓN SCHEMA NEO4J")
    print("=" * 60)
    print(f"URI: {settings.neo4j_uri}")
    print(f"Database: {settings.neo4j_database}")
    print(f"Schema: {SCHEMA_PATH}")
    print()

    statements = load_statements()

    print(f"Sentencias encontradas: {len(statements)}")
    print()

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(
            settings.neo4j_user,
            settings.neo4j_password.get_secret_value(),
        ),
    )

    try:
        driver.verify_connectivity()
        print("Conexión Neo4j: OK")
        print()

        with driver.session(database=settings.neo4j_database) as session:
            for position, statement in enumerate(
                statements,
                start=1,
            ):
                first_line = statement.splitlines()[0]

                print(f"[{position}/{len(statements)}] {first_line[:80]}")

                session.run(statement).consume()

        print()
        print("Schema aplicado correctamente.")

        with driver.session(database=settings.neo4j_database) as session:
            constraints = list(
                session.run(
                    """
                    SHOW CONSTRAINTS
                    YIELD name, type, labelsOrTypes, properties
                    RETURN
                        name,
                        type,
                        labelsOrTypes,
                        properties
                    ORDER BY name
                    """
                )
            )

            indexes = list(
                session.run(
                    """
                    SHOW INDEXES
                    YIELD
                        name,
                        type,
                        entityType,
                        labelsOrTypes,
                        properties,
                        state
                    RETURN
                        name,
                        type,
                        entityType,
                        labelsOrTypes,
                        properties,
                        state
                    ORDER BY name
                    """
                )
            )

        print()
        print("=" * 60)
        print("CONSTRAINTS")
        print("=" * 60)

        for row in constraints:
            print(f"{row['name']} | {row['labelsOrTypes']} | {row['properties']}")

        print()
        print(f"Total constraints: {len(constraints)}")

        print()
        print("=" * 60)
        print("INDEXES")
        print("=" * 60)

        for row in indexes:
            print(
                f"{row['name']} | "
                f"{row['type']} | "
                f"{row['labelsOrTypes']} | "
                f"{row['properties']} | "
                f"{row['state']}"
            )

        print()
        print(f"Total indexes: {len(indexes)}")

        print()
        print("=" * 60)
        print("SCHEMA NEO4J: OK")
        print("=" * 60)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
