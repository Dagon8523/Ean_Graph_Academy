import hashlib
from pathlib import PureWindowsPath

from pydantic import BaseModel, ConfigDict


def normalize_component(value: object) -> str:
    if value is None:
        return ""

    return " ".join(str(value).strip().lower().split())


def extract_filename(file_path: object) -> str:
    if not file_path:
        return ""

    return PureWindowsPath(str(file_path)).name


class UnitStudyRecord(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
    )

    file_path: str | None = None
    folder_breadcrumb: str | None = None
    sheet_name: str | None = None
    sheet_type: str | None = None

    anio: str | None = None
    codigo_plan_estudios: str | None = None
    codigo_unidad_estudio: str | None = None
    tipo_unidad_estudio: str | None = None

    modalidad: str | None = None
    nivel: str | None = None
    programa: str | None = None
    nombre_unidad_estudio: str | None = None

    creditos_academicos: str | None = None
    had: str | None = None
    hta: str | None = None
    ht: str | None = None

    descripcion_unidad: str | None = None
    resultado_aprendizaje_unidad: str | None = None
    contenidos_unidad: str | None = None
    competencia_programa: str | None = None
    estrategias_pedagogicas: str | None = None

    modulo: str | None = None
    ciclo: str | None = None
    semestre: str | None = None
    esquema_calificacion: str | None = None
    porcentaje: str | None = None

    bibliografia_obligatoria: str | None = None
    bibliografia_complementaria: str | None = None
    recursos_tecnologicos: str | None = None
    componente_lengua_extranjera: str | None = None

    @property
    def source_filename(self) -> str:
        return extract_filename(self.file_path)

    @property
    def natural_key(self) -> str:
        components = [
            self.folder_breadcrumb,
            self.source_filename,
            self.sheet_name,
            self.codigo_plan_estudios,
            self.codigo_unidad_estudio,
            self.anio,
        ]

        return "|".join(normalize_component(component) for component in components)

    @property
    def content_fingerprint(self) -> str:
        semantic_fields = [
            self.descripcion_unidad,
            self.resultado_aprendizaje_unidad,
            self.contenidos_unidad,
            self.competencia_programa,
            self.estrategias_pedagogicas,
            self.esquema_calificacion,
            self.bibliografia_obligatoria,
            self.bibliografia_complementaria,
        ]

        normalized_content = "|".join(
            normalize_component(value) for value in semantic_fields
        )

        return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()

    @property
    def unit_id(self) -> str:
        identity = f"{self.natural_key}|{self.content_fingerprint}"

        return hashlib.sha256(identity.encode("utf-8")).hexdigest()

    @property
    def semantic_text(self) -> str:
        fields = [
            self.nombre_unidad_estudio,
            self.descripcion_unidad,
            self.resultado_aprendizaje_unidad,
            self.contenidos_unidad,
            self.competencia_programa,
        ]

        unique_parts: list[str] = []
        seen: set[str] = set()

        for value in fields:
            if not value:
                continue

            normalized = normalize_component(value)

            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_parts.append(value.strip())

        return "\n\n".join(unique_parts)

    def to_neo4j_row(self) -> dict:
        row = self.model_dump(
            exclude_none=True,
        )

        # No almacenar la ruta absoluta del computador.
        row.pop("file_path", None)

        row.update(
            {
                "unidad_id": self.unit_id,
                "llave_natural": self.natural_key,
                "huella_contenido": (self.content_fingerprint),
                "codigo_programa": (self.codigo_plan_estudios),
                "nombre_normalizado": (normalize_component(self.nombre_unidad_estudio)),
                "programa_origen": self.programa,
                "archivo_origen": self.source_filename,
                "carpeta_origen": (self.folder_breadcrumb),
                "hoja_origen": self.sheet_name,
                "tipo_hoja": self.sheet_type,
                "texto_semantico": (self.semantic_text or None),
                "busqueda_semantica_disponible": bool(self.semantic_text),
                "origen": "SYLLABUS_JSON",
            }
        )

        return row
