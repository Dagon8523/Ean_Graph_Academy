"""Cliente HTTP asíncrono para SAP Datasphere mediante OData."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Mapping
from contextlib import suppress
from typing import Any, Self
from urllib.parse import urljoin, urlsplit

import httpx
import structlog
from pydantic import ValidationError

from src.config.settings import Settings, SettingsConfigurationError
from src.integrations.sap_events.exceptions import (
    SapODataAuthenticationError,
    SapODataConfigurationError,
    SapODataConnectionError,
    SapODataContractError,
    SapODataPaginationError,
    SapODataResponseError,
    SapODataUnsafeRedirectError,
)
from src.integrations.sap_events.models import SapEventRecord, SapODataPage

logger = structlog.get_logger(__name__)

_RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}

_MAX_PAGES = 100_000
_TOKEN_EXPIRATION_MARGIN_SECONDS = 30.0


class SapODataClient:
    """Consulta eventos desde SAP Datasphere mediante OData V4."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._http_client = http_client
        self._owns_http_client = http_client is None

        self._access_token: str | None = None
        self._access_token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

        try:
            self._settings.validate_sap_events_ready()
        except SettingsConfigurationError as error:
            raise SapODataConfigurationError(str(error)) from error

        entity_url = self._settings.sap_events_entity_url

        if entity_url is None:
            raise SapODataConfigurationError(
                "No fue posible construir la URL del EntitySet SAP."
            )

        self._entity_url = entity_url
        self._allowed_origin = self._get_origin(entity_url)

    @property
    def entity_url(self) -> str:
        """Retorna la URL completa del EntitySet configurado."""

        return self._entity_url

    @property
    def is_open(self) -> bool:
        """Indica si existe un cliente HTTP disponible."""

        return self._http_client is not None

    async def __aenter__(self) -> Self:
        """Abre el cliente para utilizarlo como administrador de contexto."""

        self._get_http_client()
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        """Cierra los recursos administrados por el cliente."""

        await self.close()

    async def close(self) -> None:
        """Cierra el cliente HTTP cuando fue creado internamente."""

        if self._http_client is None:
            return

        if self._owns_http_client:
            await self._http_client.aclose()

        self._http_client = None

    async def iter_pages(self) -> AsyncIterator[SapODataPage]:

        page_size = self._settings.sap_events_page_size
        current_url = self._entity_url
        current_params: Mapping[str, str | int] | None = {
            "$top": page_size,
            "$skip": 0,
            "$count": "true",
            "$orderby": "EVENTO_ID asc",
        }

        visited_urls: set[str] = set()
        page_number = 0
        offset = 0
        total_count: int | None = None
        following_next_link = False

        while current_url:
            page_number += 1

            if page_number > _MAX_PAGES:
                raise SapODataPaginationError(
                    "La consulta superó el máximo permitido de páginas."
                )

            request_identifier = self._build_request_identifier(
                current_url,
                current_params,
            )

            if request_identifier in visited_urls:
                raise SapODataPaginationError(
                    "SAP devolvió un ciclo en la paginación OData."
                )

            visited_urls.add(request_identifier)

            page = await self._fetch_page(
                current_url,
                params=current_params,
            )

            if page.total_count is not None:
                total_count = page.total_count

            logger.info(
                "sap_odata_page_received",
                page_number=page_number,
                item_count=page.item_count,
                total_count=total_count,
                offset=offset,
                has_next_link=bool(page.next_link),
            )

            yield page

            # Primera opción: continuación enviada directamente por SAP.
            if page.next_link is not None:
                current_url = self._resolve_next_link(
                    current_url=current_url,
                    next_link=page.next_link,
                )
                current_params = None
                following_next_link = True
                continue

            # Si veníamos siguiendo nextLink y ya no llegó otro, finaliza.
            if following_next_link:
                break

            # Una página vacía siempre indica el final.
            if page.item_count == 0:
                break

            offset += page.item_count

            # Sin nextLink ni @odata.count no es seguro seguir usando $skip.
            if total_count is None:
                break

            # Ya se alcanzó el total informado por SAP.
            if offset >= total_count:
                break

            # Continuación manual para SAP Datasphere.
            current_url = self._entity_url
            current_params = {
                "$top": page_size,
                "$skip": offset,
                "$orderby": "EVENTO_ID asc",
            }

    async def iter_events(self) -> AsyncIterator[SapEventRecord]:
        """Entrega los eventos individualmente sin cargar todo en memoria."""

        async for page in self.iter_pages():
            for event in page.items:
                yield event

    async def _fetch_page(
        self,
        url: str,
        *,
        params: Mapping[str, str | int] | None,
    ) -> SapODataPage:
        """Descarga y valida una página OData."""

        payload = await self._request_json(
            method="GET",
            url=url,
            params=params,
        )

        try:
            return SapODataPage.model_validate(payload)
        except ValidationError as error:
            logger.error(
                "sap_odata_contract_validation_failed",
                validation_error_count=error.error_count(),
            )

            raise SapODataContractError(
                "La respuesta de SAP no cumple el contrato OData esperado."
            ) from error

    async def _request_json(
        self,
        *,
        method: str,
        url: str,
        params: Mapping[str, str | int] | None = None,
    ) -> dict[str, Any]:
        """Ejecuta una petición y retorna una respuesta JSON."""

        authentication_was_refreshed = False
        maximum_attempts = self._settings.sap_events_max_retries + 1

        for attempt in range(1, maximum_attempts + 1):
            headers = await self._build_request_headers()

            try:
                response = await self._get_http_client().request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                )
            except (httpx.TimeoutException, httpx.TransportError) as error:
                if attempt >= maximum_attempts:
                    raise SapODataConnectionError(
                        "No fue posible establecer comunicación con SAP."
                    ) from error

                await self._wait_before_retry(attempt)
                continue

            if (
                response.status_code == 401
                and self._settings.sap_events_auth_type == "oauth2_client_credentials"
                and not authentication_was_refreshed
            ):
                self._invalidate_access_token()
                authentication_was_refreshed = True
                continue

            if response.status_code in _RETRYABLE_STATUS_CODES:
                if attempt >= maximum_attempts:
                    raise SapODataResponseError(
                        "SAP no respondió satisfactoriamente después "
                        "de los reintentos configurados.",
                        status_code=response.status_code,
                    )

                await self._wait_before_retry(
                    attempt,
                    response=response,
                )
                continue

            if response.status_code in {401, 403}:
                raise SapODataAuthenticationError(
                    "SAP rechazó la autenticación configurada."
                )

            if not response.is_success:
                raise SapODataResponseError(
                    "SAP respondió con un estado HTTP no satisfactorio.",
                    status_code=response.status_code,
                )

            try:
                payload = response.json()
            except ValueError as error:
                raise SapODataContractError(
                    "SAP respondió con un contenido que no es JSON válido."
                ) from error

            if not isinstance(payload, dict):
                raise SapODataContractError(
                    "La respuesta JSON de SAP debe ser un objeto."
                )

            return payload

        raise SapODataConnectionError(
            "La petición a SAP terminó sin obtener una respuesta."
        )

    async def _build_request_headers(self) -> dict[str, str]:
        """Construye los encabezados sin exponer credenciales."""

        headers = {
            "Accept": "application/json",
            "OData-Version": "4.0",
        }

        if self._settings.sap_events_auth_type == "oauth2_client_credentials":
            access_token = await self._get_access_token()
            headers["Authorization"] = f"Bearer {access_token}"

        return headers

    async def _get_access_token(self) -> str:
        """Obtiene y conserva temporalmente un token OAuth2."""

        if self._is_access_token_valid():
            return self._access_token or ""

        async with self._token_lock:
            if self._is_access_token_valid():
                return self._access_token or ""

            token_url = self._settings.sap_oauth_token_url
            client_id = self._settings.sap_oauth_client_id
            client_secret = self._settings.sap_oauth_client_secret

            if token_url is None or client_id is None or client_secret is None:
                raise SapODataConfigurationError(
                    "La configuración OAuth2 de SAP está incompleta."
                )

            try:
                response = await self._get_http_client().post(
                    str(token_url),
                    data={"grant_type": "client_credentials"},
                    auth=httpx.BasicAuth(
                        username=client_id,
                        password=client_secret.get_secret_value(),
                    ),
                    headers={
                        "Accept": "application/json",
                        "Content-Type": ("application/x-www-form-urlencoded"),
                    },
                )
            except (httpx.TimeoutException, httpx.TransportError) as error:
                raise SapODataConnectionError(
                    "No fue posible solicitar el token OAuth2 de SAP."
                ) from error

            if not response.is_success:
                raise SapODataAuthenticationError(
                    "SAP rechazó la solicitud del token OAuth2."
                )

            try:
                payload = response.json()
            except ValueError as error:
                raise SapODataAuthenticationError(
                    "La respuesta OAuth2 de SAP no es JSON válido."
                ) from error

            if not isinstance(payload, dict):
                raise SapODataAuthenticationError(
                    "La respuesta OAuth2 de SAP tiene un formato inválido."
                )

            access_token = payload.get("access_token")
            expires_in = payload.get("expires_in", 300)

            if not isinstance(access_token, str) or not access_token:
                raise SapODataAuthenticationError(
                    "SAP no entregó un access_token válido."
                )

            try:
                expiration_seconds = max(float(expires_in), 0.0)
            except (TypeError, ValueError) as error:
                raise SapODataAuthenticationError(
                    "SAP entregó un expires_in inválido."
                ) from error

            usable_lifetime = max(
                expiration_seconds - _TOKEN_EXPIRATION_MARGIN_SECONDS,
                1.0,
            )

            self._access_token = access_token
            self._access_token_expires_at = time.monotonic() + usable_lifetime

            logger.info(
                "sap_oauth_token_obtained",
                expires_in_seconds=expiration_seconds,
            )

            return access_token

    def _get_http_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP reutilizable."""

        if self._http_client is not None:
            return self._http_client

        authentication: httpx.Auth | None = None

        if self._settings.sap_events_auth_type == "basic":
            username = self._settings.sap_events_username
            password = self._settings.sap_events_password

            if username is None or password is None:
                raise SapODataConfigurationError(
                    "La autenticación básica SAP está incompleta."
                )

            authentication = httpx.BasicAuth(
                username=username,
                password=password.get_secret_value(),
            )

        timeout = httpx.Timeout(
            self._settings.sap_events_timeout_seconds,
        )

        self._http_client = httpx.AsyncClient(
            auth=authentication,
            timeout=timeout,
            verify=self._settings.sap_events_verify_ssl,
            follow_redirects=False,
        )

        return self._http_client

    def _resolve_next_link(
        self,
        *,
        current_url: str,
        next_link: str,
    ) -> str:
        """Resuelve y valida un nextLink absoluto o relativo."""

        resolved_url = urljoin(current_url, next_link)

        if self._get_origin(resolved_url) != self._allowed_origin:
            raise SapODataUnsafeRedirectError(
                "SAP devolvió un nextLink dirigido a otro servidor."
            )

        return resolved_url

    def _is_access_token_valid(self) -> bool:
        """Indica si el token almacenado todavía puede utilizarse."""

        return (
            self._access_token is not None
            and time.monotonic() < self._access_token_expires_at
        )

    def _invalidate_access_token(self) -> None:
        """Descarta el token OAuth2 almacenado."""

        self._access_token = None
        self._access_token_expires_at = 0.0

    async def _wait_before_retry(
        self,
        attempt: int,
        *,
        response: httpx.Response | None = None,
    ) -> None:
        """Espera antes de repetir una petición transitoria."""

        delay_seconds = min(2 ** (attempt - 1), 30)

        if response is not None:
            retry_after = response.headers.get("Retry-After")

        if retry_after:
            with suppress(ValueError):
                delay_seconds = min(
                    max(float(retry_after), 0.0),
                    60.0,
                )

        logger.warning(
            "sap_odata_request_retry",
            attempt=attempt,
            delay_seconds=delay_seconds,
            status_code=(response.status_code if response is not None else None),
        )

        await asyncio.sleep(delay_seconds)

    @staticmethod
    def _build_request_identifier(
        url: str,
        params: Mapping[str, str | int] | None,
    ) -> str:
        """Construye un identificador estable para detectar ciclos."""

        if not params:
            return url

        serialized_params = "&".join(
            f"{key}={value}" for key, value in sorted(params.items())
        )

        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{serialized_params}"

    @staticmethod
    def _get_origin(url: str) -> tuple[str, str, int | None]:
        """Extrae esquema, servidor y puerto de una URL."""

        parsed_url = urlsplit(url)

        if parsed_url.scheme not in {"http", "https"}:
            raise SapODataUnsafeRedirectError(
                "La URL OData utiliza un esquema no permitido."
            )

        if parsed_url.hostname is None:
            raise SapODataUnsafeRedirectError(
                "La URL OData no contiene un servidor válido."
            )

        return (
            parsed_url.scheme.lower(),
            parsed_url.hostname.lower(),
            parsed_url.port,
        )
