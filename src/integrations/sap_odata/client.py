from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Self

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import Settings


@dataclass(frozen=True)
class ODataPage:
    items: list[dict[str, Any]]
    next_link: str | None
    total_count: int | None


class SapProgramsClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.validate_sap_programs_ready()

        self._access_token: str | None = None
        self._token_expires_at = 0.0

        self._http = httpx.Client(
            timeout=httpx.Timeout(settings.sap_odata_timeout_seconds),
            headers={"Accept": "application/json"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _get_access_token(self) -> str:
        if self._access_token and time.monotonic() < self._token_expires_at:
            return self._access_token

        data = {"grant_type": "client_credentials"}

        if self.settings.sap_oauth_scope:
            data["scope"] = self.settings.sap_oauth_scope

        response = self._http.post(
            self.settings.sap_oauth_token_url,
            data=data,
            auth=(
                self.settings.sap_oauth_client_id,
                self.settings.sap_oauth_client_secret.get_secret_value(),
            ),
        )
        response.raise_for_status()

        payload = response.json()
        access_token = payload.get("access_token")

        if not access_token:
            raise RuntimeError("La respuesta OAuth no contiene access_token")

        expires_in = int(payload.get("expires_in", 3600))

        self._access_token = access_token
        self._token_expires_at = time.monotonic() + max(expires_in - 60, 60)

        return access_token

    @retry(
        retry=retry_if_exception_type(
            (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
            )
        ),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    @retry(
        retry=retry_if_exception_type(
            (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
            )
        ),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        token = self._get_access_token()

        response = self._http.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 401:
            self._access_token = None
            self._token_expires_at = 0

            token = self._get_access_token()

            response = self._http.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )

        if response.is_error:
            response_preview = response.text[:2000]

            raise httpx.HTTPStatusError(
                (
                    f"SAP OData respondió HTTP "
                    f"{response.status_code}. "
                    f"Detalle: {response_preview}"
                ),
                request=response.request,
                response=response,
            )

        payload = response.json()

        if not isinstance(payload, dict):
            raise TypeError("La respuesta SAP OData no es un objeto JSON")

        return payload

    def fetch_page(
        self,
        url: str | None = None,
        page_size: int | None = None,
        skip: int = 0,
    ) -> ODataPage:
        request_url = url or self.settings.sap_programs_entity_url

        params = None
        if url is None:
            params = {
                "$top": page_size or self.settings.sap_odata_page_size,
                "$skip": skip,
            }

        payload = self._get_json(request_url, params=params)

        items = payload.get("value", [])
        if not isinstance(items, list):
            raise TypeError("La respuesta OData no contiene una lista en 'value'")

        raw_count = payload.get("@odata.count")
        total_count = int(raw_count) if raw_count is not None else None

        return ODataPage(
            items=items,
            next_link=payload.get("@odata.nextLink"),
            total_count=total_count,
        )

    def iter_pages(
        self,
        page_size: int | None = None,
    ) -> Iterator[ODataPage]:
        effective_page_size = page_size or self.settings.sap_odata_page_size
        skip = 0
        page_number = 1
        seen_signatures: set[str] = set()

        while True:
            page = self.fetch_page(
                page_size=effective_page_size,
                skip=skip,
            )

            if not page.items:
                break

            serialized_page = json.dumps(
                page.items,
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
            signature = hashlib.sha256(serialized_page.encode("utf-8")).hexdigest()

            if signature in seen_signatures:
                raise RuntimeError(
                    "SAP repitió una página. "
                    f"Página detectada: {page_number}; skip={skip}"
                )

            seen_signatures.add(signature)
            yield page

            records_read = len(page.items)

            if records_read < effective_page_size:
                break

            skip += records_read
            page_number += 1
