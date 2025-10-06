#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para vectorizar Keywords, Topics y Subtopics de archivos Excel
Utiliza un modelo de Hugging Face optimizado para español
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import sys
import os
from pathlib import Path

# Configurar la salida para manejar Unicode correctamente en Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_spanish_model():
    """
    Carga el modelo de embeddings en español desde Hugging Face
    Usamos 'hiiamsid/sentence_similarity_spanish_es' que es excelente para español
    """
    print("🔄 Cargando modelo de embeddings en español...")
    model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')
    print("✅ Modelo cargado correctamente\n")
    return model

def vectorize_text(model, texts):
    """
    Vectoriza una lista de textos usando el modelo
    """
    # Convertir a strings y manejar valores nulos
    texts = [str(text) if pd.notna(text) else "" for text in texts]

    # Generar embeddings
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

def process_excel(input_file, output_file=None):
    """
    Procesa el archivo Excel, vectoriza las columnas y guarda el resultado
    """
    # Validar que el archivo existe
    if not os.path.exists(input_file):
        print(f"❌ Error: El archivo '{input_file}' no existe")
        return False

    print(f"📂 Leyendo archivo: {input_file}")

    try:
        # Leer el Excel
        df = pd.read_excel(input_file)
        print(f"✅ Archivo leído correctamente: {len(df)} filas\n")

        # Mostrar columnas disponibles
        print("📋 Columnas encontradas:", list(df.columns))
        print()

        # Verificar que existen las columnas necesarias
        required_columns = ['Keyword', 'Topic']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"❌ Error: Faltan las columnas: {missing_columns}")
            return False

        # Cargar el modelo
        model = load_spanish_model()

        # Vectorizar Keyword
        print("🔄 Vectorizando Keywords...")
        keyword_embeddings = vectorize_text(model, df['Keyword'])

        # Agregar embeddings de keywords como múltiples columnas
        for i in range(keyword_embeddings.shape[1]):
            df[f'keyword_embed_{i}'] = keyword_embeddings[:, i]
        print(f"✅ Keywords vectorizadas: {keyword_embeddings.shape[1]} dimensiones\n")

        # Vectorizar Topic
        print("🔄 Vectorizando Topics...")
        topic_embeddings = vectorize_text(model, df['Topic'])

        # Agregar embeddings de topics
        for i in range(topic_embeddings.shape[1]):
            df[f'topic_embed_{i}'] = topic_embeddings[:, i]
        print(f"✅ Topics vectorizados: {topic_embeddings.shape[1]} dimensiones\n")

        # Vectorizar Subtopic si existe
        if 'Subtopic' in df.columns:
            print("🔄 Vectorizando Subtopics...")
            subtopic_embeddings = vectorize_text(model, df['Subtopic'])

            # Agregar embeddings de subtopics
            for i in range(subtopic_embeddings.shape[1]):
                df[f'subtopic_embed_{i}'] = subtopic_embeddings[:, i]
            print(f"✅ Subtopics vectorizados: {subtopic_embeddings.shape[1]} dimensiones\n")

        # Determinar nombre del archivo de salida
        if output_file is None:
            input_path = Path(input_file)
            output_file = str(input_path.parent / f"{input_path.stem}_vectorizado{input_path.suffix}")

        # Guardar el resultado
        print(f"💾 Guardando archivo vectorizado: {output_file}")
        df.to_excel(output_file, index=False)
        print(f"✅ Archivo guardado exitosamente\n")

        # Mostrar resumen
        print("📊 RESUMEN:")
        print(f"   - Total de filas procesadas: {len(df)}")
        print(f"   - Columnas originales: {len(df.columns) - keyword_embeddings.shape[1] * (3 if 'Subtopic' in df.columns else 2)}")
        print(f"   - Columnas de embeddings agregadas: {keyword_embeddings.shape[1] * (3 if 'Subtopic' in df.columns else 2)}")
        print(f"   - Total de columnas en archivo final: {len(df.columns)}")
        print(f"   - Archivo de salida: {output_file}")

        return True

    except Exception as e:
        print(f"❌ Error al procesar el archivo: {str(e)}")
        return False

def main():
    """
    Función principal
    """
    print("=" * 60)
    print("🚀 VECTORIZADOR DE KEYWORDS SEO")
    print("   Embeddings en español con Hugging Face")
    print("=" * 60)
    print()

    # Verificar argumentos
    if len(sys.argv) < 2:
        print("📖 Uso: python vectorize_keywords.py <archivo_excel.xlsx> [archivo_salida.xlsx]")
        print()
        print("Ejemplo:")
        print("  python vectorize_keywords.py datos.xlsx")
        print("  python vectorize_keywords.py datos.xlsx datos_vectorizados.xlsx")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Procesar el archivo
    success = process_excel(input_file, output_file)

    if success:
        print("\n✅ ¡Proceso completado exitosamente!")
    else:
        print("\n❌ El proceso falló. Revisa los errores anteriores.")
        sys.exit(1)

if __name__ == "__main__":
    main()
