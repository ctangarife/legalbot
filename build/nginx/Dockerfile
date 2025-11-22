FROM nginx:alpine

# Copiar configuración personalizada
COPY data/nginx/nginx.conf /etc/nginx/nginx.conf
COPY data/nginx/conf.d /etc/nginx/conf.d
COPY data/nginx/includes /etc/nginx/includes

# Exponer puertos
EXPOSE 80 8080

# Nginx se ejecuta automáticamente con CMD del imagen base
# pero docker-compose puede sobrescribirlo si es necesario

