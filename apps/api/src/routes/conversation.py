from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, HTTPException
from neo4j.exceptions import Neo4jError

from apps.api.src.schemas.conversation import ConversationRequest, ConversationResponse
from src.repositories.job_offer_repository import JobOfferRepository
from src.repositories.conversation_catalog_repository import ConversationCatalogRepository
from src.repositories.recommendation_repository import RecommendationRepository
from src.services.conversation_model import ConversationModel, ConversationSettings, ModelUnavailable
from src.services.conversation_service import ConversationService, SessionStore, SessionMissing, SessionBusy
from src.services.persistent_session_store import PersistentSessionStore
from src.services.recommendation_service import RecommendationService

router = APIRouter(prefix='/api/v1/conversations', tags=['Orientador conversacional'])


@lru_cache
def get_store():
    settings = ConversationSettings()
    if settings.chat_session_db_path:
        return PersistentSessionStore(settings.chat_session_db_path,
                                      settings.chat_session_ttl_seconds,
                                      settings.chat_max_sessions)
    return SessionStore(settings.chat_session_ttl_seconds, settings.chat_max_sessions)


@router.post('/message', response_model=ConversationResponse)
def message(request: ConversationRequest):
    settings = ConversationSettings()
    academic = RecommendationRepository(settings)
    jobs = JobOfferRepository(settings)
    catalog = ConversationCatalogRepository(settings)
    try:
        service = ConversationService(ConversationModel(settings),
                                      RecommendationService(academic), jobs, get_store(), catalog=catalog)
        return service.chat(request)
    except SessionMissing as error:
        raise HTTPException(404, 'La conversación expiró. Inicia una conversación nueva.') from error
    except SessionBusy as error:
        raise HTTPException(409, 'Hay una consulta en curso o se alcanzó el límite de sesiones.') from error
    except ModelUnavailable as error:
        raise HTTPException(503, str(error)) from error
    except Neo4jError as error:
        raise HTTPException(503, 'No fue posible consultar el catálogo académico de Neo4j.') from error
    except ValueError as error:
        raise HTTPException(422, 'No fue posible procesar el mensaje. Revisa su contenido.') from error
    finally:
        academic.close()
        jobs.close()
        catalog.close()


@router.delete('/{conversation_id}', status_code=204)
def delete_conversation(conversation_id: UUID):
    try:
        get_store().delete(conversation_id)
    except SessionMissing as error:
        raise HTTPException(404, 'La conversación no existe o expiró.') from error
    except SessionBusy as error:
        raise HTTPException(409, 'Espera a que termine la consulta antes de borrar la conversación.') from error
