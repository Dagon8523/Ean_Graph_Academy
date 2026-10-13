from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SapProgramRecord(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        str_strip_whitespace=True,
    )

    cost_center: str | None = Field(default=None, alias="_0COSTCENTER")
    program_variant: str | None = Field(default=None, alias="HE_PRGDMA")
    program_id: str = Field(alias="HE_PRGRM")
    program_code: str | None = Field(default=None, alias="HE_PRGRMT")
    program_unit: str | None = Field(default=None, alias="HE_PRGUND")
    program_type: str | None = Field(default=None, alias="HE_PRTYPE")
    location: str | None = Field(default=None, alias="HE_UBICA")

    snies_code: str | None = Field(default=None, alias="SNIES_CODIGO")
    snies_short_description: str | None = Field(
        default=None,
        alias="SNIES_DESCRIPCION_ABREVIADA",
    )
    snies_gender_distinction: str | None = Field(
        default=None,
        alias="SNIES_DISTINCION_GENERO",
    )
    snies_status: str | None = Field(default=None, alias="SNIES_ESTADO")
    snies_faculty: str | None = Field(default=None, alias="SNIES_FACULTAD")
    snies_approval_date: str | None = Field(
        default=None,
        alias="SNIES_FECHA_APROBACION_RC",
    )
    snies_rnrc_validity_years: float | None = Field(
        default=None,
        alias="SNIES_RNRC_VIGENCIA_ANOS",
    )
    snies_ac_validity_years: float | None = Field(
        default=None,
        alias="SNIES_AC_VIGENCIA_ANOS",
    )
    snies_modality: str | None = Field(default=None, alias="SNIES_MODALIDAD")
    snies_education_level: str | None = Field(
        default=None,
        alias="SNIES_NIVEL_FORMACION",
    )
    snies_school: str | None = Field(default=None, alias="SNIES_SCHOOL")
    snies_program_type: str | None = Field(
        default=None,
        alias="SNIES_TIPO_PROGRAMA",
    )
    snies_global_program_type: str | None = Field(
        default=None,
        alias="SNIES_TIPO_PROGRAMA_GLOBAL",
    )

    intensity: float | None = Field(default=None, alias="ZZ_INTESIAD")
    minimum_credits: float | None = Field(default=None, alias="HE_CREMIN")
    maximum_credits: float | None = Field(default=None, alias="HE_CREMAX")
    optimal_credits: float | None = Field(
        default=None,
        alias="SNIES_CREDITOS_OPTIMOS",
    )
    maximum_snies_credits: float | None = Field(
        default=None,
        alias="SNIES_CREDITOS_MAXIMOS",
    )
    study_duration: float | None = Field(
        default=None,
        alias="SNIES_DURACION_ESTUDIOS",
    )
    counter: int | None = Field(default=None, alias="contador")

    @field_validator(
        "program_variant",
        "program_id",
        "program_code",
        "program_unit",
        "program_type",
        "snies_code",
        mode="before",
    )
    @classmethod
    def preserve_identifiers(cls, value: Any) -> str | None:
        if value is None:
            return None

        text = str(value).strip()
        return text or None

    @property
    def semantic_text(self) -> str:
        """
        Texto permitido para la búsqueda semántica directa de programas.

        Solo utiliza:
        - SNIES_DESCRIPCION_ABREVIADA
        - SNIES_DISTINCION_GENERO
        """
        parts = [
            self.snies_short_description,
            self.snies_gender_distinction,
        ]

        return " ".join(part for part in parts if part).strip()
