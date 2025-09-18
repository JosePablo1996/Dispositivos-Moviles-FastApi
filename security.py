from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os

# SOLUCIÓN TEMPORAL: Usar APL_KEYS en lugar de API_KEYS
env_keys = os.getenv("APL_KEYS", "")  # ← Cambiado temporalmente
if not env_keys:
    # Fallback a API_KEYS por si acaso
    env_keys = os.getenv("API_KEYS", "")

# Lista de API keys válidas por defecto
DEFAULT_API_KEYS = [
    "gestor_estudiantes_key_2025",
    "android_app_key_2025", 
    "desarrollo_key_2025"
]

API_KEYS = env_keys.split(",") if env_keys else DEFAULT_API_KEYS
API_KEYS = [key.strip() for key in API_KEYS if key.strip()]

if not API_KEYS:
    API_KEYS = DEFAULT_API_KEYS

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key missing",
        )
    
    if api_key_header in API_KEYS:
        print(f"✅ API Key válida: {api_key_header}")
        return api_key_header
        
    print(f"❌ API Key inválida: {api_key_header}")
    print(f"📋 Keys configuradas: {API_KEYS}")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )

async def get_api_key(api_key: str = Security(api_key_header)):
    return await validate_api_key(api_key)