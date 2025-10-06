# 🚀 Guía de Deployment - Topic Map SEO

## Escenario: Integración con Aplicación Existente

Esta guía es para cuando **ya tienes otra aplicación** corriendo en tu VPS y quieres añadir Topic Map como subcarpeta.

---

## ⚙️ Prerequisitos

✅ VPS con Ubuntu/Debian
✅ Docker instalado
✅ Nginx instalado y corriendo
✅ Otra aplicación funcionando (ej: `http://tu-dominio.com`)

---

## 📋 Opción 1: Deployment Automático (Recomendado)

### Paso 1: Conectar al VPS

```bash
ssh usuario@tu-vps-ip
```

### Paso 2: Ejecutar Script de Deployment

```bash
# Clonar repositorio
cd /opt
sudo git clone https://github.com/dvillarrubia/topic-map-seo.git
cd topic-map-seo

# Dar permisos de ejecución
sudo chmod +x deploy-subdirectory.sh

# Ejecutar deployment
sudo ./deploy-subdirectory.sh
```

**El script automáticamente:**
- ✅ Descarga el código
- ✅ Construye contenedor Docker para la API
- ✅ Configura Nginx del sistema (NO contenedor)
- ✅ Despliega en subcarpeta `/topic-map`
- ✅ Verifica que todo funcione

### Paso 3: Verificar

```bash
# Verificar contenedor
sudo docker ps | grep topic-map-api

# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx

# Test API
curl http://localhost:5000/health

# Test frontend
curl http://localhost/topic-map
```

### Acceder

🌐 **Frontend**: `http://tu-dominio.com/topic-map`
🔌 **API**: `http://tu-dominio.com/topic-map/api`
💚 **Health**: `http://tu-dominio.com/topic-map/health`

---

## 📋 Opción 2: Deployment Manual

### Paso 1: Clonar Repositorio

```bash
cd /opt
sudo git clone https://github.com/dvillarrubia/topic-map-seo.git
cd topic-map-seo
```

### Paso 2: Build y Start del Contenedor API

```bash
# Solo iniciar el contenedor API (NO Nginx)
sudo docker-compose up -d topic-map-api

# Verificar logs
sudo docker logs -f topic-map-api
```

### Paso 3: Configurar Archivos Estáticos

```bash
# Crear directorio web
sudo mkdir -p /var/www/topic-map

# Copiar frontend
sudo cp topic-map-server-dev.html /var/www/topic-map/index.html

# Permisos
sudo chown -R www-data:www-data /var/www/topic-map
```

### Paso 4: Configurar Nginx del Sistema

```bash
# Crear archivo de configuración
sudo nano /etc/nginx/sites-available/topic-map
```

**Pega este contenido:**

```nginx
server {
    listen 80;
    server_name _;  # O tu dominio específico

    client_max_body_size 50M;

    # Frontend en /topic-map
    location /topic-map {
        alias /var/www/topic-map;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, must-revalidate";
        index index.html;
    }

    # API backend (proxy a Docker en puerto 5000)
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
```

### Paso 5: Activar Configuración

```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/topic-map /etc/nginx/sites-enabled/

# Verificar sintaxis
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

### Paso 6: Verificar Firewall

```bash
# Si usas UFW
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## 🔄 Actualizar Deployment

```bash
cd /opt/topic-map-seo
sudo git pull origin master
sudo docker-compose build topic-map-api
sudo docker-compose up -d topic-map-api
sudo cp topic-map-server-dev.html /var/www/topic-map/index.html
```

O simplemente:

```bash
sudo ./deploy-subdirectory.sh
```

---

## 🐛 Troubleshooting

### Error: Puerto 5000 ya en uso

```bash
# Ver qué usa el puerto
sudo lsof -i :5000

# Cambiar puerto en docker-compose.yml
ports:
  - "5001:5000"  # Usar 5001 externamente

# Actualizar nginx.conf para usar 127.0.0.1:5001
```

### Error: 502 Bad Gateway

```bash
# Verificar contenedor corriendo
sudo docker ps | grep topic-map-api

# Ver logs
sudo docker logs topic-map-api

# Verificar conectividad desde Nginx
curl http://127.0.0.1:5000/health
```

### Error: 404 Not Found en /topic-map

```bash
# Verificar archivos estáticos
ls -la /var/www/topic-map/

# Verificar permisos
sudo chown -R www-data:www-data /var/www/topic-map

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

### Frontend carga pero API no responde

```bash
# Verificar que el contenedor escucha en 5000
sudo docker port topic-map-api

# Test directo a API
curl -v http://localhost:5000/health

# Verificar configuración de proxy en Nginx
sudo nginx -T | grep -A 20 "location /topic-map/api"
```

---

## 📊 Monitoreo

### Ver Logs en Tiempo Real

```bash
# Logs de API
sudo docker logs -f --tail=100 topic-map-api

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Estado de Servicios

```bash
# Docker
sudo docker ps
sudo docker stats topic-map-api

# Nginx
sudo systemctl status nginx

# Uso de recursos
htop
df -h
```

---

## 🔐 Configurar HTTPS (Opcional)

Si tu dominio ya tiene SSL configurado con Let's Encrypt:

```bash
# Editar configuración existente de SSL
sudo nano /etc/nginx/sites-available/default
```

Añadir dentro del bloque `server { listen 443 ssl; ... }`:

```nginx
# Topic Map en HTTPS
location /topic-map {
    alias /var/www/topic-map;
    try_files $uri $uri/ /index.html;
    index index.html;
}

location /topic-map/api/ {
    rewrite ^/topic-map/api/(.*) /$1 break;
    proxy_pass http://127.0.0.1:5000;
    # ... resto de config proxy
}
```

---

## 🎯 Arquitectura Final

```
┌──────────────────────────────────────────────┐
│  VPS (tu-dominio.com)                        │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ Nginx (Sistema - Puerto 80/443)        │ │
│  │                                        │ │
│  │  / → Tu app principal                 │ │
│  │  /topic-map → Frontend estático       │ │
│  │  /topic-map/api → Proxy a :5000       │ │
│  └────────┬───────────────────────────────┘ │
│           │                                  │
│           ↓                                  │
│  ┌────────────────────────────────────────┐ │
│  │ Docker Container (topic-map-api)       │ │
│  │ - Flask server en puerto 5000          │ │
│  │ - UMAP + Sentence Transformers         │ │
│  │ - Modelo pre-cargado                   │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa logs: `sudo docker logs topic-map-api`
2. Verifica Nginx: `sudo nginx -t`
3. Abre issue en: https://github.com/dvillarrubia/topic-map-seo/issues

---

**Desarrollado para deployment flexible en VPS compartidos** 🚀
