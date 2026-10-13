"""Extiende el contrato existente conservando sus campos públicos."""
from typing import Any, Literal

from pydantic import BaseModel, Field
from apps.api.src.schemas.recommendations import LearningPathResponse as BaseLearningPathResponse


class AcademicSection(BaseModel):
    modo_busqueda: str
    total: int
    resultados: list[dict[str, Any]]


class AcademicPath(BaseModel):
    estado: Literal["EXPLORATORIA"] = "EXPLORATORIA"
    total_conexiones_recuperadas: int
    recorridos: list[dict[str, Any]]
    relaciones_estructurales: list[dict[str, Any]]
    ofertas_continuada_relacionadas: list[dict[str, Any]]
    unidades_sin_programa: list[str]
    observaciones: list[str] = Field(default_factory=list)


class LearningPathResponse(BaseLearningPathResponse):
    consulta_tolerante: str
    unidades_estudio: AcademicSection
    eanx: AcademicSection
    ruta_academica: AcademicPath
