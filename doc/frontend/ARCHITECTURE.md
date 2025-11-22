# Arquitectura del Frontend - LegalBot

## Visión General

El frontend de LegalBot está construido con Vue 3 utilizando Composition API (aunque los componentes actuales usan Options API para simplicidad). La aplicación sigue una arquitectura de componentes modulares con separación clara de responsabilidades.

## Estructura de Directorios

```
data/frontend/
├── src/
│   ├── components/          # Componentes reutilizables
│   │   ├── Sidebar.vue
│   │   ├── Chat.vue
│   │   └── DocumentProcessor.vue
│   ├── App.vue              # Componente raíz
│   └── main.js              # Punto de entrada
├── dist/                    # Build de producción (generado)
├── index.html               # HTML principal
├── package.json             # Dependencias
└── vite.config.js          # Configuración de Vite
```

## Flujo de Datos

### Comunicación con el Backend

```
Frontend (Vue 3)
    │
    ├── Chat Component
    │   └── POST /api/chat
    │       └── { message: string }
    │
    └── DocumentProcessor Component
        └── POST /api/documents/upload
            └── FormData { files: File[] }
```

### Flujo de Navegación

```
App.vue (Root)
    │
    ├── Sidebar Component
    │   └── Emite: change-view
    │
    └── Main Content Area
        ├── Chat Component (si view === 'chat')
        └── DocumentProcessor Component (si view === 'documents')
```

## Patrones de Diseño

### 1. Component-Based Architecture

Cada funcionalidad principal está encapsulada en su propio componente:

- **Sidebar**: Navegación y estado de vista activa
- **Chat**: Lógica de comunicación con LLM
- **DocumentProcessor**: Gestión de archivos y upload

### 2. Props Down, Events Up

- Los componentes hijos reciben datos mediante **props**
- Los componentes hijos comunican cambios mediante **events**
- El componente padre (`App.vue`) gestiona el estado global de la vista

### 3. Separation of Concerns

- **Presentación**: Estilos y estructura HTML en cada componente
- **Lógica**: Métodos y datos reactivos en el script del componente
- **Comunicación**: Axios para peticiones HTTP, eventos para comunicación padre-hijo

## Gestión de Estado

### Estado Local por Componente

Cada componente gestiona su propio estado:

- **App.vue**: `currentView` (vista activa)
- **Chat.vue**: `messages`, `currentMessage`, `loading`
- **DocumentProcessor.vue**: `uploadedFiles`, `uploading`, `uploadStatus`, `processedDocuments`

### Estado Compartido

Actualmente no hay estado compartido entre componentes. Si fuera necesario en el futuro, se podría implementar:

- **Vuex** o **Pinia** para estado global
- **Provide/Inject** para estado compartido en árbol de componentes
- **Props drilling** para casos simples

## Comunicación con API

### Configuración

La URL de la API se configura mediante variables de entorno:

```javascript
apiUrl: import.meta.env.VITE_API_URL || '/api'
```

### Manejo de Errores

Cada componente implementa su propio manejo de errores:

1. **Errores de Red**: Detectados mediante `error.code === 'ERR_NETWORK'`
2. **Errores HTTP**: Detectados mediante `error.response.status`
3. **Errores de Validación**: Mostrados mediante mensajes de estado

### Patrón de Peticiones

```javascript
try {
  const response = await axios.post(endpoint, data)
  // Manejo de éxito
} catch (error) {
  // Manejo de errores específicos
  if (error.response?.status === 404) {
    // Endpoint no disponible
  } else {
    // Otro tipo de error
  }
}
```

## Estilos y Diseño

### Enfoque de Estilos

- **Scoped Styles**: Cada componente tiene sus estilos encapsulados con `<style scoped>`
- **CSS Variables**: No se utilizan actualmente, pero podrían agregarse para temas
- **Responsive Design**: Media queries para adaptación móvil

### Sistema de Diseño

- **Colores**: Paleta consistente definida en cada componente
- **Espaciado**: Uso consistente de padding y margin
- **Tipografía**: Fuentes del sistema para mejor rendimiento
- **Animaciones**: Transiciones suaves para mejor UX

## Build y Despliegue

### Desarrollo

```bash
npm run dev
```

- Servidor de desarrollo en `http://localhost:3000`
- Hot Module Replacement (HMR) activo
- Source maps para debugging

### Producción

```bash
npm run build
```

- Build optimizado en `dist/`
- Minificación con Terser
- Assets optimizados
- Sin source maps (configurado en `vite.config.js`)

### Despliegue

El build se sirve mediante Nginx:

1. `frontend` service construye la aplicación
2. Archivos estáticos copiados a `data/static/`
3. Nginx sirve los archivos estáticos en `/`

## Optimizaciones

### Rendimiento

- **Lazy Loading**: No implementado actualmente (componentes cargados al inicio)
- **Code Splitting**: Podría implementarse con `defineAsyncComponent`
- **Tree Shaking**: Automático con Vite y ES modules

### Mejoras Futuras

1. **Lazy Loading de Componentes**:
```javascript
const Chat = defineAsyncComponent(() => import('./components/Chat.vue'))
```

2. **Caching de Respuestas**: Implementar caché para mensajes del chat

3. **Service Worker**: Para funcionalidad offline

4. **Virtual Scrolling**: Para listas largas de mensajes/documentos

## Testing (Futuro)

### Estrategia de Testing

- **Unit Tests**: Para lógica de componentes (Vue Test Utils)
- **Integration Tests**: Para flujos completos
- **E2E Tests**: Para casos de uso críticos (Cypress/Playwright)

### Estructura Propuesta

```
src/
├── components/
├── __tests__/
│   ├── Chat.spec.js
│   ├── DocumentProcessor.spec.js
│   └── Sidebar.spec.js
└── utils/
    └── __tests__/
```

## Seguridad

### Consideraciones Actuales

- Validación de tipos de archivo en el cliente (PDF)
- Sanitización de inputs (manejada por Vue)
- CORS configurado en el backend

### Mejoras Futuras

- Validación adicional en el backend
- Rate limiting en peticiones
- Autenticación y autorización
- Sanitización de HTML en respuestas del LLM

## Accesibilidad

### Implementaciones Actuales

- Estructura semántica HTML
- Estados disabled en botones
- Mensajes de error claros

### Mejoras Futuras

- ARIA labels y roles
- Navegación por teclado completa
- Contraste de colores mejorado
- Screen reader support

## Escalabilidad

### Preparación para Crecimiento

1. **Estructura Modular**: Fácil agregar nuevos componentes
2. **Separación de Concerns**: Lógica separada de presentación
3. **Configuración Centralizada**: Variables de entorno para configuración

### Posibles Extensiones

- Sistema de plugins para funcionalidades adicionales
- Internacionalización (i18n)
- Temas personalizables
- Múltiples idiomas

