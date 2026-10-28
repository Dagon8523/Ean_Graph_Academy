from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsConfigurationError(ValueError):
    """Configuración incompleta o inválida."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7689"
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr
    neo4j_database: str = "neo4j"

    # SAP Datasphere - Educación Continuada
    sap_events_auth_type: str = "oauth2_client_credentials"
    sap_events_entity_url: str | None = None

    sap_events_page_size: int = Field(
        default=1000,
        ge=1,
        le=5000,
    )
    sap_events_timeout_seconds: float = Field(
        default=60,
        gt=0,
    )
    sap_events_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
    )
    sap_events_verify_ssl: bool = True

    sap_events_username: str | None = None
    sap_events_password: SecretStr | None = None

    # SAP Datasphere
    sap_programs_auth_type: str = "oauth2_client_credentials"
    sap_programs_entity_url: str | None = None

    sap_oauth_token_url: str | None = None
    sap_oauth_client_id: str | None = None
    sap_oauth_client_secret: SecretStr | None = None
    sap_oauth_scope: str | None = None

    sap_odata_page_size: int = Field(default=1000, ge=1, le=5000)
    sap_odata_timeout_seconds: float = Field(default=60, gt=0)
    sap_odata_max_retries: int = Field(default=3, ge=0, le=10)

    def validate_sap_programs_ready(self) -> None:
        if self.sap_programs_auth_type != "oauth2_client_credentials":
            raise ValueError(
                "SAP_PROGRAMS_AUTH_TYPE debe ser oauth2_client_credentials"
            )

        required_values = {
            "SAP_PROGRAMS_ENTITY_URL": self.sap_programs_entity_url,
            "SAP_OAUTH_TOKEN_URL": self.sap_oauth_token_url,
            "SAP_OAUTH_CLIENT_ID": self.sap_oauth_client_id,
            "SAP_OAUTH_CLIENT_SECRET": (
                (self.sap_oauth_client_secret.get_secret_value() if self.sap_oauth_client_secret else None)
            ),
        }

        missing = [
            name
            for name, value in required_values.items()
            if not value or value.strip().lower() in {"change_me", "coloca_aqui"}
        ]

        if missing:
            raise ValueError("Faltan variables SAP válidas: " + ", ".join(missing))

    def validate_sap_events_ready(self) -> None:
        if not self.sap_events_entity_url:
            raise SettingsConfigurationError("Falta SAP_EVENTS_ENTITY_URL")

        if self.sap_events_auth_type != "oauth2_client_credentials":
            raise SettingsConfigurationError(
                "SAP_EVENTS_AUTH_TYPE debe ser oauth2_client_credentials"
            )

        required_values = {
            "SAP_OAUTH_TOKEN_URL": (self.sap_oauth_token_url),
            "SAP_OAUTH_CLIENT_ID": (self.sap_oauth_client_id),
            "SAP_OAUTH_CLIENT_SECRET": (
                (self.sap_oauth_client_secret.get_secret_value() if self.sap_oauth_client_secret else None)
            ),
        }

        missing = [
            name
            for name, value in required_values.items()
            if not value or not str(value).strip()
        ]

        if missing:
            raise SettingsConfigurationError(
                "Faltan variables SAP: " + ", ".join(missing)
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
