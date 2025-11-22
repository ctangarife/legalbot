"""
Cliente para Ollama - Modelos de Lenguaje
"""
import os
import logging
from typing import Optional, List, Dict
import httpx

logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")

# Timeout para peticiones a Ollama (puede tardar en generar respuestas)
REQUEST_TIMEOUT = 300.0  # 5 minutos


async def generate_response(
    prompt: str,
    model: str = DEFAULT_MODEL,
    context: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """
    Genera una respuesta usando Ollama con contexto RAG.
    
    Args:
        prompt: Pregunta del usuario
        model: Nombre del modelo a usar (default: mistral:7b-instruct)
        context: Lista de chunks de texto relevantes para el contexto
        system_prompt: Prompt del sistema para guiar el comportamiento del modelo
        temperature: Controla la creatividad (0.0-1.0). Más bajo = más determinista
        max_tokens: Máximo número de tokens a generar
    
    Returns:
        Respuesta generada por el modelo
    """
    try:
        # Construir el prompt completo con contexto
        logger.debug(f"Construyendo prompt RAG (contexto: {len(context) if context else 0} chunks)")
        full_prompt = build_rag_prompt(prompt, context, system_prompt)
        prompt_length = len(full_prompt)
        logger.info(f"Prompt construido: {prompt_length} caracteres")
        logger.info(f"=== PROMPT COMPLETO ENVIADO A OLLAMA ===\n{full_prompt}\n=== FIN DEL PROMPT ===")
        
        # Preparar el payload para la API de Ollama
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,  # Respuesta completa, no streaming
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        else:
            # Límite por defecto: ~300 palabras ≈ 400 tokens (promedio 1.3 tokens/palabra)
            payload["options"]["num_predict"] = 400
        
        # Realizar petición a Ollama
        logger.info(f"Enviando petición a Ollama (modelo: {model}, URL: {OLLAMA_URL}, timeout: {REQUEST_TIMEOUT}s)")
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                logger.debug(f"POST {OLLAMA_URL}/api/generate")
                response = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json=payload
                )
                logger.info(f"Respuesta recibida de Ollama (status: {response.status_code})")
                response.raise_for_status()
                
                result = response.json()
                generated_text = result.get("response", "")
                
                if not generated_text:
                    logger.warning(f"Ollama retornó respuesta vacía. Resultado completo: {result}")
                    raise Exception("El modelo retornó una respuesta vacía")
                
                logger.info(f"Respuesta generada por Ollama (modelo: {model}, tokens: {result.get('eval_count', 0)}, longitud: {len(generated_text)} caracteres)")
                return generated_text.strip()
            except httpx.TimeoutException as e:
                logger.error(f"Timeout al generar respuesta con Ollama después de {REQUEST_TIMEOUT}s")
                raise Exception(f"El modelo tardó demasiado en responder (más de {REQUEST_TIMEOUT}s). Intenta con una pregunta más corta o menos contexto.")
            except httpx.HTTPStatusError as e:
                error_text = e.response.text if hasattr(e.response, 'text') else str(e.response)
                logger.error(f"Error HTTP {e.response.status_code} de Ollama: {error_text}")
                raise Exception(f"Error al comunicarse con el modelo de lenguaje (HTTP {e.response.status_code}): {error_text}")
            
    except httpx.TimeoutException:
        logger.error(f"Timeout al generar respuesta con Ollama (modelo: {model})")
        raise Exception("El modelo tardó demasiado en responder. Intenta con una pregunta más corta.")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP al comunicarse con Ollama: {e}")
        raise Exception(f"Error al comunicarse con el modelo de lenguaje: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error al generar respuesta con Ollama: {e}")
        raise


