from __future__ import annotations

import argparse
import json

from src.config.settings import get_settings
from src.repositories.recommendation_repository import (
    RecommendationRepository,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prueba la búsqueda unificada de Ruta EAN.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Consulta compatible con el índice full-text.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Resultados máximos por cada camino.",
    )

    return parser


def print_section(
    title: str,
    rows: list[dict],
) -> None:
    print()
    print(f"=== {title} ===")
    print(f"Resultados: {len(rows)}")

    print(
        json.dumps(
            rows,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


def main() -> None:
    arguments = build_parser().parse_args()
    settings = get_settings()

    with RecommendationRepository(settings) as repository:
        repository.verify_connectivity()

        continuing_education = repository.search_continuing_education(
            arguments.query,
            limit=arguments.limit,
        )
        direct_programs = repository.search_official_programs(
            arguments.query,
            limit=arguments.limit,
        )
        programs_by_units = repository.search_programs_by_units(
            arguments.query,
            limit=arguments.limit,
        )

    print_section(
        "EDUCACIÓN CONTINUADA",
        continuing_education,
    )
    print_section(
        "PROGRAMAS — COINCIDENCIA DIRECTA",
        direct_programs,
    )
    print_section(
        "PROGRAMAS — COINCIDENCIA POR UNIDAD",
        programs_by_units,
    )

    print()
    print("Prueba de búsqueda unificada: OK")


if __name__ == "__main__":
    main()
