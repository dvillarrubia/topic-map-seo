#!/bin/bash
# Script de deployment para Topic Map SEO en SUBDIRECTORIO
# Usa cuando ya tienes otra aplicación corriendo en tu VPS
# Uso: ./deploy-subdirectory.sh

set -e  # Exit on error

REPO_URL="https://github.com/dvillarrubia/topic-map-seo.git"
APP_DIR="/opt/topic-map-seo"
NGINX_CONF="/etc/nginx/sites-available/topic-map"
NGINX_ENABLED="/etc/nginx/sites-enabled/topic-map"
WEB_ROOT="/var/www/topic-map"

echo "🚀 Deploying Topic Map SEO en subcarpeta /topic-map..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 1. Verificar Docker
log "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado."
fi

# 2. Clonar/actualizar repositorio
if [ -d "$APP_DIR/.git" ]; then
    log "Actualizando código desde Git..."
    cd $APP_DIR
    git fetch origin
    git reset --hard origin/master
else
    log "Clonando repositorio..."
    sudo rm -rf $APP_DIR
    sudo git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# 3. Detener contenedor anterior (solo API, NO Nginx)
log "Deteniendo contenedor anterior..."
sudo docker-compose stop topic-map-api 2>/dev/null || true
sudo docker-compose rm -f topic-map-api 2>/dev/null || true

# 4. Build de imagen API
log "Construyendo imagen Docker..."
sudo docker-compose build topic-map-api

# 5. Iniciar solo el servicio API (NO Nginx)
log "Iniciando servicio API..."
sudo docker-compose up -d topic-map-api

# 6. Preparar archivos estáticos para Nginx
log "Configurando archivos estáticos..."
sudo mkdir -p $WEB_ROOT
sudo cp topic-map-server-dev.html $WEB_ROOT/index.html
sudo chown -R www-data:www-data $WEB_ROOT

# 7. Configurar Nginx del VPS (no el contenedor)
log "Configurando Nginx del sistema..."

# Crear configuración de Nginx para /topic-map
sudo tee $NGINX_CONF > /dev/null <<'EOF'
# Topic Map SEO - Configuración para subcarpeta /topic-map

server {
    listen 80;
    server_name _;  # Cambiar a tu dominio si es necesario

    # Limite de tamaño de archivo
    client_max_body_size 50M;

    # Servir frontend estático en /topic-map
    location /topic-map {
        alias /var/www/topic-map;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, must-revalidate";

        # Servir index.html por defecto
        index index.html;
    }

    # API backend (proxy a Docker)
    location /topic-map/api/ {
        rewrite ^/topic-map/api/(.*) /$1 break;

        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts largos
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check
    location /topic-map/health {
        rewrite ^/topic-map/health$ /health break;
        proxy_pass http://127.0.0.1:5000;
        access_log off;
    }
}
EOF

# 8. Activar configuración si no existe
if [ ! -f "$NGINX_ENABLED" ]; then
    log "Activando configuración de Nginx..."
    sudo ln -s $NGINX_CONF $NGINX_ENABLED
fi

# 9. Verificar y recargar Nginx
log "Verificando configuración de Nginx..."
sudo nginx -t

log "Recargando Nginx..."
sudo systemctl reload nginx

# 10. Esperar a que el servicio esté disponible
log "Esperando a que el servicio esté disponible..."
TIMEOUT=60
COUNTER=0
until curl -f http://localhost:5000/health &>/dev/null || [ $COUNTER -eq $TIMEOUT ]; do
    sleep 2
    COUNTER=$((COUNTER + 2))
    echo -n "."
done
echo ""

if [ $COUNTER -eq $TIMEOUT ]; then
    error "El servicio no respondió después de ${TIMEOUT}s"
fi

# 11. Verificar estado
log "Verificando contenedor..."
sudo docker ps | grep topic-map-api

# Final
echo ""
log "✅ Deployment completado exitosamente!"
echo ""
echo "📊 URLs de acceso:"
echo "   - Frontend: http://$(hostname -I | awk '{print $1}')/topic-map"
echo "   - API: http://$(hostname -I | awk '{print $1}')/topic-map/api"
echo "   - Health: http://$(hostname -I | awk '{print $1}')/topic-map/health"
echo ""
echo "📝 Comandos útiles:"
echo "   - Ver logs API: sudo docker logs -f topic-map-api"
echo "   - Ver logs Nginx: sudo tail -f /var/log/nginx/error.log"
echo "   - Reiniciar API: sudo docker-compose restart topic-map-api"
echo "   - Redeployar: sudo ./deploy-subdirectory.sh"
echo ""
