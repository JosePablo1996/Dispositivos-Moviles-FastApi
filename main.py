from fastapi import FastAPI, HTTPException, Path, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from urllib.parse import quote_plus
import os
import logging

# Importar seguridad
from security import validate_api_key, get_api_key

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

    # NO crear nuevas columnas para evitar conflictos
    # email y carrera se manejarán diferente

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

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="API de Gestión de Estudiantes",
    version="2.0.0",
    description="API para gestión de estudiantes con base de datos existente",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Endpoints públicos (no requieren API Key)
@app.get("/public-info", tags=["Info"])
def public_info():
    """Información pública sobre la API"""
    return {
        "api_name": "Gestión de Estudiantes API",
        "version": "2.0.0",
        "description": "API para gestión de estudiantes",
        "requires_api_key": True,
        "endpoints_protected": True,
        "api_key_required_for": ["/estudiantes", "/database-info"]
    }

# Endpoints protegidos (requieren API Key)
@app.get("/estudiantes/", response_model=list[EstudianteResponse], tags=["Estudiantes"])
def obtener_estudiantes(
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """Obtiene todos los estudiantes de la tabla existente (requiere API Key)"""
    estudiantes = db.query(Estudiante).order_by(Estudiante.id).all()
    return estudiantes

@app.get("/estudiantes/{id}", response_model=EstudianteResponse, tags=["Estudiantes"])
def obtener_estudiante_por_id(
    id: int = Path(..., ge=1), 
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """Obtiene un estudiante por ID (requiere API Key)"""
    estudiante = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante

@app.post("/estudiantes/", response_model=EstudianteResponse, tags=["Estudiantes"])
def crear_estudiante(
    estudiante: EstudianteSchema, 
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """Crea un nuevo estudiante en la tabla existente (requiere API Key)"""
    db_estudiante = Estudiante(nombre=estudiante.nombre, edad=estudiante.edad)
    db.add(db_estudiante)
    db.commit()
    db.refresh(db_estudiante)
    return db_estudiante

@app.put("/estudiantes/{id}", response_model=EstudianteResponse, tags=["Estudiantes"])
def modificar_estudiante(
    id: int, 
    estudiante: EstudianteSchema, 
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """Modifica un estudiante existente (requiere API Key)"""
    est = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    est.nombre = estudiante.nombre
    est.edad = estudiante.edad
    db.commit()
    db.refresh(est)
    return est

@app.delete("/estudiantes/{id}", tags=["Estudiantes"])
def eliminar_estudiante(
    id: int, 
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """Elimina un estudiante (requiere API Key)"""
    est = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    db.delete(est)
    db.commit()
    return {"mensaje": "Estudiante eliminado exitosamente"}

@app.get("/database-info", tags=["Debug"])
def database_info(
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """Información sobre la base de datos y tabla (requiere API Key)"""
    try:
        # Obtener información de la tabla
        result = db.execute(text("""
            SELECT COUNT(*) as total_estudiantes, 
                   MIN(id) as min_id, 
                   MAX(id) as max_id 
            FROM estudiantes
        """))
        stats = result.first()
        
        return {
            "database_name": "mq100216",
            "table_name": "estudiantes",
            "total_records": stats[0],
            "id_range": f"{stats[1]} - {stats[2]}",
            "columns": ["id", "nombre", "edad"],
            "api_version": "2.0.0",
            "security": "api_key_required"
        }
    except Exception as e:
        return {"error": str(e)}

# Nuevo endpoint para verificar API Key
@app.get("/verify-api-key", tags=["Security"])
def verify_api_key(api_key: str = Security(get_api_key)):
    """Verifica si una API Key es válida"""
    return {
        "valid": True,
        "message": "API Key válida",
        "permissions": ["read:estudiantes", "write:estudiantes", "delete:estudiantes"]
    }