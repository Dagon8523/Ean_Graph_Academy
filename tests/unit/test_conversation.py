from uuid import uuid4
from unittest.mock import Mock

import pytest

from apps.api.src.schemas.conversation import ConversationRequest, Extraction, Reply
from src.services.conversation_service import ConversationService, SessionStore, SessionMissing, SessionBusy
from src.services.conversation_model import ModelUnavailable
from ops.scripts.import_conversation_jobs import rows_from


def setup_service(changes, text='Gracias. ¿Qué estudios tienes?'):
    model = Mock()
    model.generate.side_effect = [Extraction(changes=changes), Reply(text=text)]
    academic, jobs = Mock(), Mock()
    academic.recommend.return_value = {'programas_directos': {'resultados': []}}
    jobs.search.return_value = ([], 'NOT_LOADED')
    store = SessionStore()
    return ConversationService(model, academic, jobs, store), model, academic, jobs


def change(field, value, evidence):
    return {'field': field, 'value': value, 'evidence': evidence}


def test_greeting_does_not_search_or_invent_profile():
    service, _, academic, jobs = setup_service([])
    result = service.chat(ConversationRequest(message='Hola'))
    assert result['profile'].learning_goal is None
    academic.recommend.assert_not_called()
    jobs.search.assert_not_called()


def test_context_correction_and_refusal_across_turns():
    service, model, academic, _ = setup_service([
        change('learning_goal', 'analítica de datos', 'analítica de datos'),
        change('age', '25', '25 años'),
    ])
    result = service.chat(ConversationRequest(message='Quiero analítica de datos y tengo 25 años'))
    identifier = result['conversation_id']
    model.generate.side_effect = [Extraction(changes=[change('age', '26', '26')]), Reply(text='Gracias')]
    result = service.chat(ConversationRequest(message='Corrijo: tengo 26', conversation_id=identifier))
    assert result['profile'].age == 26
    assert result['profile'].learning_goal == 'analítica de datos'
    model.generate.side_effect = [Extraction(changes=[change('age', None, 'no compartir mi edad')]), Reply(text='Está bien')]
    result = service.chat(ConversationRequest(message='Prefiero no compartir mi edad', conversation_id=identifier))
    assert result['profile'].age is None and 'age' in result['skipped_fields']
    assert academic.recommend.call_count == 1


def test_no_evidence_and_invalid_age_are_rejected():
    service, _, _, _ = setup_service([
        change('learning_goal', 'medicina', 'quiero medicina'),
        change('age', '999', '999'),
    ])
    result = service.chat(ConversationRequest(message='999'))
    assert result['profile'].age is None and result['profile'].learning_goal is None
    assert len(result['notices']) == 2


def test_failure_does_not_commit_profile_or_history():
    service, model, _, _ = setup_service([])
    result = service.chat(ConversationRequest(message='Hola'))
    identifier = result['conversation_id']
    model.generate.side_effect = [Extraction(changes=[change('education', 'técnico', 'técnico')]), ModelUnavailable()]
    with pytest.raises(ModelUnavailable):
        service.chat(ConversationRequest(message='Soy técnico', conversation_id=identifier))
    session = service.store.sessions[identifier]
    assert session.profile.education is None and len(session.history) == 2
    assert not session.lock.locked()


def test_sessions_are_isolated_expire_and_can_be_deleted():
    store = SessionStore(ttl=60, maximum=2)
    first, a = store.acquire(None)
    with pytest.raises(SessionBusy):
        store.acquire(first)
    a.lock.release()
    second, b = store.acquire(None)
    b.lock.release()
    assert a is not b
    with pytest.raises(SessionBusy):
        store.acquire(None)
    a.touched -= 61
    with pytest.raises(SessionMissing):
        store.acquire(first)
    store.delete(second)
    with pytest.raises(SessionMissing):
        store.acquire(uuid4())


