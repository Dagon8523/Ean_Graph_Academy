"""HTTP adapters. The LLM never receives credentials or runs Cypher."""
import json
from typing import Literal

import httpx
from pydantic import BaseModel, Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConversationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    neo4j_uri: str = 'bolt://localhost:7689'
    neo4j_user: str = 'neo4j'
    neo4j_password: SecretStr
    neo4j_database: str = 'neo4j'
    chat_provider: Literal['ollama', 'gemini'] = 'ollama'
    chat_model: str = 'gemma4:e2b'
    ollama_base_url: str = 'http://localhost:11434'
    gemini_api_key: SecretStr | None = None
    chat_timeout_seconds: float = Field(default=45, ge=1, le=50)
    chat_session_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    chat_session_db_path: str | None = None
    chat_max_sessions: int = Field(default=100, ge=1, le=1000)


class ModelUnavailable(Exception):
    pass


class ConversationModel:
    def __init__(self, settings):
        self.settings = settings

    def generate(self, instruction: str, payload: dict, schema: type[BaseModel]):
        settings = self.settings
        data = json.dumps(payload, ensure_ascii=False, default=str)
        try:
            with httpx.Client(timeout=settings.chat_timeout_seconds) as client:
                if settings.chat_provider == 'ollama':
                    response = client.post(
                        settings.ollama_base_url.rstrip('/') + '/api/chat',
                        json={
                            'model': settings.chat_model, 'stream': False,
                            'messages': [
                                {'role': 'system', 'content': instruction},
                                {'role': 'user', 'content': data},
                            ],
                            'format': schema.model_json_schema(),
                            'options': {'temperature': (0.45 if schema.__name__ == 'Reply' else 0), 'num_predict': 1200, 'num_ctx': 8192},
                        },
                    )
                    response.raise_for_status()
                    content = response.json()['message']['content']
                else:
                    if not settings.gemini_api_key:
                        raise ModelUnavailable('Falta GEMINI_API_KEY.')
                    response = client.post(
                        'https://generativelanguage.googleapis.com/v1beta/models/'
                        + settings.chat_model + ':generateContent',
                        headers={'x-goog-api-key': settings.gemini_api_key.get_secret_value()},
                        json={
                            'systemInstruction': {'parts': [{'text': instruction}]},
                            'contents': [{'role': 'user', 'parts': [{'text': data}]}],
                            'generationConfig': {
                                'temperature': (0.45 if schema.__name__ == 'Reply' else 0), 'maxOutputTokens': 1800,
                                'responseMimeType': 'application/json',
                                'responseJsonSchema': schema.model_json_schema(),
                            },
                        },
                    )
                    response.raise_for_status()
                    content = ''.join(
                        part.get('text', '') for part in
                        response.json()['candidates'][0]['content']['parts']
                        if not part.get('thought')
                    )
            return schema.model_validate_json(content)
        except ModelUnavailable:
            raise
        except (httpx.HTTPError, KeyError, IndexError, ValueError, ValidationError) as error:
            # Provider bodies and URLs may contain secrets; never expose them.
            raise ModelUnavailable('El modelo no está disponible o devolvió un formato inválido.') from error
