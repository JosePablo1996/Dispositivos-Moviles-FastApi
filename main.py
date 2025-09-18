from fastapi import FastAPI, HTTPException, Path, Depends, Security, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from urllib.parse import quote_plus
import os
import logging
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la contraseña de variable de entorno
PASSWORD = os.getenv("DB_PASSWORD", "uPxBHn]Ag9H~N4'K")
ENCODED_PASSWORD = quote_plus(PASSWORD)

# URL de conexión a tu base de datos EXISTENTE - CORREGIDA: mq100216
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://postgres:{ENCODED_PASSWORD}@20.84.99.214:443/mq100216"
)

# Configuración de la base de datos
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    # Verificar conexión y estructura existente
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'estudiantes'"))
        existing_columns = [row[0] for row in result]
        logger.info(f"Columnas existentes en la tabla: {existing_columns}")
        
except Exception as e:
    logger.error(f"Error al conectar con la base de datos: {e}")
    raise

# Usar Base existente para compatibilidad
Base = declarative_base()

# Mapear la tabla EXISTENTE 'estudiantes'
class Estudiante(Base):
    __tablename__ = 'estudiantes'
    __table_args__ = {'extend_existing': True}  # Importantísimo para tablas existentes
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    edad = Column(Integer, nullable=False)

# Esquemas Pydantic
class EstudianteSchema(BaseModel):
    nombre: str
    edad: int

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "edad": 25
            }
        }

class EstudianteResponse(BaseModel):
    id: int
    nombre: str
    edad: int

    class Config:
        from_attributes = True

# Configuración de API Keys específicas para Android
API_KEYS = {
    "android_app_key_2025": "Aplicación Android Principal",
    "gestor_estudiantes_key_2025": "Gestor de Estudiantes Android", 
    "desarrollo_key_2025": "Key de Desarrollo y Testing"
}

# Función para validar API Key
def validate_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if api_key in API_KEYS:
        return api_key
    raise HTTPException(
        status_code=401,
        detail="API Key inválida o faltante. Use una de las siguientes: android_app_key_2025, gestor_estudiantes_key_2025, desarrollo_key_2025",
        headers={"WWW-Authenticate": "APIKey"}
    )

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="API de Gestión de Estudiantes",
    version="2.0.0",
    description="API para gestión de estudiantes con base de datos existente",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS - ACTUALIZADO para React y Android
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React development
        "http://localhost:5173",    # Vite development
        "http://localhost:8080",    # Android emulator
        "http://localhost",         # Local development
        "https://tu-app-react.vercel.app",  # Tu dominio de producción React
        "https://*.render.com",     # Render deployments
        "*"                         # Para desarrollo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas de la API
@app.get("/", tags=["Home"])
def home():
    return {"message": "Bienvenido a la API de estudiantes!", "database": "mq100216"}

