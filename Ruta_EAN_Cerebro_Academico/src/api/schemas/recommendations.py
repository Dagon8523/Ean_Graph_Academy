from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SearchMode = Literal[
    "ESTRICTA",
    "RELAJADA",
    "AMPLIA",
    "SIN_RESULTADOS",
]


class LearningPathRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    learning_goal: str = Field(
        min_length=3,
        max_length=1000,
        description=("Descripción libre de lo que el estudiante desea aprender."),
        examples=["Quiero aprender inteligencia artificial aplicada a negocios"],
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Resultados máximos por cada catálogo.",
    )


class MatchingUnit(BaseModel):
    unidad_id: str
    nombre: str | None = None


class ContinuingEducationResult(BaseModel):
    formacion_id: str
    nombre: str | None = None
    score: float
    eventos_vigentes: int
    proxima_fecha: str | None = None
    ultima_fecha: str | None = None
    disponibilidad: Literal[
        "VIGENTE",
        "PROXIMA",
        "SIN_OFERTA_DISPONIBLE",
    ]


class OfficialProgramResult(BaseModel):
    programa_id: str
    snies_codigo: str | None = None
    descripcion_abreviada: str | None = None
    distincion_genero: str | None = None
    estado: str | None = None
    modalidad: str | None = None
    nivel_formacion: str | None = None
    score: float
    origen: Literal[
        "COINCIDENCIA_DIRECTA",
        "COINCIDENCIA_POR_UNIDAD",
    ]
    unidades_coincidentes: list[MatchingUnit] = Field(default_factory=list)


class ContinuingEducationSection(BaseModel):
    modo_busqueda: SearchMode
    total: int
    resultados: list[ContinuingEducationResult]


class OfficialProgramsSection(BaseModel):
    modo_busqueda: SearchMode
    total: int
    resultados: list[OfficialProgramResult]


class LearningPathResponse(BaseModel):
    entrada: str
    palabras_clave: list[str]
    consulta_estricta: str
    consulta_relajada: str
    consulta_amplia: str
    educacion_continuada: ContinuingEducationSection
    programas_directos: OfficialProgramsSection
    programas_por_unidades: OfficialProgramsSection


class HealthResponse(BaseModel):
    status: Literal["ok"]
    neo4j: Literal["connected"]
