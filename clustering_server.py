#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servidor Flask para Clustering Semántico con UMAP
Calcula centroides de topics y posiciones UMAP para visualización
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import umap
import sys
import io

# Configurar salida UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__)
CORS(app)  # Permitir requests desde el navegador

# Cargar modelo globalmente (solo una vez)
print("🔄 Cargando modelo de embeddings en español...")
model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')
print("✅ Modelo cargado\n")

# Almacenar estado del último UMAP calculado
umap_state = {
    'reducer': None,
    'embeddings': None,
    'vector_type': None
}

def extract_embeddings(df, prefix):
    """Extrae embeddings de un DataFrame según el prefijo"""
    embed_cols = [col for col in df.columns if col.startswith(prefix)]
    if not embed_cols:
        return None
    embeddings = df[embed_cols].values
    return embeddings

def calculate_umap_2d(embeddings, n_neighbors=8, min_dist=0.4):
    """Calcula UMAP en 2D con parámetros optimizados para mayor separación semántica"""
    print(f"🔄 Calculando UMAP con {len(embeddings)} puntos...")

    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric='cosine',
        random_state=42
    )

    embedding_2d = reducer.fit_transform(embeddings)
    print("✅ UMAP completado")

    return embedding_2d

def calculate_topic_centroids(df, embeddings, umap_coords):
    """Calcula centroides de cada topic en el espacio UMAP"""
    centroids = []

    # Agrupar por topic
    topics = df['Topic'].unique()

    for topic in topics:
        mask = df['Topic'] == topic
        topic_coords = umap_coords[mask]

        # Centroide = promedio de posiciones
        centroid_x = np.mean(topic_coords[:, 0])
        centroid_y = np.mean(topic_coords[:, 1])

        # Contar keywords en el topic
        count = np.sum(mask)

        # Calcular dispersión (desviación estándar)
        dispersion = np.std(topic_coords, axis=0).mean()

        centroids.append({
            'topic': topic,
            'x': float(centroid_x),
            'y': float(centroid_y),
            'count': int(count),
            'dispersion': float(dispersion)
        })

    return centroids

def vectorize_general_topics(general_topics):
    """Vectoriza topics generales usando el modelo"""
    print(f"🔄 Vectorizando {len(general_topics)} topics generales...")
    embeddings = model.encode(general_topics)
    print("✅ Topics generales vectorizados")
    return embeddings

