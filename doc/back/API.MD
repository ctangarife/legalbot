# API LegalBot - Documentación para Frontend

Esta documentación describe cómo consumir los endpoints de la API LegalBot desde el frontend.

## Base URL

```
http://localhost/api
```

**Nota:** En desarrollo, si accedes directamente al backend sin nginx:
```
http://localhost:8000
```

## Autenticación

Actualmente la API no requiere autenticación. En futuras versiones se implementará JWT.

## Endpoints Disponibles

### 1. Health Check

Verifica el estado de la API.

**Endpoint:** `GET /api/health`

**Respuesta Exitosa:**
```json
{
  "status": "ok"
}
```

**Ejemplo de uso (JavaScript/Vue):**
```javascript
const response = await fetch('/api/health');
const data = await response.json();
console.log(data.status); // "ok"
```

---

### 2. Subir Archivo Único

Sube un archivo legal (PDF, DOCX, TXT, MD) al servidor.

**Endpoint:** `POST /api/upload`

**Content-Type:** `multipart/form-data`

**Parámetros:**
- `files` (File[], requerido): Lista de archivos a subir (se procesa solo el primero)
- `description` (String, opcional): Descripción del documento

**Nota:** Aunque acepta una lista, este endpoint procesa solo el primer archivo y devuelve un objeto único. Para subir múltiples archivos y obtener todos los resultados, usa `/api/upload/multiple`.

**Tipos de archivo permitidos:**
- `.pdf`
- `.docx`
- `.doc`
- `.txt`
- `.md`

**Límite de tamaño:** 50MB por archivo

**Respuesta Exitosa (200):**
```json
{
  "success": true,
  "message": "Archivo subido exitosamente",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "documento.pdf",
  "file_size": 1024000,
  "uploaded_at": "2024-01-15T10:30:00.000000"
}
```

**Errores Posibles:**

- **400 Bad Request:** No se proporcionó ningún archivo
```json
{
  "detail": "No se proporcionó ningún archivo"
}
```

- **400 Bad Request:** Tipo de archivo no permitido
```json
{
  "detail": "Tipo de archivo no permitido. Extensiones permitidas: .pdf, .docx, .doc, .txt, .md"
}
```

- **400 Bad Request:** Archivo demasiado grande
```json
{
  "detail": "Archivo demasiado grande. Tamaño máximo: 50MB"
}
```

- **409 Conflict:** Archivo duplicado (mismo contenido ya subido)
```json
{
  "detail": {
    "error": "Archivo duplicado",
    "message": "Este archivo ya ha sido subido anteriormente como 'documento.pdf'",
    "existing_file_id": "550e8400-e29b-41d4-a716-446655440000",
    "existing_filename": "documento.pdf",
    "uploaded_at": "2024-01-15T10:30:00.000000"
  }
}
```

**Nota sobre duplicados:** El sistema detecta archivos duplicados comparando el hash SHA-256 del contenido. Si intentas subir un archivo con el mismo contenido (aunque tenga diferente nombre), recibirás un error 409 Conflict con información del archivo original.

- **500 Internal Server Error:** Error al procesar el archivo
```json
{
  "detail": "Error al subir archivo: [mensaje de error]"
}
```

**Ejemplo de uso (JavaScript/Vue):**

```javascript
// Método 1: Usando FormData
async function uploadFile(file, description = null) {
  const formData = new FormData();
  formData.append('files', file); // Nota: usa 'files' (plural)
  if (description) {
    formData.append('description', description);
  }

  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al subir archivo');
    }

    const data = await response.json();
    console.log('Archivo subido:', data);
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Uso en componente Vue
const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const result = await uploadFile(file, 'Documento legal importante');
    console.log('File ID:', result.file_id);
    // Guardar file_id para procesamiento posterior
  } catch (error) {
    alert('Error al subir archivo: ' + error.message);
  }
};
```

**Ejemplo con axios (Vue):**

```javascript
import axios from 'axios';

async function uploadFileWithAxios(file, description = null) {
  const formData = new FormData();
  formData.append('files', file); // Nota: usa 'files' (plural)
  if (description) {
    formData.append('description', description);
  }

  try {
    const response = await axios.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.detail || 'Error al subir archivo');
    }
    throw error;
  }
}
```

---

### 3. Subir Múltiples Archivos

Sube varios archivos en una sola petición.

**Endpoint:** `POST /api/upload/multiple`

**Content-Type:** `multipart/form-data`

**Parámetros:**
- `files` (File[], requerido): Array de archivos a subir

