# Dockerfile para Topic Map SEO Clustering Server
FROM python:3.11-slim

# Metadata
LABEL maintainer="dvillarrubia"
LABEL description="Semantic SEO clustering with UMAP and Spanish embeddings"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_APP=clustering_server.py \
    FLASK_ENV=production

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Descargar modelo de sentence-transformers en build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')"

# Copiar código de la aplicación
COPY clustering_server.py .
COPY vectorize_keywords.py .

# Crear directorio para archivos subidos
RUN mkdir -p /app/uploads

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Comando de inicio
CMD ["python", "clustering_server.py"]
