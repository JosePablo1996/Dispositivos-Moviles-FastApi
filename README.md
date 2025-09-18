# 🚀 API REST para Gestión de Estudiantes - FastAPI

Una API RESTful desarrollada con FastAPI para la gestión integral de estudiantes, diseñada específicamente para aplicaciones móviles.

## 🛠️ Tecnologías Utilizadas

- **FastAPI**: Framework moderno y rápido para construir APIs con Python 3.7+
- **Python 3.13**: Versión más reciente de Python
- **SQLAlchemy**: ORM para interactuar con bases de datos
- **Pydantic**: Validación de datos y configuración mediante tipos Python
- **Docker**: Contenerización de la aplicación
- **JWT**: Autenticación mediante tokens Web
- **CORS**: Soporte para Cross-Origin Resource Sharing

## 📦 Estructura del Proyecto

Dispositivos-Moviles-FastApi/
├── venv/ # Entorno virtual de Python
├── pycache/ # Archivos compilados de Python
├── main.py # Punto de entrada principal de la API
├── main_BACKUP.py # Copia de seguridad del main
├── security.py # Módulo de seguridad y autenticación
├── fix_main.py # Utilidades para corrección del main
├── requirements.txt # Dependencias del proyecto
├── Dockerfile # Configuración para contenerización
├── .dockerignore # Archivos a ignorar en Docker
├── .env # Variables de entorno
├── .gitignore # Archivos a ignorar por Git
└── arbol_logo.png # Logo del proyecto (opcional)


## 🔌 Endpoints Disponibles

### Estudiantes
- `GET /estudiantes/` - Obtener lista de todos los estudiantes
- `GET /estudiantes/{id}` - Obtener estudiante por ID
- `POST /estudiantes/` - Crear nuevo estudiante
- `PUT /estudiantes/{id}` - Actualizar estudiante existente
- `DELETE /estudiantes/{id}` - Eliminar estudiante específico
- `DELETE /estudiantes/admin/delete-all` - Eliminar todos los estudiantes (admin)

### Autenticación
- `POST /token` - Obtener token JWT
- `POST /register` - Registrar nuevo usuario
- `GET /users/me` - Obtener información del usuario actual

## ⚙️ Configuración e Instalación

### Prerrequisitos
- Python 3.13+
- pip (gestor de paquetes de Python)
- Docker (opcional, para contenerización)

### Instalación Local
```bash
# Clonar el repositorio
git clone https://github.com/JosePablo1996/Dispositivos-Moviles-FastApi.git
cd Dispositivos-Moviles-FastApi

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Linux/Mac)
source venv/bin/activate

# Activar entorno virtual (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
uvicorn main:app --reload --host 0.0.0.0 --port 8000

Ejecución con Docker

# Construir la imagen
docker build -t estudiantes-api .

# Ejecutar el contenedor
docker run -d -p 8000:8000 --name estudiantes-container estudiantes-api

🚀 Uso de la API
Obtener todos los estudiantes

curl -X GET "http://localhost:8000/estudiantes/" \
  -H "Authorization: Bearer <TU_TOKEN_JWT>"

Crear un nuevo estudiante

curl -X POST "http://localhost:8000/estudiantes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TU_TOKEN_JWT>" \
  -d '{"nombre": "Juan Pérez", "edad": 22}'

Autenticación

# Obtener token
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

🔒 Seguridad

    Autenticación JWT: Todos los endpoints (excepto login/register) requieren token

    CORS habilitado: Configurado para aplicaciones móviles y web

    Validación de datos: Pydantic asegura la integridad de los datos

    Variables de entorno: Configuración sensible en archivo .env

📊 Modelos de Datos
Estudiante

class Estudiante(BaseModel):
    id: int
    nombre: str
    edad: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

Usuario

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

🐳 Dockerización

El proyecto incluye configuración completa para Docker:

FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

🌐 Despliegue

La API estará disponible en:

    Local: http://localhost:8000

    Documentación interactiva: http://localhost:8000/docs

    Documentación alternativa: http://localhost:8000/redoc

🧪 Testing

# Probar endpoints con curl o herramientas como:
# - Thunder Client (VS Code)
# - Postman
# - Insomnia

📝 Variables de Entorno

Crear archivo .env con:

DATABASE_URL=sqlite:///./estudiantes.db
SECRET_KEY=tu-clave-secreta-jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

🤝 Contribución

    1.Fork del proyecto

    2.Crear rama para feature (git checkout -b feature/AmazingFeature)

    3.Commit de cambios (git commit -m 'Add AmazingFeature')

    4.Push a la rama (git push origin feature/AmazingFeature)

📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.


👨‍💻 Autor
José Pablo - GitHub

Desarrollado para el curso de Dispositivos Móviles -2025_José Pablo Miranda Quintanilla



