from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os

# Leer API keys desde variables de entorno (sin dotenv)
API_KEYS = os.getenv("API_KEYS", "gestor_estudiantes_key_2025,android_app_key_2025,desarrollo_key_2025").split(",")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key missing",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    if api_key_header in API_KEYS:
        return api_key_header
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
        headers={"WWW-Authenticate": "APIKey"},
    )

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key in API_KEYS:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )