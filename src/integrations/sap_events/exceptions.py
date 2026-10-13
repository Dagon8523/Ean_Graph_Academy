"""Excepciones de la integración OData con SAP Datasphere."""

from __future__ import annotations


class SapODataError(Exception):
    """Error base de la integración SAP OData."""


class SapODataConfigurationError(SapODataError):
    """La configuración requerida para SAP está incompleta."""


class SapODataAuthenticationError(SapODataError):
    """SAP rechazó la autenticación configurada."""


class SapODataConnectionError(SapODataError):
    """No fue posible establecer comunicación con SAP."""


class SapODataContractError(SapODataError):
    """La respuesta de SAP no cumple el contrato esperado."""


class SapODataPaginationError(SapODataError):
    """SAP entregó una paginación inválida o cíclica."""


class SapODataUnsafeRedirectError(SapODataError):
    """SAP intentó continuar la consulta en un servidor no autorizado."""


class SapODataResponseError(SapODataError):
    """SAP respondió con un estado HTTP no satisfactorio."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