def test_jobs_failure_is_not_reported_as_empty():
    service, _, _, jobs = setup_service([change('learning_goal', 'datos', 'datos')])
    jobs.search.side_effect = RuntimeError('secret')
    result = service.chat(ConversationRequest(message='datos'))
    assert result['jobs_status'] == 'UNAVAILABLE'
    assert 'secret' not in str(result)


def test_import_skips_conflicts_and_marks_unverified():
    source = {'ofertas': [
        {'oferta_id': '1', 'valores_fuente': {'TITULO': ['Analista'], 'CARGO': ['BI']}, 'habilidades': []},
        {'oferta_id': '2', 'requiere_revision': True},
        {'oferta_id': '3', 'valores_fuente': {'TITULO': ['A', 'B']}},
    ]}
    rows, skipped = rows_from(source)
    assert len(rows) == 1 and skipped == 2
    assert rows[0]['titulo'] == 'Analista' and rows[0]['vigencia'] == 'NO_VERIFICADA'


def test_provider_contracts_and_safe_errors(monkeypatch):
    import httpx
    from src.services.conversation_model import ConversationSettings, ConversationModel
    settings = ConversationSettings(_env_file=None, neo4j_password='test', chat_model='test-model')
    real_client = httpx.Client
    bodies = []

    def handler(request):
        import json
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={'message': {'content': '{"changes": []}'}})

    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: real_client(transport=httpx.MockTransport(handler)))
    model = ConversationModel(settings)
    assert model.generate('Extract', {}, Extraction).changes == []
    assert bodies[0]['format'] == Extraction.model_json_schema()
    assert bodies[0]['stream'] is False

    def gemini(request):
        import json
        bodies.append(json.loads(request.content))
        assert request.headers['x-goog-api-key'] == 'private-key'
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': '{"text":"Hola"}'}]}}]})

    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: real_client(transport=httpx.MockTransport(gemini)))
    settings = settings.model_copy(update={'chat_provider': 'gemini'})
    from pydantic import SecretStr
    settings.gemini_api_key = SecretStr('private-key')
    assert ConversationModel(settings).generate('Reply', {}, Reply).text == 'Hola'
    assert bodies[-1]['generationConfig']['responseJsonSchema'] == Reply.model_json_schema()

    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: real_client(transport=httpx.MockTransport(
        lambda request: httpx.Response(429, text='private-key quota exceeded'))))
    with pytest.raises(ModelUnavailable) as error:
        ConversationModel(settings).generate('Reply', {}, Reply)
    assert 'private-key' not in str(error.value)


def test_api_contract_and_expired_session(monkeypatch):
    from fastapi.testclient import TestClient
    from apps.api.src.main import create_app
    from apps.api.src.routes import conversation as route
    from src.services.conversation_model import ConversationSettings
    settings = ConversationSettings(_env_file=None, neo4j_password='test')
    monkeypatch.setattr(route, 'ConversationSettings', lambda: settings)
    academic, jobs, model = Mock(), Mock(), Mock()
    monkeypatch.setattr(route, 'RecommendationRepository', lambda settings: academic)
    monkeypatch.setattr(route, 'JobOfferRepository', lambda settings: jobs)
    monkeypatch.setattr(route, 'ConversationCatalogRepository', lambda settings: Mock())
    monkeypatch.setattr(route, 'ConversationModel', lambda settings: model)
    store = SessionStore()
    monkeypatch.setattr(route, 'get_store', lambda: store)
    model.generate.side_effect = [Extraction(changes=[]), Reply(text='¿Qué te gustaría estudiar?')]
    with TestClient(create_app()) as client:
        response = client.post('/api/v1/conversations/message', json={'message': 'Hola'})
        assert response.status_code == 200
        identifier = response.json()['conversation_id']
        assert response.json()['jobs_status'] == 'NOT_QUERIED'
        assert client.delete(f'/api/v1/conversations/{identifier}').status_code == 204
        response = client.post('/api/v1/conversations/message', json={'message': 'Hola', 'conversation_id': identifier})
        assert response.status_code == 404
        assert client.post('/api/v1/conversations/message', json={'message': ''}).status_code == 422
