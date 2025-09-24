from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import ExternalAPISettings
from .client import ExternalAPIClient

_security = HTTPBearer(auto_error=False)

def get_settings() -> ExternalAPISettings:
    return ExternalAPISettings()

def get_api_client(settings: ExternalAPISettings = Depends(get_settings)) -> ExternalAPIClient:
    return ExternalAPIClient(settings)

async def get_user_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> str | None:
    if credentials and credentials.scheme.lower() == "bearer" and credentials.credentials:
        return credentials.credentials
    return None
