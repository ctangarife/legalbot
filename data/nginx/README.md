# Configuración Nginx para LegalBot

Este directorio contiene la configuración del reverse proxy Nginx que actúa como punto de entrada para todas las peticiones al backend FastAPI.

## Estructura

```
nginx/
├── nginx.conf              # Configuración principal de Nginx
├── conf.d/
│   └── default.conf        # Configuración del reverse proxy
├── includes/
│   └── security-headers.conf  # Headers de seguridad HTTP
└── README.md               # Este archivo
```

## Funcionalidades

### Reverse Proxy
- Todas las peticiones a `/api/*` se redirigen al backend FastAPI
- Rate limiting configurado para protección DDoS
- Timeouts optimizados para diferentes tipos de operaciones

### Endpoints Especiales

- **`/api/chat`**: Endpoint de chat con rate limiting más restrictivo y timeouts extendidos para procesamiento LLM
- **`/api/documents`**: Endpoint de ingesta de documentos con soporte para archivos grandes (hasta 100MB)
- **`/api/health`**: Health check sin rate limiting
- **`/docs`**: Documentación interactiva de FastAPI
- **`/openapi.json`**: Esquema OpenAPI

### Seguridad

- Headers de seguridad HTTP configurados (X-Frame-Options, CSP, etc.)
- Rate limiting por tipo de endpoint
- Bloqueo de acceso a archivos sensibles
- Ocultación de versión de Nginx

### Optimizaciones

- Compresión Gzip habilitada
- Keep-alive connections al upstream
- Buffering optimizado para diferentes tipos de respuestas
- Soporte para streaming (SSE) en endpoints de chat

## Puertos

- **80**: Puerto principal para el reverse proxy
- **8080**: Puerto interno para health checks y estadísticas (solo accesible desde la red Docker)

## Rate Limiting

- **General**: 10 requests/segundo
- **API**: 30 requests/segundo
- **Chat**: 5 requests/segundo (más restrictivo debido al procesamiento LLM)

## Timeouts

- **API General**: 30 segundos
- **Chat/LLM**: 600 segundos (10 minutos) para procesamiento de respuestas
- **Documentos**: 180 segundos para procesamiento de archivos

## Modificación de Configuración

Para modificar la configuración:

1. Edita los archivos en `data/nginx/`
2. Reinicia el contenedor nginx: `docker-compose restart nginx`
3. O reconstruye si cambias el Dockerfile: `docker-compose up -d --build nginx`

## Logs

Los logs de Nginx están disponibles en:
- `/var/log/nginx/access.log` - Logs de acceso
- `/var/log/nginx/error.log` - Logs de errores
- `/var/log/nginx/legalbot.access.log` - Logs específicos del servidor
- `/var/log/nginx/legalbot.error.log` - Errores específicos del servidor

Para ver los logs: `docker-compose logs nginx`

