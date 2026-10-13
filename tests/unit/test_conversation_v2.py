from unittest.mock import Mock

from apps.api.src.schemas.conversation import Extraction, Reply, ConversationRequest
from src.services.conversation_service import ConversationService, SessionStore


def service():
    model, academic, jobs, catalog = Mock(), Mock(), Mock(), Mock()
    academic.recommend.return_value = {'programas_directos': {'resultados': []}}
    jobs.search.return_value = ([], 'NOT_LOADED')
    catalog.browse.return_value = [{'programa_id': 'P1', 'descripcion_abreviada': 'Administración',
                                  'modalidad': 'Virtual', 'nivel_formacion': 'Pregrado'}]
    return ConversationService(model, academic, jobs, SessionStore(), catalog), model, academic, catalog


def turn(s, model, message, changes=None, intent='conversation', identifier=None, reply='¿Qué estudios tienes?'):
    model.generate.side_effect = [Extraction(changes=changes or [], intent=intent), Reply(text=reply)]
    return s.chat(ConversationRequest(message=message, conversation_id=identifier))


def test_virtual_undergraduate_question_overrides_old_goal_and_model_misclassification():
    s, model, academic, catalog = service()
    result = turn(s, model, 'Me interesan finanzas e inglés', [
        {'field': 'learning_goal', 'value': 'finanzas e inglés', 'evidence': 'finanzas e inglés'}])
    result = turn(s, model, 'tienes pregrados irtuales ?', identifier=result['conversation_id'],
                  reply='Encontré Administración en modalidad virtual.')
    assert academic.recommend.call_count == 1
    catalog.browse.assert_called_once_with(modality='virtual', level='pregrado')
    assert result['academic']['programas_directos']['resultados'][0]['programa_id'] == 'P1'
    assert model.generate.call_args.args[1]['proxima_pregunta'] is None


def test_profile_followup_does_not_repeat_cards_or_same_question():
    s, model, academic, _ = service()
    result = turn(s, model, 'Quiero finanzas', [
        {'field': 'learning_goal', 'value': 'finanzas', 'evidence': 'finanzas'}])
    result = turn(s, model, 'Tengo 28 años', [
        {'field': 'age', 'value': '28', 'evidence': '28 años'}], identifier=result['conversation_id'])
    assert result['academic'] is None
    assert academic.recommend.call_count == 1
    assert 'experiencia' in model.generate.call_args.args[1]['proxima_pregunta']


def test_generic_orientation_does_not_query_catalog():
    s, model, academic, catalog = service()
    result = turn(s, model, 'Quiero decidir qué estudiar', [
        {'field': 'learning_goal', 'value': 'decidir qué estudiar', 'evidence': 'decidir qué estudiar'}])
    assert result['profile'].learning_goal is None
    academic.recommend.assert_not_called()
    catalog.browse.assert_not_called()


def test_generated_completed_course_claim_is_removed_when_education_unknown():
    s, model, _, _ = service()
    result = turn(s, model, 'Quiero finanzas', [
        {'field': 'learning_goal', 'value': 'finanzas', 'evidence': 'finanzas'}],
        reply='Veo que ya has tomado cursos en finanzas. ¿Qué estudios tienes?')
    assert 'has tomado' not in result['text']
    assert result['profile'].education is None


def test_next_catalog_turn_keeps_level_and_changes_modality():
    s, model, _, catalog = service()
    result = turn(s, model, '¿Tienes pregrados virtuales?', reply='Estas son las opciones.')
    result = turn(s, model, '¿Y presenciales?', identifier=result['conversation_id'], reply='Estas son las opciones.')
    catalog.browse.assert_called_with(modality='presencial', level='pregrado')


def test_greeting_removed_in_later_turns_and_profile_help_can_clarify():
    s, model, _, _ = service()
    result = turn(s, model, 'Hola')
    result = turn(s, model, 'que mas necesitas saber', identifier=result['conversation_id'],
                  reply='¡Hola! ¿Qué temas te interesan?')
    assert not result['text'].startswith('¡Hola')
    assert model.generate.call_args.args[1]['intent'] == 'profile_help'
