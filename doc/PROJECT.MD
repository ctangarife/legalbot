Objetivo: Desarrollar un chat generativo que permita a los usuarios interactuar con documentos legales provistos, obteniendo explicaciones claras y concisas en lenguaje natural, minimizando la jerga legal.

Tecnologías Clave:

Backend: Python (FastAPI)
Frontend: Vue3
Base de Datos de Documentos/Metadatos: MongoDB
Base de Datos Vectorial: Qdrant (recomendado por su balance entre rendimiento y facilidad de despliegue con Docker)
Modelo de Lenguaje (LLM): Ollama (para ejecución local/privada de LLMs)
Contenedores: Docker y Docker Compose
Flujo General (RAG):

Ingesta: Documentos legales se preprocesan (extracción de texto, segmentación, metadatos) y se almacenan en MongoDB.
Indexación: Los segmentos de texto se convierten en embeddings y se almacenan en Qdrant.
Consulta: El usuario pregunta en el frontend.
Recuperación (Retrieval): El backend convierte la pregunta en embedding, busca los segmentos más relevantes en Qdrant (filtrando por metadatos de MongoDB si es necesario).
Generación (Generation): Los segmentos recuperados se envían a Ollama (junto con la pregunta y un prompt de "sencillez") para generar la respuesta.
Respuesta: La respuesta (con citas) se muestra al usuario en el frontend.
Arquitectura de Despliegue con Docker Compose
Vamos a definir los servicios principales que correrán en contenedores Docker.

1. Servicios Principales
2. mongodb: Base de datos para almacenar el texto original de los documentos, sus metadatos y los IDs de los chunks.
3. ollama: Servidor para ejecutar modelos de lenguaje grandes (LLMs) de forma local.
4. backend: Aplicación Python (FastAPI) que orquesta todo:
5. API para ingesta de documentos.
6. API para el chat (recuperación + generación).
7. Conexión con MongoDB, Qdrant y Ollama.
8. frontend: Aplicación Vue3 que proporciona la interfaz de usuario para el chat.