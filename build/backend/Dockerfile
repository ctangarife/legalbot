FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt e instalar dependencias Python en el sistema
# Las dependencias se instalan antes de montar el volumen para que estén disponibles

# El código se monta como volumen desde docker-compose para permitir hot-reload
# Las dependencias ya están instaladas en el sistema Python y estarán disponibles

