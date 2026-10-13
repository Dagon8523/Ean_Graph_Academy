import unittest

from src.services.recommendation_service import RecommendationService, compact_paths
from src.repositories.recommendation_repository import (
    CONTINUING_BY_IDS_QUERY, SEMANTIC_PATHS_QUERY, SEARCH_PROGRAMS_BY_UNITS_QUERY,
)
from apps.api.src.schemas.academic_path import LearningPathResponse


class FakeRepository:
    def __init__(self, connected=True):
        self.connected = connected
        self.seeds = []

    def search_continuing_education(self, query, limit):
        return []

    def search_official_programs(self, query, limit):
        return []

    def search_programs_by_units(self, query, limit):
        return []

    def search_units(self, query, limit):
        return [{"unidad_id": "u1", "nombre": "Java", "score": 1.0,
                 "programas": [], "estado_programa": "pendiente_revision"}]

    def search_programs_for_units(self, units, limit):
        return []

    def search_eanx(self, query, limit):
        return [{"tipo": "FormacionEANX", "id": "x1", "nombre": "Java", "score": 1.0}]

    def find_semantic_paths(self, seeds, limit):
        self.seeds = seeds
        if not self.connected:
            return []
        return [{"origen": {"tipo": "UnidadEstudio", "id": "u1"}, "saltos": 1,
                 "nodos": [{"tipo": "UnidadEstudio", "id": "u1"},
                           {"tipo": "Formacion", "id": "f1"}],
                 "conexiones": [{"validada": True, "naturaleza": "afinidad_tematica"}]}]

    def get_continuing_education_by_ids(self, ids, limit):
        return [{"formacion_id": identifier, "disponibilidad": "SIN_OFERTA_DISPONIBLE"}
                for identifier in ids]

    def find_containers(self, nodes):
        return []


class AcademicPathTests(unittest.TestCase):
    def test_related_offer_and_orphan_unit_remain_explicit(self):
        repo = FakeRepository()
        response = RecommendationService(repo).recommend("Quiero aprender Java")
        self.assertEqual(response["eanx"]["total"], 1)
        self.assertEqual(response["ruta_academica"]["unidades_sin_programa"], ["u1"])
        self.assertEqual(response["ruta_academica"]["ofertas_continuada_relacionadas"][0]
                         ["disponibilidad"], "SIN_OFERTA_DISPONIBLE")
        self.assertIn({"tipo": "FormacionEANX", "id": "x1"}, repo.seeds)
        self.assertEqual(response["ruta_academica"]["estado"], "EXPLORATORIA")

    def test_no_connection_is_not_fabricated(self):
        response = RecommendationService(FakeRepository(False)).recommend("Java")
        self.assertEqual(response["ruta_academica"]["recorridos"], [])
        self.assertEqual(response["ruta_academica"]["ofertas_continuada_relacionadas"], [])

    def test_mirrored_paths_count_as_one_connection(self):
        path = FakeRepository().find_semantic_paths([], 5)[0]
        reverse = {**path, "origen": {"tipo": "Formacion", "id": "f1"},
                   "nodos": list(reversed(path["nodos"]))}
        rows, count = compact_paths([path, reverse, path])
        self.assertEqual(len(rows), 1)
        self.assertEqual(count, 1)
        self.assertEqual(len(rows[0]["origenes_consulta"]), 2)

    def test_response_keeps_legacy_fields_and_new_sections(self):
        result = RecommendationService(FakeRepository()).recommend("Java")
        response = LearningPathResponse.model_validate(result)
        self.assertEqual(response.entrada, "Java")
        self.assertEqual(response.eanx.total, 1)
        self.assertEqual(response.programas_directos.total, 0)
        self.assertEqual(response.ruta_academica.total_conexiones_recuperadas, 1)

    def test_short_academic_acronyms_and_invalid_input(self):
        self.assertIn("ia", RecommendationService.extract_keywords("Quiero aprender IA"))
        self.assertIn("bi", RecommendationService.extract_keywords("Quiero aprender BI"))
        with self.assertRaises(ValueError):
            RecommendationService(FakeRepository()).recommend(" ")

    def test_only_current_reviewed_semantic_links_are_queried(self):
        for fragment in ("r.validada = true", "academic_similarity_v25_hybrid",
                         "startNode(r).embedding_text_hash", "endNode(r).embedding_text_hash",
                         "requiere_revision_contenido"):
            self.assertIn(fragment, SEMANTIC_PATHS_QUERY)
        self.assertIn("program.codigo_snies AS snies_codigo", SEARCH_PROGRAMS_BY_UNITS_QUERY)
        self.assertNotIn("db.index.fulltext.queryNodes", CONTINUING_BY_IDS_QUERY)
        self.assertIn("node.formacion_id IN $ids", CONTINUING_BY_IDS_QUERY)


if __name__ == '__main__':
    unittest.main()
