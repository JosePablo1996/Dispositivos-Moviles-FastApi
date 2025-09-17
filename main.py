from fastapi import FastAPI, HTTPException, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from urllib.parse import quote_plus
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la contraseña de variable de entorno o usar la predeterminada
PASSWORD = os.getenv("DB_PASSWORD", "uPxBHn]Ag9H~N4'K")

# Codificar la contraseña para la URL
ENCODED_PASSWORD = quote_plus(PASSWORD)

# Usar variable de entorno para la URL de la base de datos con fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://postgres:{ENCODED_PASSWORD}@20.84.99.214:443/mq100216"
)

# Configuración de la base de datos con SQLAlchemy
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base = declarative_base()
    logger.info("Conexión a la base de datos configurada exitosamente")
except Exception as e:
    logger.error(f"Error al configurar la base de datos: {e}")
    raise

# Definir el modelo de la base de datos para la tabla 'estudiantes'
class Estudiante(Base):
    __tablename__ = "estudiantes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), index=True)
    edad = Column(Integer)
    email = Column(String(100), unique=True, nullable=True)  # Nuevo campo
    carrera = Column(String(100), nullable=True)  # Nuevo campo

# Crear las tablas en la base de datos si no existen
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas de la base de datos verificadas/creadas")
except Exception as e:
    logger.error(f"Error al crear tablas: {e}")

# Esquema Pydantic para validación de datos
class EstudianteSchema(BaseModel):
    nombre: str
    edad: int
    email: str = None  # Nuevo campo opcional
    carrera: str = None  # Nuevo campo opcional

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "edad": 25,
                "email": "juan@email.com",
                "carrera": "Ingeniería en Sistemas"
            }
        }

class EstudianteUpdateSchema(BaseModel):
    nombre: str = None
    edad: int = None
    email: str = None
    carrera: str = None

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="API de Gestión de Estudiantes",
    version="2.0.0",
    description="API completa para gestión de información estudiantil con PostgreSQL",
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

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Rutas de la API
@app.get("/", tags=["Home"], summary="Saludo de la API")
def home():
    return {"message": "Bienvenido a la API de estudiantes!", "version": "2.0.0"}

@app.get("/estudiantes/", tags=["Estudiantes"], summary="Obtiene todos los estudiantes")
def obtener_estudiantes(db: Session = Depends(get_db)):
    estudiantes = db.query(Estudiante).all()
    return {
        "count": len(estudiantes),
        "estudiantes": [
            {
                "id": est.id, 
                "nombre": est.nombre, 
                "edad": est.edad,
                "email": est.email,
                "carrera": est.carrera
            } for est in estudiantes
        ]
    }

@app.get("/estudiantes/{id}", tags=["Estudiantes"], summary="Obtiene un estudiante por ID")
def obtener_estudiante_por_id(id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    estudiante = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante

@app.post("/estudiantes/", tags=["Estudiantes"], summary="Crea un nuevo estudiante")
def crear_estudiante(estudiante: EstudianteSchema, db: Session = Depends(get_db)):
    # Verificar si el email ya existe
    if estudiante.email:
        existing = db.query(Estudiante).filter(Estudiante.email == estudiante.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    db_estudiante = Estudiante(**estudiante.dict())
    db.add(db_estudiante)
    db.commit()
    db.refresh(db_estudiante)
    return {
        "mensaje": "Estudiante creado exitosamente",
        "estudiante": db_estudiante
    }

@app.put("/estudiantes/{id}", tags=["Estudiantes"], summary="Modifica un estudiante existente")
def modificar_estudiante(id: int, estudiante: EstudianteUpdateSchema, db: Session = Depends(get_db)):
    est = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Actualizar solo los campos proporcionados
    update_data = estudiante.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(est, field, value)
    
    db.commit()
    db.refresh(est)
    return {
        "mensaje": "Estudiante actualizado",
        "estudiante": est
    }

@app.delete("/estudiantes/{id}", tags=["Estudiantes"], summary="Elimina un estudiante")
def eliminar_estudiante(id: int, db: Session = Depends(get_db)):
    est = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    db.delete(est)
    db.commit()
    return {"mensaje": "Estudiante eliminado exitosamente"}

# Nueva ruta para health check
@app.get("/health", tags=["Health"], summary="Verifica el estado de la API")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "version": "2.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Manejo de excepciones global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Error interno del servidor"}
    )