# Documentación de Componentes - Frontend LegalBot

## Componente: Sidebar

### Propósito
Panel de navegación lateral que permite cambiar entre las diferentes secciones de la aplicación.

### Ubicación
`data/frontend/src/components/Sidebar.vue`

### Props

| Prop | Tipo | Requerido | Descripción |
|------|------|-----------|-------------|
| `activeView` | String | Sí | Vista actualmente activa. Valores posibles: `'chat'` o `'documents'` |

### Eventos

| Evento | Payload | Descripción |
|--------|---------|-------------|
| `change-view` | `String` | Emitido cuando el usuario hace clic en un elemento del menú. El payload es el nombre de la vista seleccionada. |

### Uso

```vue
<Sidebar 
  :active-view="currentView" 
  @change-view="handleViewChange" 
/>
```

### Estilos

- Ancho fijo: 280px en desktop
- Fondo: Gradiente de gris oscuro (#2c3e50 a #34495e)
- Elemento activo: Resaltado con borde izquierdo azul (#667eea)
- Responsive: Se adapta a móviles ocultando texto y mostrando solo iconos

---

## Componente: Chat

### Propósito
Interfaz de chat para interactuar con el LLM y hacer consultas sobre documentos legales.

### Ubicación
`data/frontend/src/components/Chat.vue`

### Props
Ninguno

### Datos Reactivos

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `messages` | Array | Lista de mensajes del chat. Cada mensaje tiene: `type` ('user', 'assistant', 'error'), `content` (String), `sources` (Array, opcional), `timestamp` (Date) |
| `currentMessage` | String | Texto del mensaje actual en el textarea |
| `loading` | Boolean | Indica si hay una petición en curso |
| `apiUrl` | String | URL base de la API (desde env o por defecto '/api') |
| `selectedFileId` | String/null | ID del documento para filtrar búsquedas (opcional) |
| `model` | String | Modelo de Ollama a usar (default: 'mistral:7b-instruct') |
| `maxChunks` | Number | Número máximo de chunks a usar como contexto (default: 5) |
| `temperature` | Number | Creatividad de la respuesta 0.0-1.0 (default: 0.7) |

### Métodos

| Método | Descripción |
|--------|-------------|
| `sendMessage()` | Envía el mensaje actual al backend usando RAG y maneja la respuesta |
| `scrollToBottom()` | Hace scroll automático al final de los mensajes |
| `formatTime(date)` | Formatea una fecha a hora local (HH:MM) |
| `formatMessageContent(content)` | Convierte saltos de línea a HTML para mostrar correctamente |
| `autoResizeTextarea()` | Ajusta automáticamente la altura del textarea |

### Endpoints Utilizados

- `POST ${apiUrl}/chat`: Envía preguntas al LLM usando RAG (Retrieval Augmented Generation)

**Request:**
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
- `file_id` (string, opcional): Si se especifica, busca solo en ese documento
- `model` (string, opcional): Modelo de Ollama (default: "mistral:7b-instruct")
- `max_chunks` (int, opcional): Número máximo de chunks a usar (default: 5)
- `temperature` (float, opcional): Creatividad 0.0-1.0 (default: 0.7)

**Response esperado:**
```json
{
  "answer": "Según el documento, el arrendatario tiene las siguientes obligaciones...",
  "sources": [
    {
      "chunk_id": "a7f3c2d1-8e4b-4f9a-9c2d-1e5f8a3b7c9d",
      "file_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "contrato.pdf",
      "text_preview": "El contrato establece que...",
      "relevance_score": 0.9234,
      "chunk_index": 5
    }
  ],
  "model_used": "mistral:7b-instruct"
}
```

**Errores posibles:**
- `404`: No se encontraron documentos relevantes
- `400`: Documento no procesado
- `503`: Modelo no disponible en Ollama

### Características

- Mensaje de bienvenida al montar el componente
- Indicador de escritura mientras se procesa la respuesta
- Timestamps en cada mensaje
- Visualización de fuentes (sources) cuando están disponibles
- Muestra relevancia de cada fuente utilizada
- Manejo de errores específicos según el tipo (404, 400, 503)
- Auto-scroll al recibir nuevos mensajes
- Textarea con auto-resize (máximo 120px de altura)
- Envío con Enter, nueva línea con Shift+Enter
- Soporte para formateo de texto (saltos de línea)
- Integración con RAG (Retrieval Augmented Generation)

### Uso

```vue
<Chat />
```

---

## Componente: DocumentProcessor

### Propósito
Permite subir documentos legales en formato PDF para procesarlos y hacerlos disponibles para consultas en el chat.

### Ubicación
`data/frontend/src/components/DocumentProcessor.vue`

### Props
Ninguno

### Datos Reactivos

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `uploadedFiles` | Array | Lista de archivos seleccionados (objetos File) |
| `isDragging` | Boolean | Indica si hay un archivo siendo arrastrado sobre la zona |
| `uploading` | Boolean | Indica si hay una subida en curso |
| `uploadStatus` | Object/null | Estado de la última operación: `{ type: 'success'|'error'|'info', message: String }` |
| `processedDocuments` | Array | Lista de documentos procesados exitosamente |
| `apiUrl` | String | URL base de la API |

### Métodos

| Método | Descripción |
|--------|-------------|
| `triggerFileInput()` | Abre el diálogo de selección de archivos |
| `handleFileSelect(event)` | Maneja la selección de archivos desde el input |
| `handleDrop(event)` | Maneja el evento de soltar archivos (drag & drop) |
| `addFiles(files)` | Agrega archivos a la lista, validando que sean PDF |
| `removeFile(index)` | Elimina un archivo de la lista |
| `clearFiles()` | Limpia todos los archivos seleccionados |
| `uploadFiles()` | Sube los archivos al backend (usa endpoint según cantidad) |
| `showStatus(type, message)` | Muestra un mensaje de estado |
| `formatFileSize(bytes)` | Convierte bytes a formato legible (KB, MB, etc.) |
| `formatDate(date)` | Formatea una fecha a formato local |

### Endpoints Utilizados

El componente usa diferentes endpoints según la cantidad de archivos:

- **Un archivo**: `POST ${apiUrl}/upload`
- **Múltiples archivos**: `POST ${apiUrl}/upload/multiple`

**Request (archivo único):**
```
Content-Type: multipart/form-data
FormData:
  file: File (archivo único)
  description: String (opcional)
```

**Request (múltiples archivos):**
```
Content-Type: multipart/form-data
FormData:
  files: File[] (múltiples archivos)
```

**Response (archivo único - 200):**
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

**Response (múltiples archivos - 200):**
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
    "success": false,
    "message": "Tipo de archivo no permitido: archivo.exe",
    "file_id": null,
    "filename": "archivo.exe"
  }
]
```

**Errores posibles:**
- `400 Bad Request`: Tipo de archivo no permitido o archivo demasiado grande (>50MB)
- `404 Not Found`: Endpoint no disponible
- `413 Payload Too Large`: Archivo excede el límite de tamaño

### Características

- Drag & drop de archivos PDF
- Selección múltiple de archivos PDF
- Validación estricta de tipo de archivo (solo PDF)
- Vista previa de archivos con nombre y tamaño
- Eliminación individual de archivos
- Indicadores de estado (éxito, error, información)
- Lista de documentos procesados con file_id
- Manejo de errores con mensajes informativos
- Auto-limpieza después de subida exitosa
- Manejo de respuestas parciales (algunos archivos exitosos, otros fallidos)

### Validaciones

- Solo acepta archivos PDF con tipo MIME: `application/pdf`
- Validación por extensión como fallback: `.pdf`
- Evita duplicados (mismo nombre y tamaño)
- Muestra mensaje de error si se intentan subir archivos que no sean PDF
- Límite de tamaño: 50MB por archivo (validado por el backend)

### Uso

```vue
<DocumentProcessor />
```

---

## Componente: App

### Propósito
Componente raíz de la aplicación que orquesta los demás componentes.

### Ubicación
`data/frontend/src/App.vue`

### Componentes Utilizados

- `Sidebar`
- `Chat`
- `DocumentProcessor`

### Datos Reactivos

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `currentView` | String | Vista actualmente activa ('chat' o 'documents') |

### Métodos

| Método | Descripción |
|--------|-------------|
| `changeView(view)` | Cambia la vista actual |

### Estructura

```
App
├── Sidebar (siempre visible)
└── Main Content
    ├── Chat (si currentView === 'chat')
    └── DocumentProcessor (si currentView === 'documents')
```

### Uso

El componente se monta automáticamente en `main.js`:

```javascript
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
```

