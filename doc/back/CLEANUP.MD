# Limpieza de Bases de Datos - LegalBot

## ⚠️ Importante

Las operaciones de limpieza **NO están disponibles como endpoints públicos** por razones de seguridad. Solo se pueden ejecutar desde dentro del contenedor Docker del backend.

## Requisitos

- Acceso al contenedor Docker del backend
- Permisos para ejecutar comandos dentro del contenedor

## Uso del Script de Limpieza

El script `cleanup.py` está ubicado en `/app/cleanup.py` dentro del contenedor del backend.

### Ver Ayuda

```bash
docker exec -it legalbot-backend-1 python cleanup.py --help
```

### Opciones Disponibles

#### 1. Eliminar un Documento Específico

Elimina un documento de MongoDB, Qdrant y el sistema de archivos.

```bash
docker exec -it legalbot-backend-1 python cleanup.py --document <file_id>
```

**Ejemplo:**
```bash
docker exec -it legalbot-backend-1 python cleanup.py --document 550e8400-e29b-41d4-a716-446655440000
```

#### 2. Eliminar Todos los Documentos

⚠️ **ADVERTENCIA:** Esta operación elimina TODOS los documentos de MongoDB, Qdrant y el sistema de archivos. Es **irreversible**.

```bash
docker exec -it legalbot-backend-1 python cleanup.py --all --confirm
```

**Nota:** El flag `--confirm` es obligatorio para operaciones destructivas.

#### 3. Limpiar Solo MongoDB

Elimina todos los documentos de MongoDB sin tocar archivos ni Qdrant.

```bash
docker exec -it legalbot-backend-1 python cleanup.py --mongodb-only --confirm
```

**Nota:** Los archivos físicos y vectores en Qdrant NO serán eliminados.

#### 4. Limpiar Solo Qdrant

Elimina todos los vectores/embeddings de Qdrant sin tocar MongoDB ni archivos.

```bash
docker exec -it legalbot-backend-1 python cleanup.py --qdrant-only --confirm
```

**Nota:** Los documentos en MongoDB y los archivos físicos NO serán eliminados.

## Ejemplos de Uso

### Caso 1: Limpiar Todo para Empezar de Nuevo

```bash
# Eliminar todos los documentos (MongoDB + Qdrant + archivos)
docker exec -it legalbot-backend-1 python cleanup.py --all --confirm
```

### Caso 2: Eliminar un Documento Específico

Primero, obtén el `file_id` del documento usando el endpoint `GET /api/documents`:

```bash
# Obtener lista de documentos
curl http://localhost/api/documents

# Eliminar documento específico
docker exec -it legalbot-backend-1 python cleanup.py --document <file_id>
```

### Caso 3: Limpiar Solo los Embeddings (Qdrant)

Si necesitas regenerar los embeddings pero mantener los documentos:

```bash
# Limpiar solo Qdrant
docker exec -it legalbot-backend-1 python cleanup.py --qdrant-only --confirm

# Luego reprocesar los documentos usando el endpoint POST /api/documents/{file_id}/process
```

### Caso 4: Limpiar Solo Metadatos (MongoDB)

Si necesitas limpiar los metadatos pero mantener los archivos y embeddings:

```bash
docker exec -it legalbot-backend-1 python cleanup.py --mongodb-only --confirm
```

## Salida del Script

El script muestra información detallada sobre las operaciones realizadas:

```
2024-01-15 10:30:00 - __main__ - INFO - Conectado a MongoDB
2024-01-15 10:30:01 - __main__ - INFO - Eliminando documento: documento.pdf (550e8400-...)
2024-01-15 10:30:01 - __main__ - INFO - ✓ Archivo eliminado: /app/uploads/550e8400-....pdf
2024-01-15 10:30:02 - __main__ - INFO - ✓ Vectores eliminados de Qdrant
2024-01-15 10:30:02 - __main__ - INFO - ✓ Documento eliminado de MongoDB
2024-01-15 10:30:02 - __main__ - INFO - ✓ Operación completada exitosamente
```

## Seguridad

- ✅ Solo se puede ejecutar desde dentro del contenedor
- ✅ Requiere confirmación explícita (`--confirm`) para operaciones destructivas
- ✅ No está expuesto como endpoint público
- ✅ Muestra advertencias claras antes de operaciones destructivas

## Troubleshooting

### Error: "MongoDB no está disponible"

Verifica que el contenedor de MongoDB esté corriendo:

```bash
docker ps | grep mongodb
```

### Error: "Qdrant no está disponible"

Verifica que el contenedor de Qdrant esté corriendo:

```bash
docker ps | grep qdrant
```

### Error: "Archivo no existe"

Es normal si el archivo ya fue eliminado manualmente. El script continuará eliminando los registros de MongoDB y Qdrant.

### Error: "No se pudo eliminar los vectores de Qdrant"

Verifica la conexión con Qdrant y que el `file_id` sea correcto.

## Notas para el Frontend

**IMPORTANTE:** El frontend NO puede limpiar las bases de datos directamente. Si necesitas implementar una funcionalidad de limpieza en el UI, deberías:

1. **NO crear endpoints públicos** de limpieza
2. **Sí crear una interfaz administrativa** que ejecute comandos Docker (requiere acceso SSH/shell)
3. **O crear un endpoint protegido con autenticación fuerte** (solo para administradores)

Para desarrollo/testing, los desarrolladores pueden usar el script directamente desde la terminal.

