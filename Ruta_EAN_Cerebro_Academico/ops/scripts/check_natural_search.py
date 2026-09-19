from __future__ import annotations

import argparse
import json

from src.config.settings import get_settings
from src.repositories.recommendation_repository import (
    RecommendationRepository,
)
from src.services.recommendation_service import (
    RecommendationService,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Prueba recomendaciones desde lenguaje natural."),
    )
    parser.add_argument(
        "--text",
        required=True,
        help="Lo que el estudiante desea aprender.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Resultados máximos por cada camino.",
    )

    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    settings = get_settings()

    with RecommendationRepository(settings) as repository:
        repository.verify_connectivity()

        service = RecommendationService(repository)

        response = service.recommend(
            arguments.text,
            limit=arguments.limit,
        )

    print(
        json.dumps(
            response,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )

    print()
    print("Prueba de lenguaje natural: OK")


if __name__ == "__main__":
    main()
