"""Modelos del contrato OData de eventos de formación de SAP Datasphere."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SapEventRecord(BaseModel):
    """Representa un evento recibido desde SAP Datasphere mediante OData."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    # ============================================================
    # 1. Evento
    # ============================================================

    event_id: str = Field(alias="EVENTO_ID")

    event_object_type: str | None = Field(
        default=None,
        alias="EVENTO_TIPO_OBJETO",
    )

    event_short_code: str | None = Field(
        default=None,
        alias="EVENTO_CODIGO_CORTO",
    )

    event_name: str | None = Field(
        default=None,
        alias="EVENTO_NOMBRE",
    )

    event_start_date: date = Field(
        alias="EVENTO_FECHA_INICIO",
    )

    event_end_date: date = Field(
        alias="EVENTO_FECHA_FIN",
    )

    # ============================================================
    # 2. Grupo de formación
    # ============================================================

    training_group_id: str | None = Field(
        default=None,
        alias="GRUPO_FORMACION_ID",
    )

    training_group_short_name: str | None = Field(
        default=None,
        alias="GRUPO_FORMACION_NOMBRE_CORTO",
    )

    training_group_name: str | None = Field(
        default=None,
        alias="GRUPO_FORMACION_NOMBRE",
    )

    # ============================================================
    # 3. Formación o curso
    # ============================================================

    training_id: str | None = Field(
        default=None,
        alias="FORMACION_ID",
    )

    training_object_type: str | None = Field(
        default=None,
        alias="FORMACION_TIPO_OBJETO",
    )

    training_short_name: str | None = Field(
        default=None,
        alias="FORMACION_NOMBRE_CORTO",
    )

    training_name: str | None = Field(
        default=None,
        alias="FORMACION_NOMBRE",
    )

    # ============================================================
    # 4. Método de formación
    # ============================================================

    training_method_id: str | None = Field(
        default=None,
        alias="METODO_FORMACION_ID",
    )

    training_method_short_name: str | None = Field(
        default=None,
        alias="METODO_FORMACION_NOMBRE_CORTO",
    )

    training_method_singular_name: str | None = Field(
        default=None,
        alias="METODO_FORMACION_NOMBRE_SINGULAR",
    )

    training_method_name: str | None = Field(
        default=None,
        alias="METODO_FORMACION_NOMBRE",
    )

    # ============================================================
    # 5. Sede
    # ============================================================

    location_id: str | None = Field(
        default=None,
        alias="SEDE_ID",
    )

    location_short_name: str | None = Field(
        default=None,
        alias="SEDE_NOMBRE_CORTO",
    )

    location_name: str | None = Field(
        default=None,
        alias="SEDE_NOMBRE",
    )

    # ============================================================
    # 6. Oferente
    # ============================================================

    provider_id: str | None = Field(
        default=None,
        alias="OFERENTE_ID",
    )

    provider_object_type: str | None = Field(
        default=None,
        alias="OFERENTE_TIPO_OBJETO",
    )

    provider_short_name: str | None = Field(
        default=None,
        alias="OFERENTE_NOMBRE_CORTO",
    )

    provider_name: str | None = Field(
        default=None,
        alias="OFERENTE_NOMBRE",
    )

    provider_process: str | None = Field(
        default=None,
        alias="OFERENTE_PROCESO",
    )

    provider_level_1: str | None = Field(
        default=None,
        alias="OFERENTE_NIVEL_1",
    )

    provider_level_2: str | None = Field(
        default=None,
        alias="OFERENTE_NIVEL_2",
    )

    provider_level_3: str | None = Field(
        default=None,
        alias="OFERENTE_NIVEL_3",
    )

    # ============================================================
    # 7. Facultad
    # ============================================================

    faculty_id: str | None = Field(
        default=None,
        alias="FACULTAD_ID",
    )

    faculty_short_name: str | None = Field(
        default=None,
        alias="FACULTAD_NOMBRE_CORTO",
    )

    faculty_name: str | None = Field(
        default=None,
        alias="FACULTAD_NOMBRE",
    )

    faculty_process: str | None = Field(
        default=None,
        alias="FACULTAD_PROCESO",
    )

    faculty_level_1: str | None = Field(
        default=None,
        alias="FACULTAD_NIVEL_1",
    )

    faculty_level_2: str | None = Field(
        default=None,
        alias="FACULTAD_NIVEL_2",
    )

    faculty_level_3: str | None = Field(
        default=None,
        alias="FACULTAD_NIVEL_3",
    )

    # ============================================================
    # 8. Centro de costos
    # ============================================================

    cost_center_id: str | None = Field(
        default=None,
        alias="CENTRO_COSTOS_ID",
    )

    cost_center_short_name: str | None = Field(
        default=None,
        alias="CENTRO_COSTOS_NOMBRE_CORTO",
    )

    cost_center_medium_name: str | None = Field(
        default=None,
        alias="CENTRO_COSTOS_NOMBRE_MEDIO",
    )

    cost_center_name: str | None = Field(
        default=None,
        alias="CENTRO_COSTOS_NOMBRE",
    )

    cost_center_business_line: str | None = Field(
        default=None,
        alias="CENTRO_COSTOS_LINEA_NEGOCIO",
    )

    cost_center_management: str | None = Field(
        default=None,
        alias="CENTRO_COSTOS_GERENCIA",
    )

    # ============================================================
    # 9. Duración y capacidad
    # ============================================================

    duration_days: int | None = Field(
        default=None,
        alias="DURACION_DIAS",
    )

    duration_hours: Decimal | None = Field(
        default=None,
        alias="DURACION_HORAS",
    )

    minimum_capacity: int | None = Field(
        default=None,
        alias="CAPACIDAD_MINIMA",
    )

    maximum_capacity: int | None = Field(
        default=None,
        alias="CAPACIDAD_MAXIMA",
    )

    optimal_capacity: int | None = Field(
        default=None,
        alias="CAPACIDAD_OPTIMA",
    )

    total_course_network_objects: str | None = Field(
        default=None,
        alias="TOTAL_OBJETOS_CURSO_RED",
    )

    total_learning_network_objects: str | None = Field(
        default=None,
        alias="TOTAL_OBJETOS_APRENDIZAJE_RED",
    )

    # ============================================================
    # 10. Precios y monedas
    # ============================================================

    is_external_code: str | None = Field(
        default=None,
        alias="ES_EXTERNO",
    )

    external_price: Decimal | None = Field(
        default=None,
        alias="PRECIO_EXTERNO",
    )

    external_price_currency: str | None = Field(
        default=None,
        alias="MONEDA_PRECIO_EXTERNO",
    )

    internal_price: Decimal | None = Field(
        default=None,
        alias="PRECIO_INTERNO",
    )

    internal_price_currency: str | None = Field(
        default=None,
        alias="MONEDA_PRECIO_INTERNO",
    )

    cost: Decimal | None = Field(
        default=None,
        alias="COSTO",
    )

    cost_currency: str | None = Field(
        default=None,
        alias="MONEDA_COSTO",
    )

    # ============================================================
    # 11. Publicación, evaluación y estado
    # ============================================================

    assessment_code: str | None = Field(
        default=None,
        alias="PERMITE_EVALUACION",
    )

    published_code: str | None = Field(
        default=None,
        alias="PUBLICADO",
    )

    publication_type: str | None = Field(
        default=None,
        alias="TIPO_PUBLICACION",
    )

    sap_status: str | None = Field(
        default=None,
        alias="ESTADO_SAP",
    )

    deletion_indicator: str | None = Field(
        default=None,
        alias="INDICADOR_ELIMINADO",
    )

    # ============================================================
    # 12. Datos organizacionales
    # ============================================================

    language_code: str | None = Field(
        default=None,
        alias="IDIOMA",
    )

    controlling_area: str | None = Field(
        default=None,
        alias="AREA_CONTROL",
    )

    sector: str | None = Field(
        default=None,
        alias="SECTOR",
    )

    distribution_channel: str | None = Field(
        default=None,
        alias="CANAL_DISTRIBUCION",
    )

    # ============================================================
    # 13. Campos técnicos
    # ============================================================

    follow_up_code: str | None = Field(
        default=None,
        alias="FLUPX",
    )

    total_participations: int | None = Field(
        default=None,
        alias="TOTAL_PARTICIPACIONES",
    )

    # ============================================================
    # Normalización y validaciones
    # ============================================================

    @field_validator("*", mode="before")
    @classmethod
    def normalize_empty_strings(cls, value: Any) -> Any:
        """Convierte cadenas vacías o con espacios en valores nulos."""

        if isinstance(value, str):
            normalized_value = value.strip()
            return normalized_value or None

        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        """Valida que la fecha final no sea anterior a la inicial."""

        if self.event_end_date < self.event_start_date:
            raise ValueError(
                "EVENTO_FECHA_FIN no puede ser anterior a EVENTO_FECHA_INICIO"
            )

        return self

    # ============================================================
    # Propiedades calculadas
    # ============================================================

    @property
    def is_deleted(self) -> bool:
        """Indica si SAP marcó el evento con petición de borrado."""

        return self.deletion_indicator == "X"

    def is_current_on(self, reference_date: date) -> bool:
        """Indica si el evento está vigente y no eliminado."""

        return (
            not self.is_deleted
            and self.event_start_date <= reference_date
            and self.event_end_date >= reference_date
        )

    def is_available_from(self, reference_date: date) -> bool:
        """Indica si el evento está vigente o comenzará después."""

        return not self.is_deleted and self.event_end_date >= reference_date

    @property
    def semantic_text(self) -> str:
        """Construye el texto base para búsqueda y embeddings."""

        candidate_values = [
            self.training_name,
            self.training_short_name,
            self.event_name,
            self.event_short_code,
            self.training_group_name,
            self.training_method_name,
            self.provider_name,
            self.faculty_name,
            self.cost_center_business_line,
            self.cost_center_management,
        ]

        semantic_values: list[str] = []
        normalized_values: set[str] = set()

        for value in candidate_values:
            if value is None:
                continue

            normalized_value = value.casefold()

            if normalized_value in normalized_values:
                continue

            normalized_values.add(normalized_value)
            semantic_values.append(value)

        return " | ".join(semantic_values)


class SapODataPage(BaseModel):
    """Representa una página devuelta por el servicio OData."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    context: str | None = Field(
        default=None,
        alias="@odata.context",
    )
    total_count: int | None = Field(
        default=None,
        alias="@odata.count",
    )

    items: list[SapEventRecord] = Field(
        default_factory=list,
        alias="value",
    )

    next_link: str | None = Field(
        default=None,
        alias="@odata.nextLink",
    )

    @property
    def item_count(self) -> int:
        """Retorna la cantidad de eventos recibidos en la página."""

        return len(self.items)

    @property
    def has_next_page(self) -> bool:
        """Indica si existen más registros después de esta página."""

        if self.next_link:
            return True

        return self.total_count is not None and self.item_count < self.total_count