@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Verifica el estado de la conexión a la base de datos"""
    try:
        # Verificar que la tabla exista y tenga datos
        count = db.query(Estudiante).count()
        return {
            "status": "healthy",
            "database": "connected",
            "table": "estudiantes",
            "total_estudiantes": count,
            "message": f"Conexión exitosa a la base de datos existente"
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

# Endpoints públicos (no requieren API Key) - PARA REACT
@app.get("/public/estudiantes/", response_model=list[EstudianteResponse], tags=["Estudiantes - Público"])
def obtener_estudiantes_publico(db: Session = Depends(get_db)):
    """Obtiene todos los estudiantes (público - sin API Key)"""
    try:
        estudiantes = db.query(Estudiante).order_by(Estudiante.id).all()
        return estudiantes
    except Exception as e:
        logger.error(f"Error al obtener estudiantes: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiantes: {str(e)}")

@app.post("/public/estudiantes/", response_model=EstudianteResponse, tags=["Estudiantes - Público"])
def crear_estudiante_publico(estudiante: EstudianteSchema, db: Session = Depends(get_db)):
    """Crea un nuevo estudiante (público - sin API Key)"""
    try:
        db_estudiante = Estudiante(nombre=estudiante.nombre, edad=estudiante.edad)
        db.add(db_estudiante)
        db.commit()
        db.refresh(db_estudiante)
        return db_estudiante
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear estudiante: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")

@app.put("/public/estudiantes/{id}", response_model=EstudianteResponse, tags=["Estudiantes - Público"])
def modificar_estudiante_publico(id: int, estudiante: EstudianteSchema, db: Session = Depends(get_db)):
    """Modifica un estudiante existente (público - sin API Key)"""
    try:
        est = db.query(Estudiante).filter(Estudiante.id == id).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        est.nombre = estudiante.nombre
        est.edad = estudiante.edad
        db.commit()
        db.refresh(est)
        return est
    except Exception as e:
        db.rollback()
        logger.error(f"Error al modificar estudiante {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al modificar estudiante: {str(e)}")

@app.delete("/public/estudiantes/{id}", tags=["Estudiantes - Público"])
def eliminar_estudiante_publico(id: int, db: Session = Depends(get_db)):
    """Elimina un estudiante (público - sin API Key)"""
    try:
        est = db.query(Estudiante).filter(Estudiante.id == id).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        db.delete(est)
        db.commit()
        return {"mensaje": "Estudiante eliminado exitosamente"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar estudiante {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar estudiante: {str(e)}")

# Endpoints protegidos (requieren API Key) - PARA ANDROID
@app.get("/android/estudiantes/", response_model=list[EstudianteResponse], tags=["Estudiantes - Android"])
def obtener_estudiantes_android(
    db: Session = Depends(get_db),
    api_key: str = Security(validate_api_key)
):
    """Obtiene todos los estudiantes (protegido - requiere API Key)"""
    try:
        estudiantes = db.query(Estudiante).order_by(Estudiante.id).all()
        logger.info(f"API Key utilizada: {api_key} - {API_KEYS[api_key]}")
        return estudiantes
    except Exception as e:
        logger.error(f"Error al obtener estudiantes: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiantes: {str(e)}")

@app.get("/android/estudiantes/{id}", response_model=EstudianteResponse, tags=["Estudiantes - Android"])
def obtener_estudiante_android_por_id(
    id: int = Path(..., ge=1), 
    db: Session = Depends(get_db),
    api_key: str = Security(validate_api_key)
):
    """Obtiene un estudiante por ID (protegido - requiere API Key)"""
    try:
        estudiante = db.query(Estudiante).filter(Estudiante.id == id).first()
        if not estudiante:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        logger.info(f"API Key utilizada: {api_key} - {API_KEYS[api_key]}")
        return estudiante
    except Exception as e:
        logger.error(f"Error al obtener estudiante {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiante: {str(e)}")

@app.post("/android/estudiantes/", response_model=EstudianteResponse, tags=["Estudiantes - Android"])
def crear_estudiante_android(
    estudiante: EstudianteSchema, 
    db: Session = Depends(get_db),
    api_key: str = Security(validate_api_key)
):
    """Crea un nuevo estudiante (protegido - requiere API Key)"""
    try:
        db_estudiante = Estudiante(nombre=estudiante.nombre, edad=estudiante.edad)
        db.add(db_estudiante)
        db.commit()
        db.refresh(db_estudiante)
        logger.info(f"API Key utilizada: {api_key} - {API_KEYS[api_key]}")
        return db_estudiante
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear estudiante: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")

@app.put("/android/estudiantes/{id}", response_model=EstudianteResponse, tags=["Estudiantes - Android"])
def modificar_estudiante_android(
    id: int, 
    estudiante: EstudianteSchema, 
    db: Session = Depends(get_db),
    api_key: str = Security(validate_api_key)
):
    """Modifica un estudiante existente (protegido - requiere API Key)"""
    try:
        est = db.query(Estudiante).filter(Estudiante.id == id).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        est.nombre = estudiante.nombre
        est.edad = estudiante.edad
        db.commit()
        db.refresh(est)
        logger.info(f"API Key utilizada: {api_key} - {API_KEYS[api_key]}")
        return est
    except Exception as e:
        db.rollback()
        logger.error(f"Error al modificar estudiante {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al modificar estudiante: {str(e)}")

@app.delete("/android/estudiantes/{id}", tags=["Estudiantes - Android"])
def eliminar_estudiante_android(
    id: int, 
    db: Session = Depends(get_db),
    api_key: str = Security(validate_api_key)
):
    """Elimina un estudiante (protegido - requiere API Key)"""
    try:
        est = db.query(Estudiante).filter(Estudiante.id == id).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        db.delete(est)
        db.commit()
        logger.info(f"API Key utilizada: {api_key} - {API_KEYS[api_key]}")
        return {"mensaje": "Estudiante eliminado exitosamente"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar estudiante {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar estudiante: {str(e)}")

# Endpoints de información
@app.get("/api-key-info", tags=["Security"])
def api_key_info():
    """Información sobre las API Keys"""
    return {
        "api_key_required": "Solo para endpoints /android/",
        "public_endpoints": "Disponibles en /public/estudiantes/",
        "how_to_use": "Incluir header: X-API-Key: tu_api_key",
        "available_keys": {
            "android_app_key_2025": "Aplicación Android Principal",
            "gestor_estudiantes_key_2025": "Gestor de Estudiantes Android", 
            "desarrollo_key_2025": "Key de Desarrollo y Testing"
        },
        "note": "Endpoints /public/ no requieren API Key para React"
    }

@app.get("/api-status", tags=["Info"])
def api_status():
    """Estado de la API y configuración"""
    return {
        "status": "active",
        "version": "2.0.0",
        "database": "connected",
        "cors_enabled": True,
        "security_mode": "dual",
        "android_endpoints": "Requieren API Key (/android/)",
        "react_endpoints": "Públicos sin API Key (/public/)",
        "message": "API con doble sistema de seguridad para Android y React"
    }

# Endpoint para verificar conexión simple
@app.get("/ping", tags=["Health"])
def ping():
    """Endpoint simple para verificar que la API está funcionando"""
    return {"message": "pong", "status": "online"}

# Endpoint para verificar API Key
@app.get("/verify-api-key", tags=["Security"])
def verify_api_key(api_key: str = Security(validate_api_key)):
    """Verifica si una API Key es válida"""
    return {
        "valid": True,
        "message": "API Key válida",
        "app_name": API_KEYS.get(api_key, "Desconocida"),
        "permissions": ["read:estudiantes", "write:estudiantes", "delete:estudiantes"]
    }

# Endpoint para developers - muestra información de uso
@app.get("/developer-info", tags=["Info"])
def developer_info():
    """Información para desarrolladores"""
    return {
        "api_structure": {
            "public_endpoints": {
                "get_estudiantes": "GET /public/estudiantes/",
                "create_estudiante": "POST /public/estudiantes/",
                "update_estudiante": "PUT /public/estudiantes/{id}",
                "delete_estudiante": "DELETE /public/estudiantes/{id}"
            },
            "android_endpoints": {
                "get_estudiantes": "GET /android/estudiantes/ (requiere API Key)",
                "get_estudiante": "GET /android/estudiantes/{id} (requiere API Key)",
                "create_estudiante": "POST /android/estudiantes/ (requiere API Key)",
                "update_estudiante": "PUT /android/estudiantes/{id} (requiere API Key)",
                "delete_estudiante": "DELETE /android/estudiantes/{id} (requiere API Key)"
            }
        },
        "api_keys": list(API_KEYS.keys()),
        "usage_examples": {
            "react_example": "fetch('/public/estudiantes/')",
            "android_example": "Request con header: X-API-Key: android_app_key_2025"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)