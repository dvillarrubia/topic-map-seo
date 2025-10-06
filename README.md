# 🗺️ Topic Map - Visualización Semántica de Keywords SEO

Sistema de clustering semántico para visualizar keywords SEO en mapas interactivos usando UMAP y embeddings de transformers en español.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![D3.js](https://img.shields.io/badge/D3.js-v7-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Características

- ✅ **Embeddings en Español**: Modelo `hiiamsid/sentence_similarity_spanish_es` optimizado para SEO
- ✅ **Reducción Dimensional UMAP**: 768D → 2D con parámetros optimizados para separación semántica
- ✅ **Visualización Interactiva D3.js**:
  - Zoom inteligente con labels progresivos (>2x zoom)
  - Pan y navegación fluida
  - Tooltips con métricas SEO completas
- ✅ **Multi-Dataset**: Carga y compara múltiples archivos Excel simultáneamente
- ✅ **Topics Personalizados**: Añade temas generales y visualiza su posición semántica
- ✅ **Centroides de Clusters**: Visualiza centros de topics con dispersión

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────┐
│  Frontend (HTML + React + D3.js)           │
│  - topic-map-server-dev.html               │
│  - Visualización interactiva               │
└──────────────┬──────────────────────────────┘
               │ REST API (CORS)
               ▼
┌─────────────────────────────────────────────┐
│  Backend Python (Flask)                     │
│  - clustering_server.py                     │
│  - Sentence Transformers                    │
│  - UMAP (n_neighbors=8, min_dist=0.4)      │
└─────────────────────────────────────────────┘
```

## 📦 Instalación

### Requisitos Previos

- Python 3.8+
- Git
- Navegador web moderno (Chrome, Firefox, Edge)

### Setup

1. **Clonar repositorio**
```bash
git clone <repository-url>
cd "Mapa clustering"
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate     # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install pandas openpyxl sentence-transformers torch umap-learn flask flask-cors
```

4. **Iniciar servidor**
```bash
python clustering_server.py
```

5. **Abrir visualización**
   - Abrir `topic-map-server-dev.html` en navegador
   - El servidor debe estar corriendo en `http://localhost:5000`

## 🚀 Uso

### Procesar Keywords desde Excel

**Formato de Excel requerido:**
```
| Keyword | Topic | Subtopic | Traffic | Volume | Position | KD | URL |
|---------|-------|----------|---------|--------|----------|----|-----|
```

**Opciones de vectorización:**

1. **Excel ya vectorizado** (tiene columnas `keyword_embed_0..767`):
   - Desmarcar "🔄 Vectorizar Excel"
   - Seleccionar vector type (keyword/topic/subtopic)
   - Cargar archivo

2. **Excel sin vectorizar**:
   - Marcar "🔄 Vectorizar Excel"
   - El backend generará embeddings automáticamente
   - Más lento pero no requiere pre-procesamiento

### Vectorización Offline

Para vectorizar Excels sin servidor:

```bash
python vectorize_keywords.py input.xlsx output_vectorized.xlsx
```

### Añadir Topics Personalizados

1. Cargar al menos un Excel (necesario para espacio UMAP)
2. En sección "🎯 Temas Generales Personalizados":
   - Escribir topic (ej: "Seguros de Salud")
   - Click "➕ Añadir"
   - Repetir para más topics
3. Click "⭐ Vectorizar y Mostrar"
4. Aparecerán como estrellas rojas en el mapa

## 🎨 Navegación del Mapa

| Acción | Resultado |
|--------|-----------|
| **Rueda del ratón** | Zoom in/out |
| **Arrastrar** | Pan (mover mapa) |
| **Doble click** | Reset zoom |
| **Zoom > 2x** | Muestra labels de keywords |
| **Hover sobre burbuja** | Tooltip con métricas |

## ⚙️ Configuración

### Parámetros UMAP (clustering_server.py)

```python
# Mayor separación semántica (actual)
n_neighbors = 8   # Vecindario pequeño → clusters definidos
min_dist = 0.4    # Mayor distancia → puntos dispersos

# Valores alternativos:
# n_neighbors = 15, min_dist = 0.1  → clusters compactos (menos separación)
# n_neighbors = 5, min_dist = 0.5   → máxima separación (muy disperso)
```

### Ajustar Zoom Progresivo (topic-map-server-dev.html:577)

```javascript
// Cambiar umbral de zoom para mostrar labels
scale > 2  // Actual: labels aparecen al 200% zoom
scale > 1.5  // Alternativa: labels más tempranos
```

## 📁 Estructura del Proyecto

```
Mapa clustering/
├── clustering_server.py          # Backend Flask con UMAP
├── vectorize_keywords.py         # Script offline de vectorización
├── topic-map-server-dev.html     # Frontend principal (PRODUCCIÓN)
├── topic-map-server.html         # Frontend v1 (legacy)
├── topic-map-vectorized.html     # UMAP client-side (no recomendado)
├── iati-clustering-map.html      # Versión estática legacy
├── start_server.bat              # Shortcut Windows para servidor
├── CLAUDE.md                     # Instrucciones para Claude Code
├── venv/                         # Entorno virtual (gitignored)
└── README.md                     # Este archivo
```

## 🔧 Endpoints API

### `POST /process_excel`
Procesa Excel y retorna coordenadas UMAP + centroides

**Form Data:**
```
file: <Excel file>
vector_type: "keyword" | "topic" | "subtopic"
vectorize: "true" | "false"
n_neighbors: int (default: 8)
min_dist: float (default: 0.4)
```

**Response:**
```json
{
  "keywords": [
    {
      "keyword": "seguro de coche",
      "topic": "Seguros",
      "x": -2.45,
      "y": 3.12,
      "traffic": 1500,
      "volume": 8900,
      "position": 3,
      "kd": 45.2,
      "url": "https://..."
    }
  ],
  "centroids": [
    {
      "topic": "Seguros",
      "x": -2.1,
      "y": 3.0,
      "count": 24,
      "dispersion": 0.85
    }
  ],
  "topics": ["Seguros", "Tecnología", ...]
}
```

### `POST /vectorize_topics`
Añade topics personalizados al espacio UMAP existente

**JSON Body:**
```json
{
  "topics": ["Seguros de Salud", "Fintech"],
  "vector_type": "keyword"
}
```

**Response:**
```json
{
  "general_topics": [
    {
      "topic": "Seguros de Salud",
      "x": -2.3,
      "y": 3.5
    }
  ]
}
```

### `GET /health`
Verificar estado del servidor

## 🐛 Troubleshooting

### Error: "No module named 'flask_cors'"
```bash
pip install flask flask-cors
```

### Error: "Servidor Python no detectado"
- Verificar que `clustering_server.py` esté corriendo
- Comprobar consola del servidor en `http://localhost:5000/health`

### Keywords muy juntas aunque sean diferentes
- Ajustar `n_neighbors` (bajar a 5-8)
- Aumentar `min_dist` (subir a 0.5-0.7)
- Reiniciar servidor después de cambios

### Labels no aparecen al hacer zoom
- Verificar zoom > 2x
- Comprobar consola del navegador por errores
- Refrescar página (Ctrl+F5)

## 🛣️ Roadmap

- [ ] Exportar mapa como PNG/SVG
- [ ] Filtros de búsqueda en tiempo real
- [ ] Clustering jerárquico (HDBSCAN)
- [ ] Integración con APIs de SEO (Ahrefs, SEMrush)
- [ ] Mode oscuro
- [ ] Persistencia de configuración (localStorage)

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles

## 👥 Contribuir

1. Fork del proyecto
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Añadir nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request

## 🙏 Créditos

- **Modelo de Embeddings**: [hiiamsid/sentence_similarity_spanish_es](https://huggingface.co/hiiamsid/sentence_similarity_spanish_es)
- **UMAP**: [McInnes et al.](https://github.com/lmcinnes/umap)
- **D3.js**: [Data-Driven Documents](https://d3js.org/)
- **Sentence Transformers**: [UKPLab](https://www.sbert.net/)

---

**Desarrollado para análisis semántico de keywords SEO en español** 🇪🇸
