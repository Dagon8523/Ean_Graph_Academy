from __future__ import annotations

import re
from collections.abc import Callable
from itertools import combinations
from typing import Any

from src.repositories.recommendation_repository import RecommendationRepository

SPANISH_STOPWORDS = {
    "a",
    "al",
    "algo",
    "aprender",
    "como",
    "con",
    "curso",
    "cursos",
    "de",
    "del",
    "el",
    "en",
    "estudiar",
    "formacion",
    "interesa",
    "interesado",
    "la",
    "las",
    "lo",
    "los",
    "me",
    "para",
    "programa",
    "programas",
    "que",
    "quiero",
    "sobre",
    "un",
    "una",
    "y",
}

TOKEN_PATTERN = re.compile(
    r"[a-záéíóúüñ0-9]+",
    flags=re.IGNORECASE,
)

SearchFunction = Callable[..., list[dict[str, Any]]]


def compact_paths(paths: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    groups = {}
    edges = set()
    for path in paths:
        nodes = tuple((n["tipo"], n["id"]) for n in path["nodos"])
        signature = min(nodes, nodes[::-1])
        for a, b in zip(nodes, nodes[1:]):
            edges.add(tuple(sorted((a, b))))
        if signature not in groups:
            groups[signature] = {**path, "origenes_consulta": []}
        source = {**path["origen"], "usa_representante_textual": path.get("usa_representante_textual", False)}
        if source not in groups[signature]["origenes_consulta"]:
            groups[signature]["origenes_consulta"].append(source)
    return list(groups.values()), len(edges)


class RecommendationService:
    def __init__(
        self,
        repository: RecommendationRepository,
    ) -> None:
        self.repository = repository

    def recommend(
        self,
        user_text: str,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        if not user_text.strip():
            raise ValueError("El texto de búsqueda no puede estar vacío")

        if limit < 1 or limit > 50:
            raise ValueError("El límite debe estar entre 1 y 50")

        keywords = self.extract_keywords(user_text)

        if not keywords:
            raise ValueError("No se encontraron términos útiles para buscar")

        strict_query = self.build_query(
            keywords,
            operator="AND",
        )
        tolerant_query = self.build_tolerant_query(keywords)
        relaxed_query = self.build_relaxed_query(keywords)
        broad_query = self.build_query(
            keywords,
            operator="OR",
        )

        continuing_education, continuing_mode = self._search_with_fallback(
            self.repository.search_continuing_education,
            strict_query=strict_query,
            tolerant_query=tolerant_query,
            relaxed_query=relaxed_query,
            broad_query=broad_query,
            limit=limit,
        )

        direct_programs, direct_mode = self._search_with_fallback(
            self.repository.search_official_programs,
            strict_query=strict_query,
            tolerant_query=tolerant_query,
            relaxed_query=relaxed_query,
            broad_query=broad_query,
            limit=limit,
        )

        programs_by_units, units_mode = self._search_with_fallback(
            self.repository.search_programs_by_units,
            strict_query=strict_query,
            tolerant_query=tolerant_query,
            relaxed_query=relaxed_query,
            broad_query=broad_query,
            limit=limit,
        )

        search_args = dict(strict_query=strict_query, tolerant_query=tolerant_query,
                           relaxed_query=relaxed_query, broad_query=broad_query, limit=limit)
        units, unit_search_mode = self._search_with_fallback(self.repository.search_units, **search_args)
        if unit_search_mode in {"ESTRICTA", "TOLERANTE"}:
            programs_by_units = self.repository.search_programs_for_units(units, limit=limit)
            units_mode = unit_search_mode if programs_by_units else "SIN_RESULTADOS"
        eanx, eanx_mode = self._search_with_fallback(self.repository.search_eanx, **search_args)
        seeds = set()
        for tipo, rows, key in (
            ("Formacion", continuing_education, "formacion_id"),
            ("ProgramaOficial", direct_programs + programs_by_units, "programa_id"),
            ("UnidadEstudio", units, "unidad_id"),
        ):
            seeds.update((tipo, row[key]) for row in rows if row.get(key))
        seeds.update((row["tipo"], row["id"]) for row in eanx if row.get("id"))
        for program in programs_by_units:
            seeds.update(("UnidadEstudio", row["unidad_id"])
                         for row in program.get("unidades_coincidentes", []) if row.get("unidad_id"))
        paths = self.repository.find_semantic_paths(
            [{"tipo": tipo, "id": identifier} for tipo, identifier in sorted(seeds)],
            limit=min(limit * 10, 200),
        )
        paths, connection_count = compact_paths(paths)
        related_formations = sorted({node["id"] for path in paths for node in path["nodos"]
                                     if node["tipo"] == "Formacion"})
        related_offers = self.repository.get_continuing_education_by_ids(related_formations, limit=limit)
        context_nodes = seeds | {(n["tipo"], n["id"]) for path in paths for n in path["nodos"]
                                 if n.get("tipo") and n.get("id")}
        containers = self.repository.find_containers(
            [{"tipo": tipo, "id": identifier} for tipo, identifier in sorted(context_nodes)]
        )

        return {
            "entrada": user_text,
            "palabras_clave": keywords,
            "consulta_estricta": strict_query,
            "consulta_tolerante": tolerant_query,
            "consulta_relajada": relaxed_query,
            "consulta_amplia": broad_query,
            "educacion_continuada": {
                "modo_busqueda": continuing_mode,
                "total": len(continuing_education),
                "resultados": continuing_education,
            },
            "programas_directos": {
                "modo_busqueda": direct_mode,
                "total": len(direct_programs),
                "resultados": direct_programs,
            },
            "programas_por_unidades": {
                "modo_busqueda": units_mode,
                "total": len(programs_by_units),
                "resultados": programs_by_units,
            },
            "unidades_estudio": {"modo_busqueda": unit_search_mode, "total": len(units),
                                 "resultados": units},
            "eanx": {"modo_busqueda": eanx_mode, "total": len(eanx), "resultados": eanx},
            "ruta_academica": {
                "estado": "EXPLORATORIA",
                "total_conexiones_recuperadas": connection_count,
                "total_recorridos": len(paths),
                "recorridos": paths,
                "relaciones_estructurales": containers,
                "ofertas_continuada_relacionadas": related_offers,
                "unidades_sin_programa": [row["unidad_id"] for row in units if not row.get("programas")],
                "observaciones": [
                    "Las conexiones expresan afinidad temática; no equivalencia académica.",
                    "La cobertura de conexiones es parcial y no establece un orden de prerrequisitos.",
                ],
            },
        }

    @staticmethod
    def extract_keywords(text: str) -> list[str]:
        tokens = TOKEN_PATTERN.findall(text.lower())

        keywords: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            if len(token) < 3 and token not in {"ia", "bi"}:
                continue

            if token in SPANISH_STOPWORDS:
                continue

            if token in seen:
                continue

            seen.add(token)
            keywords.append(token)

        return keywords[:10]

    @staticmethod
    def build_query(
        keywords: list[str],
        *,
        operator: str,
    ) -> str:
        if operator not in {"AND", "OR"}:
            raise ValueError("El operador debe ser AND u OR")

        return f" {operator} ".join(keywords)

    @staticmethod
    def build_tolerant_query(
        keywords: list[str],
    ) -> str:
        """
        Construye una consulta Lucene tolerante a errores tipográficos.

        Para evitar coincidencias demasiado amplias:
        - Las palabras de cinco o más caracteres permiten una edición.
        - Las palabras cortas se conservan como coincidencia exacta.
        """
        tolerant_keywords = [
            f"{keyword}~1" if len(keyword) >= 5 else keyword for keyword in keywords
        ]

        return " AND ".join(tolerant_keywords)

    @staticmethod
    def build_relaxed_query(
        keywords: list[str],
    ) -> str:
        if len(keywords) < 3:
            return ""

        selected_keywords = keywords[:5]

        pairs = [
            f"({first} AND {second})"
            for first, second in combinations(
                selected_keywords,
                2,
            )
        ]

        return " OR ".join(pairs)

    @staticmethod
    def _search_with_fallback(
        search_function: SearchFunction,
        *,
        strict_query: str,
        tolerant_query: str,
        relaxed_query: str,
        broad_query: str,
        limit: int,
    ) -> tuple[list[dict[str, Any]], str]:
        search_levels = [
            ("ESTRICTA", strict_query),
            ("TOLERANTE", tolerant_query),
            ("RELAJADA", relaxed_query),
            ("AMPLIA", broad_query),
        ]

        executed_queries: set[str] = set()

        for mode, search_query in search_levels:
            if not search_query:
                continue

            if search_query in executed_queries:
                continue

            executed_queries.add(search_query)

            results = search_function(
                search_query,
                limit=limit,
            )

            if results:
                return results, mode

        return [], "SIN_RESULTADOS"
