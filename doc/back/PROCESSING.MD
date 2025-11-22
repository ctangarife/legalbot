# Procesamiento de Documentos - Arquitectura

## Flujo de Procesamiento

El procesamiento de documentos PDF sigue estos pasos:

1. **Extracción de Texto**: Extraer texto del PDF usando PyMuPDF (fitz)
2. **Segmentación**: Dividir el texto en chunks de tamaño adecuado con overlap
3. **Generación de Embeddings**: Convertir cada chunk en un vector usando sentence-transformers
4. **Almacenamiento en Qdrant**: Guardar los embeddings con metadatos en Qdrant
5. **Actualización en MongoDB**: Actualizar el documento con los IDs de chunks y estado

## Componentes

### 1. Document Processor (`document_processor.py`)

Responsable de:
- Extracción de texto de PDFs
- Segmentación inteligente del texto
- Manejo de diferentes formatos (PDF, DOCX, TXT, MD)

### 2. Qdrant Client (`qdrant_client.py`)

Responsable de:
- Conexión con Qdrant
- Creación de colecciones
- Almacenamiento de embeddings con metadatos
- Búsqueda vectorial

### 3. Embedding Generator

Usa `sentence-transformers` con un modelo pre-entrenado:
- Modelo recomendado: `all-MiniLM-L6-v2` (ligero y rápido)
- Alternativa: `paraphrase-multilingual-MiniLM-L12-v2` (multilingüe)

## Parámetros de Segmentación

- **Chunk Size**: 500-1000 caracteres (configurable)
- **Overlap**: 100-200 caracteres entre chunks
- **Estrategia**: Por párrafos cuando sea posible, luego por oraciones

## Metadatos en Qdrant

Cada punto vectorial incluye:
- `file_id`: ID del documento origen
- `chunk_id`: ID único del chunk
- `chunk_index`: Índice del chunk en el documento
- `text`: Texto original del chunk
- `filename`: Nombre del archivo
- `file_type`: Tipo de archivo

## Estados del Documento

- `uploaded`: Archivo subido, listo para procesar
- `processing`: En proceso de extracción y segmentación
- `processed`: Procesado y listo para consultas
- `error`: Error durante el procesamiento

## Endpoint de Procesamiento

### POST /api/documents/{file_id}/process

Este endpoint inicia el procesamiento completo de un documento:

1. **Verificación**: Verifica que el documento existe y no esté ya procesado
2. **Estado inicial**: Actualiza el estado a `processing`
3. **Extracción**: Extrae texto del archivo según su tipo (PDF, DOCX, TXT, MD)
4. **Segmentación**: Divide el texto en chunks con overlap
5. **Embeddings**: Genera embeddings para cada chunk usando sentence-transformers
6. **Almacenamiento**: Guarda embeddings en Qdrant con metadatos
7. **Actualización**: Actualiza MongoDB con los IDs de chunks y estado `processed`

### Manejo de Errores

- Si el documento no existe: retorna 404
- Si ya está procesado: retorna información sin reprocesar
- Si está en proceso: retorna 409 Conflict
- Si falla cualquier paso: actualiza estado a `error` en MongoDB

### Ejemplo de Flujo

```python
# 1. Subir archivo
upload_response = POST /api/upload
file_id = upload_response.file_id  # "550e8400-..."

# 2. Procesar documento
process_response = POST /api/documents/{file_id}/process
# Retorna: { "chunks_count": 15, "success": true }

# 3. Verificar estado
document = GET /api/documents/{file_id}
# document.status = "processed"
# document.chunks_count = 15
```

## Bibliotecas Utilizadas

- **PyMuPDF (fitz)**: Extracción de texto de PDFs
- **python-docx**: Extracción de texto de documentos Word
- **sentence-transformers**: Generación de embeddings
- **qdrant-client**: Almacenamiento vectorial
- **motor**: Cliente asíncrono de MongoDB

