# ============================================================================
# Dockerfile para Frontend Vue 3
# ============================================================================
# Esta imagen solo prepara el entorno de Node.js
# La ejecución (npm run build) se hace desde docker-compose

FROM node:20-alpine

# Metadatos
LABEL maintainer="LegalBot"
LABEL description="Frontend Vue 3 build environment"

# Instalar dependencias del sistema necesarias para builds de Node.js
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# Crear directorio de trabajo
WORKDIR /app

# Crear usuario no-root para seguridad
#RUN addgroup -g 1001 -S nodejs && \
#    adduser -S nodejs -u 1001

# Crear directorios necesarios y asignar permisos
#RUN mkdir -p /app/dist && \
#    chown -R nodejs:nodejs /app

# Cambiar a usuario no-root
#USER nodejs

# El código fuente se monta como volumen desde docker-compose
# Los node_modules se instalan en el contenedor vía volumen anónimo

# NOTA: No hay CMD aquí
# El comando (npm install && npm run build) se ejecuta desde docker-compose

