# LegalBot

Chat generativo para interactuar con documentos legales, obteniendo explicaciones claras y concisas en lenguaje natural.

## Arquitectura

El proyecto utiliza una arquitectura RAG (Retrieval-Augmented Generation) con los siguientes componentes:

- **Backend**: FastAPI (Python)
- **Frontend**: Vue3
- **MongoDB**: Almacenamiento de documentos y metadatos
- **Qdrant**: Base de datos vectorial para embeddings
- **Ollama**: Servidor LLM local

## Servicios Docker

- `mongodb`: Base de datos de documentos
- `qdrant`: Base de datos vectorial
- `ollama`: Servidor LLM
- `backend`: API FastAPI
- `frontend`: Compilación de Vue3 a archivos estáticos
- `nginx`: Reverse proxy y servidor de archivos estáticos

## Inicio Rápido

1. Asegúrate de tener Docker y Docker Compose instalados

2. Configura las variables de entorno:
```bash
# Copia el archivo de ejemplo y ajusta los valores si es necesario
cp .env.example .env
```

3. Inicia los servicios:
```bash
docker-compose up -d
```

3. Accede a la aplicación:
   - Frontend (a través de nginx): http://localhost
   - Backend API (a través de nginx): http://localhost/api
   - API Docs: http://localhost/docs
   - Health Check: http://localhost/api/health

4. Para detener los servicios:
```bash
docker-compose down
```

## Estructura del Proyecto

```
legalbot/
├── data/
│   ├── backend/          # Código Python FastAPI
│   ├── frontend/         # Código fuente Vue3
│   ├── static/           # Archivos estáticos compilados (generados)
│   ├── nginx/            # Configuración de nginx
│   ├── logs/             # Logs de nginx
│   ├── mongodb/          # Datos de MongoDB
│   ├── qdrant/           # Datos de Qdrant
│   └── ollama/           # Datos de Ollama
├── build/
│   ├── backend/          # Dockerfile del backend
│   ├── frontend/         # Dockerfile del frontend
│   └── nginx/            # Dockerfile de nginx
├── doc/                  # Documentación
└── docker-compose.yml    # Orquestación de servicios
```

## Desarrollo

- **Backend**: El código se monta como volumen, permitiendo hot-reload durante el desarrollo.
- **Frontend**: Vue3 compila los archivos estáticos a `data/static/`, que nginx sirve directamente.
- **Nginx**: Actúa como reverse proxy para el backend y servidor de archivos estáticos para el frontend.

### Recompilar Frontend

Si realizas cambios en el frontend, puedes recompilar ejecutando:

```bash
docker-compose up frontend
```

O reconstruir y ejecutar:

```bash
docker-compose up --build frontend
```