def build_rag_prompt(
    user_question: str,
    context_chunks: Optional[List[str]] = None,
    system_prompt: Optional[str] = None
) -> str:
    """
    Construye el prompt completo para RAG con contexto y sistema.
    Optimizado para modelos locales con formato más compacto.
    
    Args:
        user_question: Pregunta del usuario
        context_chunks: Lista de chunks de texto relevantes
        system_prompt: Instrucciones del sistema
    
    Returns:
        Prompt completo formateado
    """
    # Prompt del sistema más corto y directo
    default_system = """Eres un asistente legal especializado en explicar documentos legales de manera clara y natural.
Tu objetivo es ayudar a los usuarios a entender información legal usando lenguaje cotidiano y conversacional.
IMPORTANTE: Solo puedes usar información que esté explícitamente en los documentos proporcionados.
NUNCA inventes, asumas o agregues información que no esté en el contexto.
Si la información no está disponible en los documentos, di claramente que no tienes esa información."""
    
    system = system_prompt or default_system
    
    # Construir el prompt de forma más compacta
    prompt_parts = []
    
    # Instrucciones del sistema (más cortas)
    prompt_parts.append(f"Instrucciones: {system}\n")
    
    # Contexto relevante (chunks del documento) - más compacto
    if context_chunks:
        prompt_parts.append("Contexto del documento:")
        # Limitar cada chunk a máximo 500 caracteres para evitar prompts muy largos
        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = chunk[:500] + "..." if len(chunk) > 500 else chunk
            prompt_parts.append(f"\n[{i}] {chunk_text}")
        prompt_parts.append("")
    
    # Pregunta del usuario
    prompt_parts.append(f"Pregunta: {user_question}\n")
    
    # Instrucción final con límite de palabras y énfasis en no inventar
    prompt_parts.append("""IMPORTANTE - Sigue estas reglas estrictamente:
1. Responde SOLO usando información que esté explícitamente en el contexto proporcionado arriba
2. NUNCA inventes, asumas o agregues información que no esté en los documentos
3. Si la respuesta no está en el contexto, di claramente: "No encontré esa información en los documentos proporcionados"
4. Mantén tu respuesta natural y conversacional, como si estuvieras explicando a un amigo
5. LIMITA tu respuesta a máximo 300 palabras
6. Usa lenguaje claro y sencillo, evitando jerga legal innecesaria

Respuesta:""")
    
    full_prompt = "\n".join(prompt_parts)
    
    # Log del tamaño del prompt
    logger.debug(f"Prompt construido: {len(full_prompt)} caracteres ({len(full_prompt)//4} tokens aprox.)")
    
    return full_prompt


async def check_model_available(model: str = DEFAULT_MODEL) -> bool:
    """
    Verifica si un modelo está disponible en Ollama.
    
    Args:
        model: Nombre del modelo a verificar
    
    Returns:
        True si el modelo está disponible, False en caso contrario
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            
            models_data = response.json()
            # Ollama almacena modelos como "mistral:7b-instruct" o "mistral:latest"
            available_models = [m.get("name", "") for m in models_data.get("models", [])]
            
            # Buscar coincidencia exacta o por base (sin tag)
            model_base = model.split(":")[0]
            is_available = (
                model in available_models or  # Coincidencia exacta
                any(m.startswith(model_base + ":") for m in available_models)  # Cualquier tag del modelo base
            )
            
            if is_available:
                logger.info(f"Modelo {model} está disponible en Ollama")
            else:
                logger.warning(f"Modelo {model} NO está disponible. Modelos disponibles: {available_models}")
            
            return is_available
            
    except Exception as e:
        logger.error(f"Error al verificar modelos disponibles en Ollama: {e}")
        return False


async def list_available_models() -> List[str]:
    """
    Lista todos los modelos disponibles en Ollama.
    
    Returns:
        Lista de nombres de modelos disponibles
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            
            models_data = response.json()
            models = [m.get("name", "") for m in models_data.get("models", [])]
            
            logger.info(f"Modelos disponibles en Ollama: {models}")
            return models
            
    except Exception as e:
        logger.error(f"Error al listar modelos en Ollama: {e}")
        return []