**Respuesta Exitosa (200):**
```json
[
  {
    "success": true,
    "message": "Archivo subido exitosamente",
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "documento1.pdf",
    "file_size": 1024000,
    "uploaded_at": "2024-01-15T10:30:00.000000"
  },
  {
    "success": true,
    "message": "Archivo subido exitosamente",
    "file_id": "660e8400-e29b-41d4-a716-446655440001",
    "filename": "documento2.docx",
    "file_size": 2048000,
    "uploaded_at": "2024-01-15T10:30:01.000000"
  },
  {
    "success": false,
    "message": "Tipo de archivo no permitido: archivo.exe",
    "file_id": null,
    "filename": "archivo.exe"
  }
]
```

**Ejemplo de uso (JavaScript/Vue):**

```javascript
async function uploadMultipleFiles(files) {
  const formData = new FormData();
  
  // Agregar todos los archivos
  Array.from(files).forEach(file => {
    formData.append('files', file);
  });

  try {
    const response = await fetch('/api/upload/multiple', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('Error al subir archivos');
    }

    const results = await response.json();
    
    // Filtrar resultados exitosos
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);
    
    console.log(`${successful.length} archivos subidos exitosamente`);
    if (failed.length > 0) {
      console.warn(`${failed.length} archivos fallaron:`, failed);
    }
    
    return results;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Uso en componente Vue con input múltiple
const handleMultipleFiles = async (event) => {
  const files = event.target.files;
  if (files.length === 0) return;

  try {
    const results = await uploadMultipleFiles(files);
    // Procesar resultados
    results.forEach(result => {
      if (result.success) {
        console.log(`Archivo ${result.filename} subido con ID: ${result.file_id}`);
      }
    });
  } catch (error) {
    alert('Error al subir archivos: ' + error.message);
  }
};
```

---

## Ejemplo Completo en Componente Vue 3

```vue
<template>
  <div class="file-upload">
    <h2>Subir Documentos Legales</h2>
    
    <!-- Subida única -->
    <div class="upload-section">
      <h3>Subir un archivo</h3>
      <input 
        type="file" 
        @change="handleSingleFile"
        accept=".pdf,.docx,.doc,.txt,.md"
      />
      <input 
        v-model="description" 
        type="text" 
        placeholder="Descripción (opcional)"
      />
      <button @click="uploadSingle" :disabled="!selectedFile || uploading">
        {{ uploading ? 'Subiendo...' : 'Subir Archivo' }}
      </button>
    </div>

    <!-- Subida múltiple -->
    <div class="upload-section">
      <h3>Subir múltiples archivos</h3>
      <input 
        type="file" 
        multiple
        @change="handleMultipleFiles"
        accept=".pdf,.docx,.doc,.txt,.md"
      />
      <button @click="uploadMultiple" :disabled="selectedFiles.length === 0 || uploading">
        {{ uploading ? 'Subiendo...' : `Subir ${selectedFiles.length} archivos` }}
      </button>
    </div>

    <!-- Resultados -->
    <div v-if="results.length > 0" class="results">
      <h3>Resultados:</h3>
      <div v-for="(result, index) in results" :key="index" :class="result.success ? 'success' : 'error'">
        <p>{{ result.filename }}: {{ result.message }}</p>
        <p v-if="result.file_id">ID: {{ result.file_id }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const selectedFile = ref(null);
const selectedFiles = ref([]);
const description = ref('');
const uploading = ref(false);
const results = ref([]);

const handleSingleFile = (event) => {
  selectedFile.value = event.target.files[0];
};

const handleMultipleFiles = (event) => {
  selectedFiles.value = Array.from(event.target.files);
};

const uploadSingle = async () => {
  if (!selectedFile.value) return;
  
  uploading.value = true;
  results.value = [];

  try {
    const formData = new FormData();
    formData.append('files', selectedFile.value); // Nota: usa 'files' (plural)
    if (description.value) {
      formData.append('description', description.value);
    }

    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al subir archivo');
    }

    const data = await response.json();
    results.value = [data];
    selectedFile.value = null;
    description.value = '';
  } catch (error) {
    results.value = [{
      success: false,
      message: error.message,
      filename: selectedFile.value?.name
    }];
  } finally {
    uploading.value = false;
  }
};

const uploadMultiple = async () => {
  if (selectedFiles.value.length === 0) return;
  
  uploading.value = true;
  results.value = [];

  try {
    const formData = new FormData();
    selectedFiles.value.forEach(file => {
      formData.append('files', file);
    });

    const response = await fetch('/api/upload/multiple', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('Error al subir archivos');
    }

    const data = await response.json();
    results.value = data;
    selectedFiles.value = [];
  } catch (error) {
    results.value = [{
      success: false,
      message: error.message
    }];
  } finally {
    uploading.value = false;
  }
};
</script>

<style scoped>
.file-upload {
  padding: 20px;
}

.upload-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.results {
  margin-top: 20px;
}

.success {
  color: green;
  padding: 10px;
  background-color: #f0f9f0;
  margin-bottom: 10px;
  border-radius: 4px;
}

.error {
  color: red;
  padding: 10px;
  background-color: #fff0f0;
  margin-bottom: 10px;
  border-radius: 4px;
}
</style>
```

