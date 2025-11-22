# Guía de Pruebas - LegalBot

Esta guía te ayudará a verificar que todos los componentes del sistema funcionan correctamente.

## 1. Verificar que los servicios estén corriendo

### Iniciar todos los servicios

```bash
docker-compose up -d
```

### Verificar estado de los contenedores

```bash
docker-compose ps
```

Deberías ver todos los servicios con estado "Up":
- `legalbot-mongodb`
- `legalbot-qdrant`
- `legalbot-ollama`
- `legalbot-backend`
- `legalbot-frontend`
- `legalbot-nginx`

### Ver logs de un servicio específico

```bash
# Backend
docker-compose logs backend

# Frontend (build)
docker-compose logs frontend

# Nginx
docker-compose logs nginx

# Todos los servicios
docker-compose logs -f
```

## 2. Verificar Health Checks

### Health Check del Backend (a través de nginx)

```bash
curl http://localhost/api/health
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "mongodb": "connected"
}
```

### Health Check de Nginx

```bash
curl http://localhost:8080/nginx-health
```

**Respuesta esperada:**
```
healthy
```

### Verificar que el frontend está servido

```bash
curl http://localhost
```

Deberías recibir el HTML del frontend.

## 3. Verificar Ollama y Modelos

### Verificar que Ollama está corriendo

```bash
curl http://localhost:11434/api/tags
```

### Instalar el modelo Mistral (si no está instalado)

```bash
docker exec legalbot-ollama ollama pull mistral:7b-instruct
```

**Nota:** Esto puede tardar varios minutos dependiendo de tu conexión.

### Verificar modelos disponibles en la API

```bash
curl http://localhost/api/models
```

**Respuesta esperada:**
```json
{
  "models": ["mistral:7b-instruct", ...],
  "default": "mistral"
}
```

### Verificar un modelo específico

```bash
curl http://localhost/api/models/mistral:7b-instruct/check
```

## 4. Probar Subida de Documentos

### Subir un archivo PDF de prueba

```bash
curl -X POST http://localhost/api/upload \
  -F "files=@ruta/a/tu/documento.pdf" \
  -F "description=Documento de prueba"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "Archivo subido y procesado exitosamente (15 chunks)",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "documento.pdf",
  "file_size": 1024000,
  "uploaded_at": "2024-01-15T10:30:00.000000"
}
```

**Guarda el `file_id` para los siguientes pasos.**

### Listar documentos

```bash
curl http://localhost/api/documents
```

### Obtener información de un documento específico

```bash
curl http://localhost/api/documents/{file_id}
```

Reemplaza `{file_id}` con el ID que obtuviste al subir el archivo.

## 5. Probar el Chat (RAG)

### Hacer una pregunta sobre el documento

```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿De qué trata este documento?",
    "file_id": "TU_FILE_ID_AQUI",
    "max_chunks": 5
  }'
```

**Respuesta esperada:**
```json
{
  "answer": "Este documento trata sobre...",
  "sources": [
    {
      "chunk_id": "...",
      "text": "Fragmento del documento...",
      "score": 0.85
    }
  ],
  "model_used": "mistral:7b-instruct",
  "tokens_generated": 150
}
```

### Hacer una pregunta general (sin file_id)

```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es un contrato?",
    "max_chunks": 5
  }'
```

## 6. Probar desde el Frontend

### Acceder al frontend

Abre tu navegador y ve a:
```
http://localhost
```

### Probar funcionalidades desde la UI

1. **Subir documento**: Usa el botón de subir archivo y selecciona un PDF
2. **Ver documentos**: Verifica que aparezcan en la lista
3. **Chat**: Haz una pregunta sobre el documento subido
4. **Procesar documento**: Si un documento no está procesado, usa el botón de procesar

## 7. Verificar Logs para Debugging

### Logs del Backend

```bash
docker-compose logs -f backend
```

Busca errores relacionados con:
- Conexión a MongoDB
- Conexión a Qdrant
- Conexión a Ollama
- Procesamiento de documentos

### Logs de Nginx

```bash
docker-compose logs -f nginx
```

### Logs de Ollama

```bash
docker-compose logs -f ollama
```

## 8. Verificar Base de Datos

### Conectar a MongoDB

```bash
docker exec -it legalbot-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin
```

### Ver documentos en MongoDB

```javascript
use legalbot
db.documents.find().pretty()
```

### Verificar Qdrant (desde el navegador)

Abre:
```
http://localhost:6333/dashboard
```

Deberías ver la colección `legal_documents` con los puntos vectoriales.

## 9. Pruebas de Rendimiento

### Probar con múltiples documentos

```bash
curl -X POST http://localhost/api/upload/multiple \
  -F "files=@documento1.pdf" \
  -F "files=@documento2.pdf" \
  -F "files=@documento3.pdf"
```

### Probar búsqueda con diferentes parámetros

```bash
# Búsqueda con más chunks
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Pregunta de prueba",
    "max_chunks": 10,
    "temperature": 0.5
  }'
```

## 10. Solución de Problemas Comunes

### Error: "El modelo no está disponible"

```bash
# Instalar el modelo
docker exec legalbot-ollama ollama pull mistral:7b-instruct

# Verificar
docker exec legalbot-ollama ollama list
```

### Error: "MongoDB no está disponible"

```bash
# Verificar que MongoDB está corriendo
docker-compose ps mongodb

# Ver logs
docker-compose logs mongodb

# Reiniciar si es necesario
docker-compose restart mongodb
```

### Error: "Qdrant no está disponible"

```bash
# Verificar que Qdrant está corriendo
docker-compose ps qdrant

# Ver logs
docker-compose logs qdrant
```

### Frontend no carga

```bash
# Verificar que el frontend compiló correctamente
docker-compose logs frontend

# Recompilar el frontend
docker-compose up --build frontend

# Verificar que hay archivos en data/static/
ls -la data/static/
```

### El chat no responde

1. Verifica que Ollama tiene el modelo instalado
2. Verifica los logs del backend para ver errores
3. Prueba con una pregunta más corta
4. Verifica que hay documentos procesados en la base de datos

## 11. Pruebas Automatizadas (Opcional)

### Script de prueba básico

Crea un archivo `test.sh`:

```bash
#!/bin/bash

echo "1. Health Check..."
curl -s http://localhost/api/health | jq

echo -e "\n2. Listar modelos..."
curl -s http://localhost/api/models | jq

echo -e "\n3. Listar documentos..."
curl -s http://localhost/api/documents | jq

echo -e "\n4. Prueba de chat..."
curl -s -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Hola, ¿funcionas?"}' | jq
```

Ejecuta:
```bash
chmod +x test.sh
./test.sh
```

## Checklist de Verificación

- [ ] Todos los contenedores están corriendo
- [ ] Health check del backend responde OK
- [ ] Health check de nginx responde OK
- [ ] Frontend carga correctamente
- [ ] Ollama tiene el modelo instalado
- [ ] Puedo subir un documento
- [ ] El documento se procesa correctamente
- [ ] Puedo hacer preguntas en el chat
- [ ] Las respuestas incluyen fuentes (chunks)
- [ ] MongoDB almacena los documentos
- [ ] Qdrant almacena los embeddings

## Siguiente Paso

Una vez que todas las pruebas pasen, puedes comenzar a usar LegalBot con documentos reales. Si encuentras algún problema, revisa los logs y la sección de solución de problemas.

