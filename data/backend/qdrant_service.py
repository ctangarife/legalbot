"""
Cliente para Qdrant - Base de datos vectorial
"""
import os
import uuid
import logging
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "legal_documents")
VECTOR_SIZE = 384  # Tamaño del vector para all-MiniLM-L6-v2

# Cliente Qdrant global
client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """
    Obtiene o crea el cliente de Qdrant.
    """
    global client
    if client is None:
        try:
            client = QdrantClient(url=QDRANT_URL)
            logger.info(f"Cliente Qdrant conectado: {QDRANT_URL}")
        except Exception as e:
            logger.error(f"Error al conectar con Qdrant: {e}")
            raise
    return client


async def ensure_collection():
    """
    Asegura que la colección existe en Qdrant.
    """
    qdrant = get_qdrant_client()
    
    try:
        # Verificar si la colección existe
        collections = qdrant.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if COLLECTION_NAME not in collection_names:
            # Crear la colección
            qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Colección '{COLLECTION_NAME}' creada en Qdrant")
        else:
            logger.info(f"Colección '{COLLECTION_NAME}' ya existe en Qdrant")
            
    except Exception as e:
        logger.error(f"Error al asegurar colección en Qdrant: {e}")
        raise


async def store_embeddings(
    file_id: str,
    chunks: List[Dict],
    embeddings: List[List[float]]
) -> List[str]:
    """
    Almacena los embeddings en Qdrant.
    
    Args:
        file_id: ID del documento
        chunks: Lista de diccionarios con información de cada chunk
        embeddings: Lista de vectores de embeddings
    
    Returns:
        Lista de IDs de puntos creados en Qdrant
    """
    qdrant = get_qdrant_client()
    await ensure_collection()
    
    try:
        points = []
        chunk_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "file_id": file_id,
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "text": chunk["text"],
                    "filename": chunk.get("filename", ""),
                    "file_type": chunk.get("file_type", ""),
                }
            )
            points.append(point)
        
        # Insertar puntos en lote
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        logger.info(f"Almacenados {len(points)} embeddings en Qdrant para documento {file_id}")
        return chunk_ids
        
    except Exception as e:
        logger.error(f"Error al almacenar embeddings en Qdrant: {e}")
        raise


async def search_similar(
    query_embedding: List[float],
    file_id: Optional[str] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Busca chunks similares en Qdrant.
    
    Args:
        query_embedding: Vector de embedding de la consulta
        file_id: Filtrar por file_id específico (opcional)
        limit: Número máximo de resultados
    
    Returns:
        Lista de chunks similares con sus metadatos
    """
    qdrant = get_qdrant_client()
    
    try:
        # Construir filtro si se especifica file_id
        query_filter = None
        if file_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchValue(value=file_id)
                    )
                ]
            )
        
        # Buscar
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit
        )
        
        # Formatear resultados
        formatted_results = []
        for result in results:
            formatted_results.append({
                "chunk_id": result.payload["chunk_id"],
                "text": result.payload["text"],
                "score": result.score,
                "file_id": result.payload["file_id"],
                "filename": result.payload.get("filename", ""),
                "chunk_index": result.payload.get("chunk_index", 0)
            })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error al buscar en Qdrant: {e}")
        raise


async def delete_document_vectors(file_id: str):
    """
    Elimina todos los vectores asociados a un documento.
    
    Args:
        file_id: ID del documento
    """
    qdrant = get_qdrant_client()
    
    try:
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchValue(value=file_id)
                    )
                ]
            )
        )
        logger.info(f"Vectores eliminados para documento {file_id}")
        
    except Exception as e:
        logger.error(f"Error al eliminar vectores de Qdrant: {e}")
        raise