---

## Manejo de Errores

Siempre maneja los errores apropiadamente:

```javascript
async function safeUpload(file) {
  try {
    const formData = new FormData();
    formData.append('files', file); // Nota: usa 'files' (plural)

    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      
      // Manejar diferentes tipos de errores
      if (response.status === 400) {
        // Error de validación
        throw new Error(`Validación fallida: ${errorData.detail}`);
      } else if (response.status === 500) {
        // Error del servidor
        throw new Error(`Error del servidor: ${errorData.detail}`);
      } else {
        throw new Error(`Error desconocido: ${errorData.detail}`);
      }
    }

    return await response.json();
  } catch (error) {
    // Error de red u otro error
    console.error('Error en la petición:', error);
    throw error;
  }
}
```

---

## Notas Importantes

1. **Tamaño de archivo:** El límite máximo es de 50MB por archivo. Nginx está configurado para aceptar hasta 50MB en rutas generales y 100MB en `/api/documents`.

2. **File ID:** Cada archivo subido recibe un `file_id` único (UUID). Guarda este ID para referenciar el archivo en futuras operaciones (procesamiento, indexación, etc.).

3. **Almacenamiento temporal:** Los archivos se almacenan en `/app/uploads` dentro del contenedor. En futuras versiones se implementará el procesamiento automático y almacenamiento en MongoDB.

4. **CORS:** La API está configurada para aceptar peticiones desde `http://localhost:3000` y `http://localhost:80`.

5. **Rate Limiting:** Nginx tiene rate limiting configurado:
   - API general: 30 requests/segundo
   - Chat: 5 requests/segundo
   - Documentos: 30 requests/segundo con burst de 5

---

---

### 4. Listar Documentos

Obtiene la lista de documentos almacenados en MongoDB.

**Endpoint:** `GET /api/documents`

**Parámetros de Query:**
- `skip` (int, opcional): Número de documentos a saltar (paginación). Default: 0
- `limit` (int, opcional): Número máximo de documentos a retornar. Default: 50, Máximo: 100
- `status` (string, opcional): Filtrar por estado. Valores: `uploaded`, `processing`, `processed`, `error`

**Respuesta Exitosa (200):**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "documento.pdf",
    "file_size": 1024000,
    "file_type": ".pdf",
    "description": "Documento legal importante",
    "status": "uploaded",
    "uploaded_at": "2024-01-15T10:30:00.000000",
    "processed_at": null,
    "chunks_count": 0,
    "metadata": {}
  }
]
```

**Ejemplo de uso (JavaScript/Vue):**
```javascript
async function listDocuments(skip = 0, limit = 50, status = null) {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString()
  });
  
  if (status) {
    params.append('status', status);
  }

  try {
    const response = await fetch(`/api/documents?${params}`);
    if (!response.ok) {
      throw new Error('Error al listar documentos');
    }
    const documents = await response.json();
    return documents;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Uso
const documents = await listDocuments(0, 20, 'uploaded');
```

---

### 5. Obtener Documento por ID

Obtiene la información detallada de un documento específico.

**Endpoint:** `GET /api/documents/{file_id}`

**Parámetros de Ruta:**
- `file_id` (string, requerido): ID único del archivo (UUID)

**Respuesta Exitosa (200):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "documento.pdf",
  "file_size": 1024000,
  "file_type": ".pdf",
  "description": "Documento legal importante",
  "status": "uploaded",
  "uploaded_at": "2024-01-15T10:30:00.000000",
  "processed_at": null,
  "chunks_count": 0,
  "metadata": {}
}
```

**Errores Posibles:**

- **404 Not Found:** Documento no encontrado
```json
{
  "detail": "Documento con file_id 550e8400-e29b-41d4-a716-446655440000 no encontrado"
}
```

- **503 Service Unavailable:** MongoDB no está disponible
```json
{
  "detail": "MongoDB no está disponible"
}
```

**Ejemplo de uso (JavaScript/Vue):**
```javascript
async function getDocument(fileId) {
  try {
    const response = await fetch(`/api/documents/${fileId}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Documento no encontrado');
      }
      throw new Error('Error al obtener documento');
    }
    const document = await response.json();
    return document;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Uso
