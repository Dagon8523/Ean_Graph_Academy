from __future__ import annotations

from collections.abc import Iterator

from src.config.settings import get_settings
from src.repositories.recommendation_repository import (
    RecommendationRepository,
)
from src.services.recommendation_service import (
    RecommendationService,
)


def get_recommendation_service() -> Iterator[RecommendationService]:
    settings = get_settings()
    repository = RecommendationRepository(settings)

    try:
        yield RecommendationService(repository)
    finally:
        repository.close()
