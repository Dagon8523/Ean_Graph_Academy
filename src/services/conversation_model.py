"""Adaptador del modelo conversacional de Ruta EAN.

El grafo Neo4j es consultado por los servicios existentes de la aplicación.
Este adaptador solo recibe los datos recuperados en `payload` y produce una
respuesta validada con Pydantic. No recibe credenciales ni ejecuta Cypher.
"""

import json
import logging
import socket
import time
from typing import Literal

import httpx

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)


class ConversationSettings(BaseSettings):
    """Configuración compatible con el backend del Cerebro Académico."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Neo4j: se conserva exactamente la interfaz de configuración existente.
    # En Docker usar el nombre DNS del servicio Neo4j, no localhost.
    neo4j_uri: str = "bolt://localhost:7689"
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr
    neo4j_database: str = "neo4j"

    # Se elimina Ollama como motor generativo.
    chat_provider: Literal["gemini"] = "gemini"
    chat_model: str = "gemini-3.5-flash"

    # Vertex AI usa Application Default Credentials (ADC).
    # Permite opcionalmente la Gemini Developer API con clave API.
    gemini_backend: Literal["vertexai", "developer"] = "vertexai"
    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    gemini_api_key: SecretStr | None = None

    chat_timeout_seconds: float = Field(default=45, ge=1, le=120)
    chat_session_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    chat_session_db_path: str | None = None
    chat_max_sessions: int = Field(default=100, ge=1, le=1000)


class ModelUnavailable(Exception):
    """El proveedor no respondió o el resultado no cumple el contrato."""


class ConversationModel:
    """Mantiene la firma de generate() usada por los servicios existentes."""

    def __init__(self, settings: ConversationSettings):
        self.settings = settings

    def _build_client(self):
        settings = self.settings
        options = types.HttpOptions(
            api_version="v1" if settings.gemini_backend == "vertexai" else "v1beta",
            timeout=int(settings.chat_timeout_seconds * 1000),
        )

        if settings.gemini_backend == "vertexai":
            if not settings.google_cloud_project:
                raise ModelUnavailable(
                    "Falta GOOGLE_CLOUD_PROJECT para utilizar Vertex AI."
                )
            return genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
                http_options=options,
            )

        if not settings.gemini_api_key:
            raise ModelUnavailable(
                "Falta GEMINI_API_KEY para utilizar Gemini Developer API."
            )
        return genai.Client(
            api_key=settings.gemini_api_key.get_secret_value(),
            http_options=options,
        )

    @staticmethod
    def _is_connection_failure(exc: Exception) -> bool:
        """Detecta fallos de conexión, incluso si el SDK los envuelve."""
        current = exc
        visited = set()

        while current is not None and id(current) not in visited:
            visited.add(id(current))

            if isinstance(
                current,
                (httpx.ConnectError, httpx.ConnectTimeout, socket.gaierror),
            ):
                return True

            if isinstance(current, OSError) and current.errno in {
                101,  # Network is unreachable
                110,  # Connection timed out
                111,  # Connection refused
            }:
                return True

            current = current.__cause__ or current.__context__

        return False

    def generate(
        self,
        instruction: str,
        payload: dict,
        schema: type[BaseModel],
    ) -> BaseModel:
        """Genera una respuesta estructurada, sin ejecutar consultas al grafo.

        `payload` contiene los datos preparados por los servicios Neo4j.
        `schema` es la clase Pydantic esperada (por ejemplo Reply).
        """
        settings = self.settings

        if settings.chat_provider != "gemini":
            raise ModelUnavailable(
                "CHAT_PROVIDER debe ser 'gemini'; Ollama está deshabilitado."
            )

        try:
            data = json.dumps(payload, ensure_ascii=False, default=str)

            # Algunos esquemas Pydantic incluyen Literal["", ...] en campos
            # como modality/level. Vertex AI no acepta enums con valores
            # vacíos dentro de response_schema (HTTP 400 INVALID_ARGUMENT).
            # Por eso solicitamos JSON sin imponer ese esquema en la API y
            # validamos el resultado con Pydantic, sin cambiar el contrato.
            schema_json = json.dumps(
                schema.model_json_schema(), ensure_ascii=False
            )
            system_instruction = (
                instruction
                + "\n\nDevuelve EXCLUSIVAMENTE un objeto JSON válido, "
                  "sin Markdown ni explicaciones externas. "
                  "Respeta el siguiente esquema JSON, incluidos sus "
                  "campos obligatorios y valores permitidos. "
                  "Si el esquema permite la cadena vacía, puedes usarla "
                  "cuando corresponda. No inventes información.\n"
                + schema_json
            )
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=4096,
                response_mime_type="application/json",
            )

            # Reintentos limitados para fallos transitorios de conexión.
            # Cada intento utiliza un cliente independiente.
            # No se reintentan errores de esquema o configuración.
            for attempt in range(1, 4):
                try:
                    with self._build_client() as client:
                        response = client.models.generate_content(
                            model=settings.chat_model,
                            contents=data,
                            config=config,
                        )
                    break

                except Exception as exc:
                    if attempt == 3 or not self._is_connection_failure(exc):
                        raise

                    delay = attempt  # 1 y 2 segundos.
                    logger.warning(
                        "Gemini: fallo de conexión en intento %s/3; "
                        "nuevo intento en %ss. Error: %s",
                        attempt,
                        delay,
                        type(exc).__name__,
                    )
                    time.sleep(delay)

            parsed = response.parsed
            if isinstance(parsed, schema):
                return parsed

            if parsed is not None:
                return schema.model_validate(parsed)

            if not response.text:
                raise ModelUnavailable(
                    "Gemini no devolvió contenido JSON válido."
                )

            return schema.model_validate_json(response.text)

        except ModelUnavailable:
            raise
        except (ValidationError, ValueError, TypeError) as exc:
            logger.warning(
                "Respuesta inválida de Gemini: %s", type(exc).__name__
            )
            raise ModelUnavailable(
                "Gemini devolvió una respuesta que no cumple el esquema."
            ) from exc
        except Exception as exc:
            # Nunca incluir mensajes externos que puedan contener secretos.
            logger.error(
                "Fallo del proveedor Gemini: %s", type(exc).__name__
            )
            raise ModelUnavailable(
                "El modelo Gemini no está disponible. "
                "Verifique proyecto, permisos, región y modelo."
            ) from exc
