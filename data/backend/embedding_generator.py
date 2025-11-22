"""
Generador de embeddings usando sentence-transformers
"""
import logging
from typing import List
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)

# Modelo global para evitar cargarlo múltiples veces
_model: SentenceTransformer = None


def get_embedding_model() -> SentenceTransformer:
    """
    Obtiene o carga el modelo de embeddings.
    Usa un modelo ligero y rápido para producción.
    """
    global _model
    
    if _model is None:
        try:
            # Modelo ligero y rápido: all-MiniLM-L6-v2
            # Vector size: 384
            # Alternativa multilingüe: paraphrase-multilingual-MiniLM-L12-v2 (vector size: 384)
            model_name = "all-MiniLM-L6-v2"
            
            logger.info(f"Cargando modelo de embeddings: {model_name}")
            _model = SentenceTransformer(model_name)
            
            # Usar GPU si está disponible
            if torch.cuda.is_available():
                _model = _model.to('cuda')
                logger.info("Modelo cargado en GPU")
            else:
                logger.info("Modelo cargado en CPU")
                
        except Exception as e:
            logger.error(f"Error al cargar modelo de embeddings: {e}")
            raise
    
    return _model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Genera embeddings para una lista de textos.
    
    Args:
        texts: Lista de textos a convertir en embeddings
    
    Returns:
        Lista de vectores de embeddings
    """
    if not texts:
        return []
    
    try:
        model = get_embedding_model()
        
        # Generar embeddings en batch
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32
        )
        
        # Convertir a lista de listas
        embeddings_list = embeddings.tolist()
        
        logger.info(f"Generados {len(embeddings_list)} embeddings")
        return embeddings_list
        
    except Exception as e:
        logger.error(f"Error al generar embeddings: {e}")
        raise

