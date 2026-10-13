from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from apps.api.src.dependencies import get_recommendation_service
from apps.api.src.schemas.recommendations import (
    HealthResponse,
    LearningPathRequest,
)
from apps.api.src.schemas.academic_path import LearningPathResponse
from src.config.settings import get_settings
from src.repositories.recommendation_repository import (
    RecommendationRepository,
)
from src.services.recommendation_service import (
    RecommendationService,
)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
)
def health_check() -> HealthResponse:
    settings = get_settings()

    try:
        with RecommendationRepository(settings) as repository:
            repository.verify_connectivity()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j no está disponible",
        ) from error

    return HealthResponse(
        status="ok",
        neo4j="connected",
    )


@router.post(
    "/api/v1/recommendations/learning-path",
    response_model=LearningPathResponse,
    tags=["Ruta EAN"],
    summary="Construir una ruta formativa inicial",
)
def recommend_learning_path(
    request: LearningPathRequest,
    service: Annotated[
        RecommendationService,
        Depends(get_recommendation_service),
    ],
) -> LearningPathResponse:
    try:
        result = service.recommend(
            request.learning_goal,
            limit=request.limit,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except (Neo4jError, ServiceUnavailable) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible consultar el catálogo académico. Verifica Neo4j y sus índices.",
        ) from error

    return LearningPathResponse.model_validate(result)
