# Frontend - LegalBot

## Descripción

Interfaz web desarrollada con Vue 3 para el sistema LegalBot. Proporciona una interfaz de usuario moderna y funcional para interactuar con documentos legales mediante un chat con LLM y procesamiento de documentos PDF.

## Estructura del Proyecto

```
data/frontend/
├── src/
│   ├── components/
│   │   ├── Sidebar.vue          # Panel lateral con menú de navegación
│   │   ├── Chat.vue              # Componente de chat para conectar con LLM
│   │   └── DocumentProcessor.vue # Componente para subir y procesar PDFs
│   ├── App.vue                   # Componente principal de la aplicación
│   └── main.js                   # Punto de entrada de la aplicación
├── index.html                    # HTML principal
├── package.json                  # Dependencias del proyecto
└── vite.config.js               # Configuración de Vite
```

## Componentes

### Sidebar.vue

Panel lateral izquierdo que contiene el menú de navegación principal.

**Características:**
- Menú de navegación con dos opciones:
  - **Chat**: Interfaz de chat para consultas
  - **Procesar Documentos**: Subida y procesamiento de PDFs
- Diseño responsive con adaptación móvil
- Indicador visual del elemento activo

**Props:**
- `activeView` (String, requerido): Vista actualmente activa ('chat' o 'documents')

**Eventos:**
- `change-view`: Emitido cuando el usuario cambia de vista

### Chat.vue

Componente principal para la interfaz de chat con el LLM.

**Características:**
- Interfaz de chat moderna con mensajes de usuario y asistente
- Indicador de escritura mientras se procesa la respuesta
- Timestamps en los mensajes
- Auto-scroll al recibir nuevos mensajes
- Textarea con auto-resize
- Manejo de errores con mensajes informativos
- Conexión con el backend mediante API REST

**Endpoints utilizados:**
- `POST /api/chat`: Envío de mensajes al LLM (aún no implementado en backend)

**Funcionalidades:**
- Envío de mensajes con Enter (Shift+Enter para nueva línea)
- Manejo de estados de carga
- Formateo de timestamps
- Animaciones suaves para nuevos mensajes

### DocumentProcessor.vue

Componente para la subida y procesamiento de documentos legales en formato PDF.

**Características:**
- Zona de arrastre y soltado (drag & drop)
- Selección múltiple de archivos
- Vista previa de archivos seleccionados con información (nombre, tamaño)
- Eliminación individual de archivos antes de subir
- Indicadores de estado (éxito, error, información)
- Lista de documentos procesados exitosamente con file_id
- Validación de tipo de archivo (solo PDF)

**Endpoints utilizados:**
- `POST /api/upload`: Subida de un archivo único
- `POST /api/upload/multiple`: Subida de múltiples archivos

El componente selecciona automáticamente el endpoint según la cantidad de archivos.

**Funcionalidades:**
- Drag & drop de archivos
- Selección mediante click
- Validación de tipo de archivo (solo PDF)
- Formateo de tamaño de archivo
- Manejo de errores y estados de carga
- Manejo de respuestas parciales (algunos archivos exitosos, otros fallidos)
- Limpieza de archivos seleccionados después de subida exitosa

## Configuración

### Variables de Entorno

El proyecto utiliza variables de entorno para la configuración:

- `VITE_API_URL`: URL base de la API del backend (por defecto: `/api`)

Estas variables se configuran en `docker-compose.yml`:

```yaml
environment:
  - VITE_API_URL=/api
```

### Dependencias Principales

- **Vue 3**: Framework JavaScript progresivo
- **Axios**: Cliente HTTP para peticiones a la API
- **Vite**: Build tool y servidor de desarrollo
- **@vitejs/plugin-vue**: Plugin de Vue para Vite

## Desarrollo

### Comandos Disponibles

```bash
# Desarrollo (con hot-reload)
npm run dev

# Build para producción
npm run build

# Preview del build de producción
npm run preview
```

### Estructura de Vistas

La aplicación utiliza un sistema de vistas basado en el componente `Sidebar`:

1. **Chat** (`currentView === 'chat'`): Muestra el componente `Chat.vue`
2. **Procesar Documentos** (`currentView === 'documents'`): Muestra el componente `DocumentProcessor.vue`

El componente `App.vue` gestiona el cambio entre vistas mediante el evento `change-view` emitido por `Sidebar`.

## Diseño

### Paleta de Colores

- **Primario**: `#667eea` (Azul púrpura)
- **Secundario**: `#2c3e50` (Gris oscuro)
- **Fondo**: `#f8f9fa` (Gris claro)
- **Éxito**: `#28a745` (Verde)
- **Error**: `#dc3545` (Rojo)

### Responsive Design

La aplicación está diseñada para ser responsive:

- **Desktop**: Sidebar fijo a la izquierda (280px), contenido principal con margen izquierdo
- **Mobile**: Sidebar adaptado, contenido a pantalla completa

## Integración con Backend

### Endpoints Esperados

#### Chat
```
POST /api/chat
Content-Type: application/json

{
  "message": "¿Qué dice el documento sobre...?"
}

Response:
{
  "response": "Respuesta del LLM...",
  // o
  "message": "Respuesta alternativa..."
}
```

#### Carga de Documentos

**Archivo único:**
```
POST /api/upload
Content-Type: multipart/form-data

FormData:
  file: File (archivo único)
  description: String (opcional)

Response:
{
  "success": true,
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "documento.pdf",
  "file_size": 1024000,
  "uploaded_at": "2024-01-15T10:30:00.000000"
}
```

**Múltiples archivos:**
```
POST /api/upload/multiple
Content-Type: multipart/form-data

FormData:
  files: File[] (múltiples archivos)

Response:
[
  {
    "success": true,
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "documento1.pdf",
    "file_size": 1024000,
    "uploaded_at": "2024-01-15T10:30:00.000000"
  }
]
```

**Tipo de archivo permitido:** PDF únicamente  
**Límite de tamaño:** 50MB por archivo

## Notas de Implementación

### Manejo de Errores

Los componentes incluyen manejo de errores para:
- Endpoints no disponibles (404)
- Errores de red
- Errores del servidor
- Validación de archivos

### Estados de Carga

Se implementan indicadores visuales para:
- Envío de mensajes
- Carga de archivos
- Procesamiento de documentos

### Accesibilidad

- Botones con estados disabled apropiados
- Mensajes de error claros
- Indicadores visuales de estado
- Navegación por teclado

## Próximas Mejoras

- [ ] Implementar WebSocket para respuestas en tiempo real
- [ ] Agregar historial de conversaciones
- [ ] Implementar búsqueda en documentos procesados
- [ ] Agregar vista previa de documentos PDF
- [ ] Implementar autenticación de usuarios
- [ ] Agregar modo oscuro
- [ ] Mejorar accesibilidad (ARIA labels, navegación por teclado)

