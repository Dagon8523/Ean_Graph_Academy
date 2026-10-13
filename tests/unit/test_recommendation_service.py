from unittest.mock import Mock

import pytest

from src.services.recommendation_service import RecommendationService


def test_extract_keywords_removes_stopwords_and_duplicates() -> None:
    result = RecommendationService.extract_keywords(
        "Quiero aprender inteligencia artificial para inteligencia de negocios"
    )

    assert result == [
        "inteligencia",
        "artificial",
        "negocios",
    ]


def test_build_query_with_and_operator() -> None:
    result = RecommendationService.build_query(
        ["inteligencia", "artificial"],
        operator="AND",
    )

    assert result == "inteligencia AND artificial"


def test_build_query_with_or_operator() -> None:
    result = RecommendationService.build_query(
        ["inteligencia", "artificial"],
        operator="OR",
    )

    assert result == "inteligencia OR artificial"


def test_build_query_rejects_invalid_operator() -> None:
    with pytest.raises(
        ValueError,
        match="El operador debe ser AND u OR",
    ):
        RecommendationService.build_query(
            ["inteligencia", "artificial"],
            operator="NOT",
        )


def test_build_tolerant_query() -> None:
    result = RecommendationService.build_tolerant_query(
        ["adminitracion", "empresas"],
    )

    assert result == "adminitracion~1 AND empresas~1"


def test_build_tolerant_query_preserves_short_keywords() -> None:
    result = RecommendationService.build_tolerant_query(
        ["big", "data", "cloud"],
    )

    assert result == "big AND data AND cloud~1"


def test_build_relaxed_query() -> None:
    result = RecommendationService.build_relaxed_query(
        [
            "ingeniería",
            "aplicada",
            "procesos",
        ]
    )

    assert result == (
        "(ingeniería AND aplicada) OR "
        "(ingeniería AND procesos) OR "
        "(aplicada AND procesos)"
    )


def test_build_relaxed_query_requires_three_keywords() -> None:
    result = RecommendationService.build_relaxed_query(["inteligencia", "artificial"])

    assert result == ""


def test_recommend_uses_progressive_fallback() -> None:
    repository = Mock()

    repository.search_continuing_education.side_effect = [
        [],
        [],
        [{"formacion_id": "07000001"}],
    ]
    repository.search_official_programs.side_effect = [
        [],
        [],
        [],
        [{"programa_id": "02000001"}],
    ]
    repository.search_programs_by_units.side_effect = [
        [{"programa_id": "02000002"}],
    ]

    service = RecommendationService(repository)

    result = service.recommend(
        "Ingeniería aplicada a procesos",
        limit=5,
    )

    assert result["educacion_continuada"]["modo_busqueda"] == "RELAJADA"
    assert result["programas_directos"]["modo_busqueda"] == "AMPLIA"
    assert result["programas_por_unidades"]["modo_busqueda"] == "ESTRICTA"

    assert result["educacion_continuada"]["total"] == 1
    assert result["programas_directos"]["total"] == 1
    assert result["programas_por_unidades"]["total"] == 1

    assert result["consulta_estricta"] == ("ingeniería AND aplicada AND procesos")
    assert result["consulta_tolerante"] == (
        "ingeniería~1 AND aplicada~1 AND procesos~1"
    )
    assert result["consulta_relajada"] == (
        "(ingeniería AND aplicada) OR "
        "(ingeniería AND procesos) OR "
        "(aplicada AND procesos)"
    )
    assert result["consulta_amplia"] == ("ingeniería OR aplicada OR procesos")


def test_recommend_uses_tolerant_search_for_typographical_error() -> None:
    repository = Mock()

    repository.search_continuing_education.side_effect = [
        [],
        [{"formacion_id": "07000515"}],
    ]
    repository.search_official_programs.side_effect = [
        [],
        [{"programa_id": "02000010"}],
    ]
    repository.search_programs_by_units.side_effect = [
        [],
        [{"programa_id": "02001264"}],
    ]

    service = RecommendationService(repository)

    result = service.recommend(
        "Quiero aprender adminitracion de empresas",
        limit=10,
    )

    assert result["palabras_clave"] == [
        "adminitracion",
        "empresas",
    ]
    assert result["consulta_estricta"] == ("adminitracion AND empresas")
    assert result["consulta_tolerante"] == ("adminitracion~1 AND empresas~1")

    assert result["educacion_continuada"]["modo_busqueda"] == "TOLERANTE"
    assert result["programas_directos"]["modo_busqueda"] == "TOLERANTE"
    assert result["programas_por_unidades"]["modo_busqueda"] == "TOLERANTE"


def test_recommend_returns_no_results_after_all_levels() -> None:
    repository = Mock()

    repository.search_continuing_education.return_value = []
    repository.search_official_programs.return_value = []
    repository.search_programs_by_units.return_value = []

    service = RecommendationService(repository)

    result = service.recommend(
        "analítica avanzada",
        limit=5,
    )

    assert result["educacion_continuada"]["modo_busqueda"] == ("SIN_RESULTADOS")
    assert result["programas_directos"]["modo_busqueda"] == ("SIN_RESULTADOS")
    assert result["programas_por_unidades"]["modo_busqueda"] == ("SIN_RESULTADOS")

    assert result["educacion_continuada"]["total"] == 0
    assert result["programas_directos"]["total"] == 0
    assert result["programas_por_unidades"]["total"] == 0


def test_recommend_rejects_empty_text() -> None:
    repository = Mock()
    service = RecommendationService(repository)

    with pytest.raises(
        ValueError,
        match="no puede estar vacío",
    ):
        service.recommend("   ")


def test_recommend_rejects_text_without_useful_keywords() -> None:
    repository = Mock()
    service = RecommendationService(repository)

    with pytest.raises(
        ValueError,
        match="No se encontraron términos útiles",
    ):
        service.recommend("Quiero aprender de un programa")


@pytest.mark.parametrize(
    "limit",
    [0, 51],
)
def test_recommend_rejects_invalid_limit(
    limit: int,
) -> None:
    repository = Mock()
    service = RecommendationService(repository)

    with pytest.raises(
        ValueError,
        match="El límite debe estar entre 1 y 50",
    ):
        service.recommend(
            "inteligencia artificial",
            limit=limit,
        )
