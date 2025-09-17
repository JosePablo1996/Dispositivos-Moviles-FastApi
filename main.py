from fastapi import FastAPI, HTTPException, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from urllib.parse import quote_plus
import os

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
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Definir el modelo de la base de datos para la tabla 'estudiantes'
class Estudiante(Base):
    __tablename__ = "estudiantes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), index=True)
    edad = Column(Integer)

# Crear las tablas en la base de datos si no existen
# Esto es útil para la configuración inicial. Si las tablas ya existen, no hace nada.
Base.metadata.create_all(bind=engine)

# Esquema Pydantic para validación de datos
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

# Inicializar la aplicación FastAPI
app = FastAPI(title="API de Estudiantes", version="1.0.0", description="Una API para gestionar información de estudiantes.")

# Configuración de CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

@app.get("/", tags=["Home"], summary="Saludo de la API")
def home():
    """
    Retorna un mensaje de bienvenida.
    """
    return {"message": "Bienvenido a la API de estudiantes!"}

@app.get("/estudiantes/", tags=["Estudiantes"], summary="Obtiene todos los estudiantes")
def obtener_estudiantes(db: Session = Depends(get_db)):
    """
    Obtiene la lista completa de todos los estudiantes registrados en la base de datos.
    """
    estudiantes = db.query(Estudiante).all()
    return [{"id": est.id, "nombre": est.nombre, "edad": est.edad} for est in estudiantes]

@app.get("/estudiantes/{id}", tags=["Estudiantes"], summary="Obtiene un estudiante por ID")
def obtener_estudiante_por_id(id: int = Path(..., description="ID del estudiante a obtener", ge=1), db: Session = Depends(get_db)):
    """
    Obtiene la información de un estudiante específico usando su ID.
    - **ID**: ID del estudiante
    """
    estudiante = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return {"id": estudiante.id, "nombre": estudiante.nombre, "edad": estudiante.edad}

@app.post("/estudiantes/", tags=["Estudiantes"], summary="Crea un nuevo estudiante")
def crear_estudiante(estudiante: EstudianteSchema, db: Session = Depends(get_db)):
    """
    Crea un nuevo estudiante en la base de datos.
    """
    db_estudiante = Estudiante(nombre=estudiante.nombre, edad=estudiante.edad)
    db.add(db_estudiante)
    db.commit()
    db.refresh(db_estudiante)
    return {"mensaje": "Estudiante creado exitosamente.", "estudiante": {"id": db_estudiante.id, "nombre": db_estudiante.nombre, "edad": db_estudiante.edad}}

@app.put("/estudiantes/{id}", tags=["Estudiantes"], summary="Modifica un estudiante existente")
def modificar_estudiante(id: int, estudiante: EstudianteSchema, db: Session = Depends(get_db)):
    """
    Modifica la información de un estudiante existente.
    """
    est = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    est.nombre = estudiante.nombre
    est.edad = estudiante.edad
    db.commit()
    db.refresh(est)
    return {"mensaje": "Estudiante actualizado.", "data": {"id": est.id, "nombre": est.nombre, "edad": est.edad}}

@app.delete("/estudiantes/{id}", tags=["Estudiantes"], summary="Elimina un estudiante")
def eliminar_estudiante(id: int, db: Session = Depends(get_db)):
    """
    Elimina un estudiante de la base de datos por ID.
    - **ID**: ID del estudiante
    """
    est = db.query(Estudiante).filter(Estudiante.id == id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    db.delete(est)
    db.commit()
    return {"mensaje": "Estudiante eliminado exitosamente."}