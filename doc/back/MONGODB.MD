# MongoDB - Documentación Técnica

## Configuración

### Variables de Entorno

- `MONGODB_URL`: URL de conexión a MongoDB (default: `mongodb://admin:admin123@mongodb:27017/?authSource=admin`)
- `MONGODB_DATABASE`: Nombre de la base de datos (default: `legalbot`)

### Conexión

La conexión a MongoDB se establece automáticamente al iniciar la aplicación FastAPI usando el módulo `database.py`. Se utiliza `motor` (AsyncIOMotorClient) para operaciones asíncronas.

## Estructura de la Base de Datos

### Base de Datos: `legalbot`

### Colección: `documents`

Almacena la información de los documentos legales subidos.

#### Esquema del Documento

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "documento.pdf",
  "file_size": 1024000,
  "file_path": "/app/uploads/550e8400-e29b-41d4-a716-446655440000.pdf",
  "file_type": ".pdf",
  "description": "Documento legal importante",
  "status": "uploaded",
  "uploaded_at": ISODate("2024-01-15T10:30:00.000Z"),
  "processed_at": null,
  "chunks": [],
  "metadata": {}
}
```

#### Campos

- **`_id`** (ObjectId): ID único de MongoDB
- **`file_id`** (string, único): UUID único del archivo (índice único)
- **`filename`** (string): Nombre original del archivo (índice)
- **`file_size`** (int): Tamaño del archivo en bytes
- **`file_path`** (string): Ruta del archivo en el servidor
- **`file_type`** (string): Extensión del archivo (.pdf, .docx, etc.)
- **`description`** (string, opcional): Descripción del documento
- **`status`** (string): Estado del documento (índice)
  - `uploaded`: Subido pero no procesado
  - `processing`: En proceso de extracción
  - `processed`: Procesado y listo
  - `error`: Error en el procesamiento
- **`uploaded_at`** (datetime): Fecha de subida (índice)
- **`processed_at`** (datetime, opcional): Fecha de procesamiento
- **`chunks`** (array de strings): IDs de los chunks generados (para referencia con Qdrant)
- **`metadata`** (object): Metadatos adicionales del documento

#### Índices

Los siguientes índices se crean automáticamente:

1. **`file_id`**: Índice único para búsquedas rápidas por UUID
2. **`filename`**: Índice para búsquedas por nombre
3. **`uploaded_at`**: Índice para ordenamiento por fecha
4. **`status`**: Índice para filtros por estado

## Operaciones

### Guardar Documento

Después de subir un archivo, se guarda automáticamente en MongoDB usando la función `save_document_to_mongo()` en `main.py`.

### Listar Documentos

```python
# Ejemplo de query
documents = await db.documents.find({"status": "uploaded"}).sort("uploaded_at", -1).skip(0).limit(50)
```

### Obtener Documento por file_id

```python
document = await db.documents.find_one({"file_id": file_id})
```

### Actualizar Estado

```python
await db.documents.update_one(
    {"file_id": file_id},
    {"$set": {"status": "processed", "processed_at": datetime.utcnow()}}
)
```

## Integración con Qdrant

Los documentos en MongoDB se relacionan con los embeddings en Qdrant a través del campo `chunks`, que contiene los IDs de los puntos vectoriales en Qdrant. Esto permite:

1. Recuperar el texto original desde MongoDB usando los IDs de chunks
2. Mantener metadatos del documento junto con los embeddings
3. Filtrar documentos por estado antes de buscar en Qdrant

## Manejo de Errores

- Si MongoDB no está disponible al iniciar, la aplicación continúa funcionando pero no guarda documentos
- Los errores de MongoDB se registran en los logs pero no interrumpen el flujo de subida de archivos
- El endpoint `/api/health` verifica la conexión con MongoDB

## Próximas Mejoras

- Implementar procesamiento de documentos (extracción de texto, segmentación)
- Guardar chunks de texto en MongoDB con referencias a Qdrant
- Implementar búsqueda full-text en MongoDB
- Agregar índices adicionales para optimizar consultas

