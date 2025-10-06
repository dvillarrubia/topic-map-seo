# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **semantic SEO keyword clustering visualization system** that combines Python backend processing with interactive D3.js visualizations. The system vectorizes Spanish keywords using sentence transformers, performs dimensionality reduction with UMAP, and displays semantic relationships in interactive bubble maps.

## Architecture

### Two-Tier System

**Python Backend (`clustering_server.py`)**
- Flask server running on `http://localhost:5000`
- Uses `sentence-transformers` with Spanish model: `hiiamsid/sentence_similarity_spanish_es`
- Generates 768-dimensional embeddings for Keywords, Topics, and Subtopics
- Performs UMAP dimensionality reduction (768D → 2D) for visualization
- Calculates topic centroids in the UMAP space
- Maintains state (`umap_state`) to project new custom topics into existing UMAP space

**Frontend (HTML/React/D3.js)**
- Three visualization modes:
  - `topic-map-server.html`: Full-featured map with Python backend (recommended)
  - `topic-map-vectorized.html`: Client-side UMAP (limited, not recommended)
  - `iati-clustering-map.html`: Legacy static map
- Communicates with Flask server via REST API
- Renders bubble charts with D3.js showing semantic clusters
- Interactive tooltips, filters, and topic legends

### Data Flow

1. **Excel Input** → Contains columns: `Keyword`, `Topic`, `Subtopic`, `Traffic`, `Volume`, `Position`, `KD`, `URL`
2. **Vectorization** (optional) → Python generates embeddings: `keyword_embed_0..767`, `topic_embed_0..767`, `subtopic_embed_0..767`
3. **UMAP Projection** → Python reduces to 2D coordinates `(x, y)`
4. **Centroid Calculation** → Python calculates mean position per topic
5. **Visualization** → D3.js renders bubbles (keywords), circles (centroids), stars (custom topics)

## Commands

### Environment Setup
```bash
# Activate virtual environment (Windows)
source venv/Scripts/activate

# Install dependencies
pip install pandas openpyxl sentence-transformers torch umap-learn flask flask-cors
```

### Running the System

**Start Flask Server** (required for topic-map-server.html):
```bash
python clustering_server.py
# Or double-click: start_server.bat
```

**Vectorize Excel Files** (standalone script):
```bash
python vectorize_keywords.py input.xlsx [output.xlsx]
# Adds embedding columns to Excel
```

### Server Endpoints

- `POST /process_excel` - Process Excel with optional vectorization
  - Form params: `file`, `vector_type` (keyword/topic/subtopic), `vectorize` (true/false)
  - Returns: keywords data, centroids, topics list

- `POST /vectorize_topics` - Add custom topics to existing UMAP space
  - JSON body: `{"topics": ["Topic 1", "Topic 2"], "vector_type": "keyword"}`
  - Returns: projected coordinates for custom topics

- `GET /health` - Server health check

## Key Implementation Details

### UMAP State Management
The server maintains `umap_state` dict to reuse the fitted UMAP reducer:
- After processing Excel, stores `reducer`, `embeddings`, `vector_type`
- When adding custom topics, uses `reducer.transform()` to project new points into existing space
- Falls back to full recalculation if transform fails

### Embedding Column Convention
Vectorized Excel files use predictable column naming:
- Keywords: `keyword_embed_0`, `keyword_embed_1`, ..., `keyword_embed_767`
- Topics: `topic_embed_0`, `topic_embed_1`, ..., `topic_embed_767`
- Subtopics: `subtopic_embed_0`, `subtopic_embed_1`, ..., `subtopic_embed_767`

Extract with: `df.columns[df.columns.str.startswith('{type}_embed_')]`

### Visualization Elements
- **Bubbles (small circles)**: Individual keywords, size = traffic/volume/position
- **Centroids (large circles)**: Topic centers, labeled with topic name + count
- **Stars (red)**: Custom general topics, positioned via UMAP transform

### Color Mapping
Topics are assigned colors from `TOPIC_COLOR_PALETTE` (36 colors) consistently:
- Global `TOPIC_COLOR_MAP` dict maps topic → color
- Populated on first data load with sorted topic list
- Ensures same topic always gets same color across sessions

## Excel Data Requirements

**Input Excel must contain these columns:**
- `Keyword` (string) - The search keyword
- `Topic` (string) - Primary topic category
- `Subtopic` (string, optional) - Secondary category
- `Traffic` (int) - Organic traffic
- `Volume` (int) - Search volume
- `Position` (int) - Search ranking position
- `KD` (float) - Keyword difficulty percentage
- `URL` (string) - Target URL

**Vectorized Excel adds:**
- 768 columns per text field (keyword, topic, subtopic)
- Use `vectorize_keywords.py` or check "Vectorizar Excel" in UI

## Common Workflows

### Processing a New Dataset
1. Start server: `python clustering_server.py`
2. Open `topic-map-server.html` in browser
3. Upload Excel file
4. Check "🔄 Vectorizar Excel" if file lacks embeddings
5. Select vector type (keyword/topic/subtopic)
6. View UMAP projection and centroids

### Adding Custom Topics
1. Ensure Excel is already loaded (UMAP space must exist)
2. Enter custom topic in "🎯 Temas Generales Personalizados" section
3. Click "➕ Añadir" to add to list
4. Click "⭐ Vectorizar y Mostrar"
5. Red stars appear showing semantic position of custom topics

### Standalone Vectorization
```bash
# Vectorize Excel offline (no server needed)
python vectorize_keywords.py original.xlsx vectorized.xlsx

# Output: Excel with 2,314 columns (10 original + 2,304 embeddings)
# Then use vectorized.xlsx in any visualization
```

## Technical Constraints

- **Spanish Model Only**: Embeddings optimized for Spanish text (`hiiamsid/sentence_similarity_spanish_es`)
- **UMAP Parameters**: `n_neighbors=15`, `min_dist=0.1`, `metric='cosine'` - tuned for semantic SEO clustering
- **Windows UTF-8 Handling**: Both Python scripts reconfigure stdout/stderr for Windows emoji/Unicode support
- **Browser CORS**: Flask server enables CORS to allow file:// protocol HTML files to make requests
- **State Limitation**: `umap_state` is in-memory only, resets on server restart

## File Reference

- **clustering_server.py** - Flask REST API server with UMAP/embedding logic
- **vectorize_keywords.py** - CLI tool for offline Excel vectorization
- **topic-map-server.html** - Primary visualization (requires server)
- **topic-map-vectorized.html** - Client-side UMAP (slower, less accurate)
- **iati-clustering-map.html** - Legacy visualization (no vectorization)
- **start_server.bat** - Windows shortcut to start Flask server