@app.route('/process_excel', methods=['POST'])
def process_excel():
    """Endpoint principal: procesa Excel y retorna datos para visualización"""
    try:
        # Obtener archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No se recibió archivo'}), 400

        file = request.files['file']
        vector_type = request.form.get('vector_type', 'keyword')
        n_neighbors = int(request.form.get('n_neighbors', 8))
        min_dist = float(request.form.get('min_dist', 0.4))
        vectorize_file = request.form.get('vectorize', 'false').lower() == 'true'

        print(f"\n📂 Procesando archivo: {file.filename}")
        print(f"   Vector type: {vector_type}")
        print(f"   UMAP params: n_neighbors={n_neighbors}, min_dist={min_dist}")
        print(f"   Vectorizar archivo: {vectorize_file}")

        # Leer Excel
        df = pd.read_excel(file)
        print(f"✅ Excel leído: {len(df)} filas")

        # Si hay que vectorizar, generar embeddings
        if vectorize_file:
            print("🔄 Vectorizando Keywords, Topics y Subtopics...")

            # Vectorizar Keywords
            if 'Keyword' in df.columns:
                keyword_embeddings = model.encode(df['Keyword'].fillna('').tolist())
                for i in range(keyword_embeddings.shape[1]):
                    df[f'keyword_embed_{i}'] = keyword_embeddings[:, i]
                print(f"   ✅ Keywords vectorizadas: {keyword_embeddings.shape[1]} dimensiones")

            # Vectorizar Topics
            if 'Topic' in df.columns:
                topic_embeddings = model.encode(df['Topic'].fillna('').tolist())
                for i in range(topic_embeddings.shape[1]):
                    df[f'topic_embed_{i}'] = topic_embeddings[:, i]
                print(f"   ✅ Topics vectorizados: {topic_embeddings.shape[1]} dimensiones")

            # Vectorizar Subtopics
            if 'Subtopic' in df.columns:
                subtopic_embeddings = model.encode(df['Subtopic'].fillna('').tolist())
                for i in range(subtopic_embeddings.shape[1]):
                    df[f'subtopic_embed_{i}'] = subtopic_embeddings[:, i]
                print(f"   ✅ Subtopics vectorizados: {subtopic_embeddings.shape[1]} dimensiones")

        # Extraer embeddings
        prefix = f'{vector_type}_embed_'
        embeddings = extract_embeddings(df, prefix)

        if embeddings is None:
            return jsonify({'error': f'No se encontraron columnas {prefix}*. ¿Activaste la opción de vectorizar?'}), 400

        print(f"✅ Embeddings extraídos: {embeddings.shape}")

        # Calcular UMAP y guardar el reducer para usarlo después
        reducer = umap.UMAP(
            n_components=2,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            metric='cosine',
            random_state=42
        )
        umap_coords = reducer.fit_transform(embeddings)

        # Guardar estado para topics generales
        umap_state['reducer'] = reducer
        umap_state['embeddings'] = embeddings
        umap_state['vector_type'] = vector_type

        # Calcular centroides de topics
        centroids = calculate_topic_centroids(df, embeddings, umap_coords)

        # Preparar datos de keywords
        keywords_data = []
        for idx, row in df.iterrows():
            keywords_data.append({
                'id': int(idx),
                'keyword': str(row.get('Keyword', '')),
                'traffic': int(row.get('Traffic', 0)),
                'volume': int(row.get('Volume', 0)),
                'position': int(row.get('Position', 0)),
                'kd': float(row.get('KD', 0)),
                'topic': str(row.get('Topic', 'Miscellaneous')),
                'subtopic': str(row.get('Subtopic', '')),
                'url': str(row.get('URL', '')),
                'x': float(umap_coords[idx, 0]),
                'y': float(umap_coords[idx, 1])
            })

        print(f"✅ Datos preparados: {len(keywords_data)} keywords, {len(centroids)} centroides")

        return jsonify({
            'keywords': keywords_data,
            'centroids': centroids,
            'topics': list(df['Topic'].unique())
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/vectorize_topics', methods=['POST'])
def vectorize_topics():
    """Endpoint para vectorizar topics generales y posicionarlos en el mapa existente"""
    try:
        data = request.json
        topics = data.get('topics', [])
        vector_type = data.get('vector_type', 'keyword')

        if not topics:
            return jsonify({'error': 'No se recibieron topics'}), 400

        # Verificar que hay un UMAP previo
        if umap_state['reducer'] is None:
            return jsonify({'error': 'Primero debes cargar un archivo Excel para generar el espacio UMAP'}), 400

        print(f"\n🎯 Vectorizando {len(topics)} topics generales")
        print(f"   Topics: {topics}")

        # Vectorizar topics generales usando el modelo
        topic_embeddings = vectorize_general_topics(topics)

        # Usar el UMAP ya entrenado para transformar los nuevos puntos
        print("🔄 Proyectando topics generales en el espacio UMAP existente...")

        # UMAP transform: proyectar nuevos puntos en el espacio ya calculado
        try:
            coords_2d = umap_state['reducer'].transform(topic_embeddings)
        except Exception as e:
            print(f"⚠️ Warning: No se pudo usar transform, recalculando UMAP completo...")
            # Si transform falla, combinar y recalcular
            all_embeddings = np.vstack([umap_state['embeddings'], topic_embeddings])
            reducer = umap.UMAP(
                n_components=2,
                n_neighbors=15,
                min_dist=0.1,
                metric='cosine',
                random_state=42
            )
            all_coords = reducer.fit_transform(all_embeddings)
            coords_2d = all_coords[-len(topics):]

        general_points = []
        for i, topic in enumerate(topics):
            general_points.append({
                'topic': topic,
                'x': float(coords_2d[i, 0]),
                'y': float(coords_2d[i, 1]),
                'is_general': True
            })

        print(f"✅ Topics generales vectorizados y posicionados en el mapa")

        return jsonify({
            'general_topics': general_points
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar que el servidor está activo"""
    return jsonify({'status': 'ok', 'model': 'hiiamsid/sentence_similarity_spanish_es'})

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 SERVIDOR DE CLUSTERING SEMÁNTICO")
    print("=" * 70)
    print("\n📍 Servidor iniciando en http://localhost:5000")
    print("📊 Endpoints disponibles:")
    print("   - POST /process_excel      → Procesar Excel y calcular UMAP")
    print("   - POST /vectorize_topics   → Vectorizar temas generales personalizados")
    print("   - GET  /health             → Verificar estado del servidor")
    print("\n✅ Listo para recibir requests\n")

    app.run(debug=True, port=5000, host='0.0.0.0')