const document = await getDocument('550e8400-e29b-41d4-a716-446655440000');
```

---

## Proceso Post-Subida

Después de subir un archivo exitosamente, el backend automáticamente:

1. **Guarda el archivo físicamente** en `/app/uploads/` con un nombre único basado en el `file_id`
2. **Registra la información en MongoDB** con los siguientes datos:
   - `file_id`: UUID único del archivo
   - `filename`: Nombre original del archivo
   - `file_size`: Tamaño en bytes
   - `file_path`: Ruta del archivo en el servidor
   - `file_type`: Extensión del archivo
   - `description`: Descripción opcional (si se proporcionó)
   - `status`: Estado inicial `"uploaded"`
   - `uploaded_at`: Fecha y hora de subida
   - `chunks`: Lista vacía inicialmente (se llenará después del procesamiento)
   - `metadata`: Diccionario vacío para metadatos adicionales

**Estados de Documento:**
- `uploaded`: Archivo subido pero aún no procesado
- `processing`: Archivo en proceso de extracción y segmentación
- `processed`: Archivo procesado y listo para consultas
- `error`: Error durante el procesamiento

---

---

### 6. Procesar Documento

Procesa un documento subido: extrae texto, lo segmenta en chunks, genera embeddings y los almacena en Qdrant.

**Endpoint:** `POST /api/documents/{file_id}/process`

**Parámetros de Ruta:**
- `file_id` (string, requerido): ID único del archivo (UUID)

**Respuesta Exitosa (200):**
```json
{
  "success": true,
  "message": "Documento procesado exitosamente",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks_count": 15,
  "processed_at": "2024-01-15T10:35:00.000000"
}
```

**Errores Posibles:**

- **404 Not Found:** Documento no encontrado
```json
{
  "detail": "Documento con file_id 550e8400-e29b-41d4-a716-446655440000 no encontrado"
}
```

- **409 Conflict:** Documento ya está en proceso
```json
{
  "detail": "Documento ya está en proceso"
}
```

- **400 Bad Request:** No se pudo extraer texto
```json
{
  "detail": "No se pudo extraer texto del documento"
}
```

- **503 Service Unavailable:** MongoDB no está disponible
```json
{
  "detail": "MongoDB no está disponible"
}
```

**Ejemplo de uso (JavaScript/Vue):**
```javascript
async function processDocument(fileId) {
  try {
    const response = await fetch(`/api/documents/${fileId}/process`, {
      method: 'POST'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al procesar documento');
    }

    const result = await response.json();
    console.log(`Documento procesado: ${result.chunks_count} chunks creados`);
    return result;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Uso después de subir un archivo
const uploadResult = await uploadFile(file);
if (uploadResult.success) {
  // Procesar inmediatamente después de subir
  const processResult = await processDocument(uploadResult.file_id);
  console.log('Procesamiento completado:', processResult);
}
```

**Notas:**
- El procesamiento puede tardar varios segundos dependiendo del tamaño del documento
- El estado del documento se actualiza automáticamente: `uploaded` → `processing` → `processed`
- Si el documento ya está procesado, retorna información sin reprocesar
- Los chunks se almacenan en Qdrant con sus embeddings para búsqueda vectorial

---

---

### 7. Chat con RAG

Hace preguntas sobre los documentos procesados usando RAG (Retrieval Augmented Generation).

**Endpoint:** `POST /api/chat`

**Content-Type:** `application/json`

**Body:**
```json
{
  "question": "¿Cuáles son las obligaciones del arrendatario?",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "mistral:7b-instruct",
  "max_chunks": 5,
  "temperature": 0.7
}
```

**Parámetros:**
- `question` (string, requerido): Pregunta del usuario
- `file_id` (string, opcional): Si se especifica, busca solo en ese documento. Si es `null`, busca en todos los documentos procesados
- `model` (string, opcional): Modelo de Ollama a usar (default: `"mistral:7b-instruct"`)
- `max_chunks` (int, opcional): Número máximo de chunks a usar como contexto (default: `5`)
- `temperature` (float, opcional): Creatividad de la respuesta 0.0-1.0 (default: `0.7`). Más bajo = más determinista

**Respuesta Exitosa (200):**
```json
{
  "answer": "Según el documento, el arrendatario tiene las siguientes obligaciones principales:\n\n1. Pagar el alquiler antes del día 5 de cada mes...\n2. Mantener el inmueble en buen estado...\n3. No puede subarrendar sin autorización...",
  "sources": [
    {
      "chunk_id": "a7f3c2d1-8e4b-4f9a-9c2d-1e5f8a3b7c9d",
      "file_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "contrato.pdf",
      "text_preview": "El contrato establece que el arrendatario debe pagar el alquiler antes del día 5 de cada mes...",
      "relevance_score": 0.9234,
      "chunk_index": 5
    },
    {
      "chunk_id": "b8g4d3e2-9f5c-5g0b-0d3e-2f6g9b4c8d0e",
      "file_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "contrato.pdf",
      "text_preview": "El arrendatario debe mantener el inmueble en buen estado de conservación...",
      "relevance_score": 0.8912,
      "chunk_index": 8
    }
  ],
  "model_name": "mistral:7b-instruct"
}
```

**Errores Posibles:**

- **404 Not Found:** No se encontraron documentos relevantes
```json
{
  "detail": "No se encontraron documentos relevantes para responder tu pregunta. Asegúrate de haber subido y procesado documentos."
}
```

- **400 Bad Request:** Documento no procesado
```json
{
  "detail": "El documento 550e8400-e29b-41d4-a716-446655440000 no está procesado. Debe estar en estado 'processed'."
}
```

- **503 Service Unavailable:** Modelo no disponible
```json
{
  "detail": "El modelo 'mistral' no está disponible en Ollama. Verifica que esté instalado."
}
```

**Ejemplo de uso (JavaScript/Vue):**
```javascript
async function askQuestion(question, fileId = null, model = "mistral:7b-instruct") {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question: question,
        file_id: fileId,
        model: model,
        max_chunks: 5,
        temperature: 0.7
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al procesar la pregunta');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Uso
const result = await askQuestion("¿Cuáles son las obligaciones del arrendatario?");
console.log('Respuesta:', result.answer);
console.log('Fuentes:', result.sources);
```

**Ejemplo con axios:**
```javascript
import axios from 'axios';

async function askQuestion(question, fileId = null) {
  try {
    const response = await axios.post('/api/chat', {
      question: question,
      file_id: fileId,
      model: 'mistral:7b-instruct',
      max_chunks: 5
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.detail || 'Error al procesar la pregunta');
    }
    throw error;
  }
}
```

**Flujo RAG:**
1. La pregunta se convierte en un embedding
2. Se buscan los chunks más similares en Qdrant (búsqueda vectorial)
3. Los chunks relevantes se envían a Ollama junto con la pregunta
4. Ollama genera una respuesta usando solo el contexto proporcionado
5. Se retorna la respuesta con las fuentes (chunks) utilizadas

---

### 8. Listar Modelos Disponibles

Lista todos los modelos instalados en Ollama.

**Endpoint:** `GET /api/models`

**Respuesta Exitosa (200):**
```json
{
  "models": [
    "mistral:latest",
    "llama2:latest"
  ],
  "default": "mistral:7b-instruct",
  "ollama_url": "http://ollama:11434"
}
```

**Ejemplo de uso:**
```javascript
async function getAvailableModels() {
  const response = await fetch('/api/models');
  const data = await response.json();
  return data.models;
}
```

---

### 9. Verificar Modelo

Verifica si un modelo específico está disponible en Ollama.

**Endpoint:** `GET /api/models/{model}/check`

**Parámetros de Ruta:**
- `model` (string, requerido): Nombre del modelo a verificar

**Respuesta Exitosa (200):**
```json
{
  "model": "mistral:7b-instruct",
  "available": true,
  "ollama_url": "http://ollama:11434"
}
```

**Ejemplo de uso:**
```javascript
async function checkModel(model) {
  const response = await fetch(`/api/models/${model}/check`);
  const data = await response.json();
  return data.available;
}

// Verificar si mistral está disponible
const isAvailable = await checkModel('mistral');
if (isAvailable) {
  console.log('Mistral está disponible');
}
```

---

## Instalación de Modelos en Ollama

Para instalar Mistral u otros modelos en Ollama:

```bash
# Desde el contenedor de Ollama
docker exec -it legalbot-ollama ollama pull mistral:7b-instruct

# O desde el host (si Ollama está expuesto en el puerto 11434)
curl http://localhost:11434/api/pull -d '{"name": "mistral:7b-instruct"}'
```

Modelos recomendados:
- `mistral:7b-instruct` - Modelo por defecto, buen balance entre calidad y velocidad
- `mistral` - Versión latest de Mistral
- `llama2` - Alternativa popular
- `codellama` - Si necesitas análisis de código

---

## Próximos Endpoints (En desarrollo)

- `DELETE /api/documents/{file_id}` - Eliminar un documento y sus vectores

---

## Soporte

Para más información sobre la arquitectura del backend, consulta la documentación en `doc/back/`.

