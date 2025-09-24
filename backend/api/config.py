from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field

class ExternalAPISettings(BaseSettings):
    """
    Settings for the upstream (external) API.
    Env vars (with prefix EXTERNAL_API_):
      - BASE_URL (required)
      - TIMEOUT (seconds)
      - VERIFY_SSL (bool)
      - SERVICE_TOKEN (optional fallback)
    """
    base_url: AnyHttpUrl = Field(...)
    timeout: float = Field(10.0)
    verify_ssl: bool = Field(True)
    service_token: str | None = Field(None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EXTERNAL_API_",
        case_sensitive=False,
    )
