from unittest.mock import MagicMock, patch

from src.repositories.program_repository import ProgramRepository


def make_repository() -> tuple[ProgramRepository, MagicMock]:
    settings = MagicMock()
    settings.neo4j_uri = "bolt://localhost:7689"
    settings.neo4j_user = "neo4j"
    settings.neo4j_password.get_secret_value.return_value = "secret"
    settings.neo4j_database = "neo4j"

    driver = MagicMock()

    with patch(
        "src.repositories.program_repository.GraphDatabase.driver",
        return_value=driver,
    ):
        repository = ProgramRepository(settings)

    return repository, driver


def test_upsert_programs_processes_batches() -> None:
    repository, _ = make_repository()

    repository._write_batch = MagicMock(
        side_effect=[2, 1],
    )

    rows = [
        {"programa_id": "1"},
        {"programa_id": "2"},
        {"programa_id": "3"},
    ]

    processed = repository.upsert_programs(
        rows,
        batch_size=2,
    )

    assert processed == 3
    assert repository._write_batch.call_count == 2

    repository._write_batch.assert_any_call(
        [
            {
                "programa_id": "1",
                "modalidad_id": None,
                "nivel_formacion_id": None,
                "tipo_programa_id": None,
            },
            {
                "programa_id": "2",
                "modalidad_id": None,
                "nivel_formacion_id": None,
                "tipo_programa_id": None,
            },
        ]
    )

    repository._write_batch.assert_any_call(
        [
            {
                "programa_id": "3",
                "modalidad_id": None,
                "nivel_formacion_id": None,
                "tipo_programa_id": None,
            },
        ]
    )


def test_prepare_dimension_id_normalizes_text() -> None:
    assert (
        ProgramRepository._normalize_dimension_id(
            "Maestría Presencial",
        )
        == "maestria-presencial"
    )

    assert (
        ProgramRepository._normalize_dimension_id(
            "Presencial - Virtual",
        )
        == "presencial-virtual"
    )

    assert (
        ProgramRepository._normalize_dimension_id(
            "  Especialización  ",
        )
        == "especializacion"
    )


def test_prepare_dimension_id_handles_empty_values() -> None:
    assert ProgramRepository._normalize_dimension_id(None) is None
    assert ProgramRepository._normalize_dimension_id("") is None
    assert ProgramRepository._normalize_dimension_id("   ") is None


def test_prepare_row_adds_dimension_ids() -> None:
    row = {
        "programa_id": "02000001",
        "modalidad": "Presencial",
        "nivel_formacion": "Posgrados",
        "tipo_programa_global": "Maestría",
    }

    prepared = ProgramRepository._prepare_row(row)

    assert prepared["modalidad_id"] == "presencial"
    assert prepared["nivel_formacion_id"] == "posgrados"
    assert prepared["tipo_programa_id"] == "maestria"

    # No modificar el diccionario original.
    assert "modalidad_id" not in row


def test_prepare_row_handles_missing_dimensions() -> None:
    row = {
        "programa_id": "02000002",
        "modalidad": None,
        "nivel_formacion": "",
        "tipo_programa_global": None,
    }

    prepared = ProgramRepository._prepare_row(row)

    assert prepared["modalidad_id"] is None
    assert prepared["nivel_formacion_id"] is None
    assert prepared["tipo_programa_id"] is None
