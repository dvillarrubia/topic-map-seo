#!/bin/bash
# Script de deployment para VPS
# Uso: ./deploy.sh [production|staging]

set -e  # Exit on error

ENV=${1:-production}
REPO_URL="https://github.com/dvillarrubia/topic-map-seo.git"
APP_DIR="/opt/topic-map-seo"
BACKUP_DIR="/opt/backups/topic-map-seo"

echo "🚀 Deploying Topic Map SEO to $ENV environment..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función de log
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
    error "Docker no está instalado. Instala Docker primero."
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado."
fi

# 2. Crear directorio de backup si no existe
log "Preparando backup..."
mkdir -p $BACKUP_DIR

# 3. Backup de versión actual (si existe)
if [ -d "$APP_DIR" ]; then
    warning "Encontrado deployment previo. Haciendo backup..."
    BACKUP_NAME="backup-$(date +'%Y%m%d-%H%M%S').tar.gz"
    tar -czf "$BACKUP_DIR/$BACKUP_NAME" -C "$APP_DIR" . 2>/dev/null || true
    log "Backup guardado en: $BACKUP_DIR/$BACKUP_NAME"
fi

# 4. Clonar/actualizar repositorio
if [ -d "$APP_DIR/.git" ]; then
    log "Actualizando código desde Git..."
    cd $APP_DIR
    git fetch origin
    git reset --hard origin/master
else
    log "Clonando repositorio..."
    rm -rf $APP_DIR
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# 5. Crear directorio static si no existe
log "Configurando archivos estáticos..."
mkdir -p $APP_DIR/static
mkdir -p $APP_DIR/uploads

# Copiar HTML al directorio static para Nginx
cp topic-map-server-dev.html static/
cp topic-map-server.html static/ 2>/dev/null || true
cp topic-map-vectorized.html static/ 2>/dev/null || true

# 6. Actualizar API_URL en frontend para producción
log "Configurando API URL..."
sed -i "s|const API_URL = 'http://localhost:5000'|const API_URL = '/api'|g" static/topic-map-server-dev.html

# 7. Detener contenedores anteriores
log "Deteniendo contenedores anteriores..."
docker-compose down 2>/dev/null || true

# 8. Build de imágenes
log "Construyendo imágenes Docker..."
docker-compose build --no-cache

# 9. Iniciar servicios
log "Iniciando servicios..."
docker-compose up -d

# 10. Esperar a que el servicio esté saludable
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
log "Verificando estado de contenedores..."
docker-compose ps

# 12. Mostrar logs recientes
log "Logs recientes del servicio:"
docker-compose logs --tail=20 topic-map-api

# 13. Limpiar imágenes antiguas
log "Limpiando imágenes antiguas..."
docker image prune -f

# Final
echo ""
log "✅ Deployment completado exitosamente!"
echo ""
echo "📊 Información del servicio:"
echo "   - API: http://localhost:5000"
echo "   - Frontend: http://localhost (Nginx)"
echo "   - Health: http://localhost:5000/health"
echo ""
echo "📝 Comandos útiles:"
echo "   - Ver logs: docker-compose logs -f topic-map-api"
echo "   - Reiniciar: docker-compose restart"
echo "   - Detener: docker-compose down"
echo "   - Redeployar: ./deploy.sh"
echo ""
