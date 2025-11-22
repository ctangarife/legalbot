import uuid
import os
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from database import connect_to_mongo, close_mongo_connection, get_database
from models import DocumentModel, DocumentResponse
from document_processor import DocumentProcessor
from embedding_generator import generate_embeddings
from qdrant_service import store_embeddings, ensure_collection, search_similar, delete_document_vectors, get_qdrant_client, COLLECTION_NAME
from qdrant_client.models import Filter
from ollama_client import generate_response, check_model_available, list_available_models

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directorio para almacenar archivos subidos temporalmente
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Tipos de archivo permitidos
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación FastAPI.
    Conecta a MongoDB y Qdrant al iniciar y desconecta al cerrar.
    """
    # Inicio: Conectar a MongoDB y Qdrant
    try:
        await connect_to_mongo()
        logger.info("Aplicación iniciada - MongoDB conectado")
    except Exception as e:
        logger.error(f"Error al conectar MongoDB al iniciar: {e}")
        # Continuar sin MongoDB si falla la conexión inicial
    
    try:
        await ensure_collection()
        logger.info("Aplicación iniciada - Qdrant conectado")
    except Exception as e:
        logger.error(f"Error al conectar Qdrant al iniciar: {e}")
    
    yield
    
    # Cierre: Desconectar
    await close_mongo_connection()
    logger.info("Aplicación cerrada")


app = FastAPI(title="LegalBot API", version="1.0.0", lifespan=lifespan)

# Configurar CORS para permitir conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de respuesta
class UploadResponse(BaseModel):
    success: bool
    message: str
    file_id: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_at: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None

# Modelos para el chat
class ChatRequest(BaseModel):
    question: str
    file_id: Optional[str] = None  # Si se especifica, busca solo en ese documento
    model: Optional[str] = None  # Modelo de Ollama a usar (default: mistral:7b-instruct)
    max_chunks: int = 5  # Número máximo de chunks a usar como contexto
    temperature: float = 0.7  # Creatividad de la respuesta (0.0-1.0)

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict] = []  # Chunks usados como contexto
    model_name: str  # Cambiado de model_used para evitar conflicto con namespace de Pydantic
    tokens_generated: Optional[int] = None


# ==================== ENDPOINTS BÁSICOS ====================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "LegalBot API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Verifica el estado de la API"""
    return {"status": "ok"}


# ==================== FUNCIONES AUXILIARES ====================

def calculate_file_hash(file_contents: bytes) -> str:
    """
    Calcula el hash SHA-256 del contenido del archivo.
    
    Args:
        file_contents: Contenido del archivo en bytes
    
    Returns:
        Hash SHA-256 en formato hexadecimal
    """
    return hashlib.sha256(file_contents).hexdigest()


async def check_duplicate_file(content_hash: str, file_size: Optional[int] = None) -> Optional[Dict]:
    """
    Verifica si ya existe un archivo con el mismo hash de contenido.
    También verifica archivos existentes sin hash calculando su hash si es necesario.
    
    Args:
        content_hash: Hash SHA-256 del contenido del archivo
        file_size: Tamaño del archivo en bytes (opcional, para optimizar búsqueda)
    
    Returns:
        Documento duplicado si existe, None si no hay duplicados
    """
    db = get_database()
    if db is None:
        return None
    
    try:
        # Primero buscar por hash (rápido para archivos nuevos)
        duplicate = await db.documents.find_one({"content_hash": content_hash})
        if duplicate:
            return duplicate
        
        # Si no se encuentra por hash, verificar archivos existentes sin hash
        # Buscar archivos con el mismo tamaño (optimización)
        query = {}
        if file_size is not None:
            query["file_size"] = file_size
        
        # Buscar archivos que no tengan content_hash o tengan un hash diferente
        query["$or"] = [
            {"content_hash": {"$exists": False}},
            {"content_hash": None}
        ]
        
        # Obtener todos los documentos candidatos
        candidates = await db.documents.find(query).to_list(length=100)  # Limitar a 100 para no sobrecargar
        
        # Calcular hash de cada archivo candidato y comparar
        for candidate in candidates:
            file_path = candidate.get("file_path")
            if not file_path:
                continue
            
            # Verificar si el archivo existe en disco
            path_obj = Path(file_path)
            if not path_obj.exists():
                continue
            
            try:
                # Leer archivo y calcular hash
                with open(path_obj, "rb") as f:
                    file_contents = f.read()
                    candidate_hash = calculate_file_hash(file_contents)
                
                # Si los hashes coinciden, es un duplicado
                if candidate_hash == content_hash:
                    # Actualizar el documento existente con el hash para futuras búsquedas rápidas
                    try:
                        await db.documents.update_one(
                            {"_id": candidate["_id"]},
                            {"$set": {"content_hash": candidate_hash}}
                        )
                        logger.info(f"Hash calculado y guardado para archivo existente: {candidate.get('filename', 'N/A')}")
                    except Exception as e:
                        logger.warning(f"No se pudo actualizar hash del archivo existente: {e}")
                    
                    return candidate
            except Exception as e:
                logger.debug(f"Error al calcular hash del archivo candidato {file_path}: {e}")
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Error al verificar duplicados: {e}")
        return None


async def save_document_to_mongo(
    file_id: str,
    filename: str,
    file_size: int,
    file_path: str,
    file_type: str,
    content_hash: str,
    description: Optional[str] = None
) -> Optional[str]:
    """
    Guarda la información del documento en MongoDB.
    
    Args:
        file_id: ID único del archivo
        filename: Nombre original del archivo
        file_size: Tamaño del archivo en bytes
        file_path: Ruta del archivo en el servidor
        file_type: Tipo/extensión del archivo
        content_hash: Hash SHA-256 del contenido del archivo
        description: Descripción opcional
    
    Returns:
        ID del documento en MongoDB o None si falla
    """
    db = get_database()
    if db is None:
        logger.error("MongoDB no está conectado, no se guardará el documento. Verifica la conexión.")
        return None
    
    logger.debug(f"MongoDB conectado, guardando documento {file_id}...")
    
    try:
        document = DocumentModel(
            file_id=file_id,
            filename=filename,
            file_size=file_size,
            file_path=str(file_path),
            file_type=file_type,
            content_hash=content_hash,
            description=description,
            status="uploaded",
            uploaded_at=datetime.utcnow()
        )
        
        # Convertir a dict para MongoDB
        document_dict = document.dict()
        
        # Insertar en la colección de documentos
        result = await db.documents.insert_one(document_dict)
        
        logger.info(f"Documento guardado en MongoDB: {file_id} -> {result.inserted_id}")
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error al guardar documento en MongoDB: {e}", exc_info=True)
        # Retornar None para que el código pueda manejar el error
        return None

async def process_document_after_upload(
    file_id: str,
    file_path: Path,
    filename: str,
    file_type: str
) -> int:
    """
    Procesa un documento después de subirlo: extrae texto, segmenta, genera embeddings y almacena en Qdrant.
    
    Args:
        file_id: ID único del archivo
        file_path: Ruta del archivo
        filename: Nombre del archivo
        file_type: Tipo/extensión del archivo
    
    Returns:
        Número de chunks generados
    """
    processor = DocumentProcessor()
    chunks_count = 0
    
    try:
        # Actualizar estado a "processing"
        db = get_database()
        if db is not None:
            await db.documents.update_one(
                {"file_id": file_id},
                {"$set": {"status": "processing"}}
            )
        
        # Extraer texto del documento
        logger.info(f"Extrayendo texto de {filename}...")
        text = processor.extract_text(str(file_path), file_type)
        
        if not text or len(text.strip()) == 0:
            logger.warning(f"No se pudo extraer texto de {filename}")
            if db is not None:
                await db.documents.update_one(
                    {"file_id": file_id},
                    {"$set": {
                        "status": "error",
                        "metadata": {"error": "No se pudo extraer texto del documento"}
                    }}
                )
            return 0
        
        # Segmentar texto en chunks
        logger.info(f"Segmentando texto de {filename}...")
        chunks = processor.segment_text(text, filename=filename, file_type=file_type)
        chunks_count = len(chunks)
        
        if chunks_count == 0:
            logger.warning(f"No se generaron chunks para {filename}")
            if db is not None:
                await db.documents.update_one(
                    {"file_id": file_id},
                    {"$set": {
                        "status": "error",
                        "metadata": {"error": "No se generaron chunks del documento"}
                    }}
                )
            return 0
        
        # Generar embeddings para cada chunk
        logger.info(f"Generando embeddings para {chunks_count} chunks de {filename}...")
        embeddings = generate_embeddings([chunk["text"] for chunk in chunks])
        
        if len(embeddings) != chunks_count:
            logger.error(f"Error: se generaron {len(embeddings)} embeddings pero hay {chunks_count} chunks")
            if db is not None:
                await db.documents.update_one(
                    {"file_id": file_id},
                    {"$set": {
                        "status": "error",
                        "metadata": {"error": f"Error al generar embeddings: se esperaban {chunks_count} pero se generaron {len(embeddings)}"}
                    }}
                )
            return 0
        
        # Almacenar embeddings en Qdrant
        logger.info(f"Almacenando {chunks_count} embeddings en Qdrant para {filename}...")
        chunk_ids = await store_embeddings(
            file_id=file_id,
            chunks=chunks,
            embeddings=embeddings
        )
        
        # Actualizar estado a "processed" y guardar chunk IDs
        if db is not None:
            await db.documents.update_one(
                {"file_id": file_id},
                {"$set": {
                    "status": "processed",
                    "processed_at": datetime.utcnow(),
                    "chunks": chunk_ids,
                    "metadata": {"chunks_count": chunks_count}
                }}
            )
        
        logger.info(f"Documento {filename} procesado exitosamente: {chunks_count} chunks almacenados")
        
    except Exception as e:
        logger.error(f"Error al procesar documento {filename}: {e}", exc_info=True)
        # Actualizar estado a "error" en MongoDB
        try:
            db = get_database()
            if db is not None:
                await db.documents.update_one(
                    {"file_id": file_id},
                    {"$set": {
                        "status": "error",
                        "metadata": {"processing_error": str(e)}
                    }}
                )
        except:
            pass
    
    return chunks_count


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    files: List[UploadFile] = File(...),
    description: Optional[str] = Form(None)
):
    """
    Endpoint para subir archivos legales (PDF, DOCX, TXT, MD).
    Acepta uno o múltiples archivos, pero procesa solo el primero.
    
    Args:
        files: Lista de archivos a subir (se procesa solo el primero)
        description: Descripción opcional del documento
    
    Returns:
        Información del archivo subido incluyendo file_id único
    """
    try:
        # Validar que haya al menos un archivo
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="No se proporcionó ningún archivo"
            )
        
        # Procesar solo el primer archivo
        file = files[0]
        
        # Validar extensión del archivo
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Generar ID único para el archivo
        file_id = str(uuid.uuid4())
        
        # Crear nombre de archivo único
        original_filename = file.filename
        safe_filename = f"{file_id}{file_ext}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Leer el contenido del archivo
        contents = await file.read()
        file_size = len(contents)
        
        # Validar tamaño (máximo 50MB)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado grande. Tamaño máximo: 50MB"
            )
        
        # Calcular hash del contenido para detectar duplicados
        content_hash = calculate_file_hash(contents)
        logger.info(f"Hash del archivo calculado: {content_hash[:16]}...")
        
        # Verificar si ya existe un archivo con el mismo contenido
        # Incluir file_size para optimizar la búsqueda en archivos existentes
        duplicate = await check_duplicate_file(content_hash, file_size=file_size)
        if duplicate:
            logger.warning(f"Archivo duplicado detectado. Hash: {content_hash[:16]}..., archivo existente: {duplicate.get('filename', 'N/A')}")
            raise HTTPException(
                status_code=409,  # Conflict
                detail={
                    "error": "Archivo duplicado",
                    "message": f"Este archivo ya ha sido subido anteriormente como '{duplicate.get('filename', 'archivo desconocido')}'",
                    "existing_file_id": duplicate.get("file_id"),
                    "existing_filename": duplicate.get("filename"),
                    "uploaded_at": duplicate.get("uploaded_at").isoformat() if duplicate.get("uploaded_at") else None
                }
            )
        
        # Guardar archivo
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Guardar información en MongoDB (post-subida)
        mongo_id = await save_document_to_mongo(
            file_id=file_id,
            filename=original_filename,
            file_size=file_size,
            file_path=file_path,
            file_type=file_ext,
            content_hash=content_hash,
            description=description
        )
        
        # Verificar que se guardó en MongoDB
        if mongo_id is None:
            logger.error(f"No se pudo guardar documento {file_id} en MongoDB")
            raise HTTPException(
                status_code=503,
                detail="No se pudo guardar el documento en la base de datos. MongoDB no está disponible."
            )
        
        # Procesar documento inmediatamente: extraer texto, segmentar, generar embeddings
        chunks_count = await process_document_after_upload(
            file_id=file_id,
            file_path=file_path,
            filename=original_filename,
            file_type=file_ext
        )
        
        # Preparar respuesta
        uploaded_at = datetime.utcnow().isoformat()
        
        return UploadResponse(
            success=True,
            message=f"Archivo subido y procesado exitosamente" + (f" ({chunks_count} chunks)" if chunks_count > 0 else ""),
            file_id=file_id,
            filename=original_filename,
            file_size=file_size,
            uploaded_at=uploaded_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al subir archivo: {str(e)}"
        )

@app.post("/upload/multiple", response_model=List[UploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...)
):
    """
    Endpoint para subir múltiples archivos a la vez.
    Procesa los archivos secuencialmente para evitar sobrecargar el sistema.
    
    Args:
        files: Lista de archivos a subir
    
    Returns:
        Lista con información de cada archivo subido (éxitos y fallos)
    """
    total_files = len(files)
    logger.info(f"Iniciando subida múltiple: {total_files} archivo(s)")
    results = []
    
    for index, file in enumerate(files, 1):
        logger.info(f"Procesando archivo {index}/{total_files}: {file.filename}")
        try:
            # Validar extensión
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                results.append(UploadResponse(
                    success=False,
                    message=f"Tipo de archivo no permitido: {file.filename}",
                    file_id=None,
                    filename=file.filename
                ))
                continue
            
            # Generar ID único
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}{file_ext}"
            file_path = UPLOAD_DIR / safe_filename
            
            # Leer el contenido del archivo
            contents = await file.read()
            file_size = len(contents)
            
            MAX_FILE_SIZE = 50 * 1024 * 1024
            if file_size > MAX_FILE_SIZE:
                results.append(UploadResponse(
                    success=False,
                    message=f"Archivo demasiado grande: {file.filename}",
                    file_id=None,
                    filename=file.filename
                ))
                continue
            
            # Calcular hash del contenido para detectar duplicados
            content_hash = calculate_file_hash(contents)
            
            # Verificar si ya existe un archivo con el mismo contenido
            # Incluir file_size para optimizar la búsqueda en archivos existentes
            duplicate = await check_duplicate_file(content_hash, file_size=file_size)
            if duplicate:
                logger.warning(f"Archivo duplicado detectado en upload múltiple: {file.filename}, hash: {content_hash[:16]}...")
                results.append(UploadResponse(
                    success=False,
                    message=f"Archivo duplicado: Este archivo ya fue subido anteriormente como '{duplicate.get('filename', 'archivo desconocido')}'",
                    file_id=None,
                    filename=file.filename
                ))
                continue
            
            # Guardar archivo
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Guardar información en MongoDB (post-subida)
            mongo_id = await save_document_to_mongo(
                file_id=file_id,
                filename=file.filename,
                file_size=file_size,
                file_path=file_path,
                file_type=file_ext,
                content_hash=content_hash,
                description=None
            )
            
            # Verificar que se guardó en MongoDB
            if mongo_id is None:
                logger.error(f"No se pudo guardar documento {file_id} en MongoDB")
                results.append(UploadResponse(
                    success=False,
                    message="No se pudo guardar el documento en la base de datos. MongoDB no está disponible.",
                    file_id=file_id,
                    filename=file.filename
                ))
                continue
            
            # Procesar documento inmediatamente
            chunks_count = await process_document_after_upload(
                file_id=file_id,
                file_path=file_path,
                filename=file.filename,
                file_type=file_ext
            )
            
            results.append(UploadResponse(
                success=True,
                message=f"Archivo subido y procesado exitosamente" + (f" ({chunks_count} chunks)" if chunks_count > 0 else ""),
                file_id=file_id,
                filename=file.filename,
                file_size=file_size,
                uploaded_at=datetime.utcnow().isoformat()
            ))
        
        except Exception as e:
            logger.error(f"Error al procesar archivo {index}/{total_files} ({file.filename}): {e}", exc_info=True)
            results.append(UploadResponse(
                success=False,
                message=f"Error al procesar {file.filename}: {str(e)}",
                file_id=None,
                filename=file.filename
            ))
    
    # Resumen final
    successful = sum(1 for r in results if r.success)
    failed = total_files - successful
    logger.info(f"Subida múltiple completada: {successful} exitoso(s), {failed} fallido(s) de {total_files} total")
    
    return results


@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents():
    """
    Lista todos los documentos almacenados en MongoDB.
    
    Returns:
        Lista de documentos con su información
    """
    try:
        db = get_database()
        if db is None:
            raise HTTPException(
                status_code=503,
                detail="MongoDB no está disponible"
            )
        
        # Obtener todos los documentos
        cursor = db.documents.find({}).sort("uploaded_at", -1)  # Más recientes primero
        documents = await cursor.to_list(length=None)
        
        # Convertir a formato de respuesta
        result = []
        for doc in documents:
            result.append(DocumentResponse(
                id=str(doc.get("_id")),
                file_id=doc.get("file_id"),
                filename=doc.get("filename"),
                file_size=doc.get("file_size"),
                file_type=doc.get("file_type"),
                description=doc.get("description"),
                status=doc.get("status", "unknown"),
                uploaded_at=doc.get("uploaded_at").isoformat() if doc.get("uploaded_at") else "",
                processed_at=doc.get("processed_at").isoformat() if doc.get("processed_at") else None,
                chunks_count=len(doc.get("chunks", [])),
                metadata=doc.get("metadata", {})
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al listar documentos: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar documentos: {str(e)}"
        )


@app.get("/documents/{file_id}", response_model=DocumentResponse)
async def get_document(file_id: str):
    """
    Obtiene información de un documento específico.
    
    Args:
        file_id: ID único del documento
    
    Returns:
        Información del documento
    """
    try:
        db = get_database()
        if db is None:
            raise HTTPException(
                status_code=503,
                detail="MongoDB no está disponible"
            )
        
        # Buscar documento
        doc = await db.documents.find_one({"file_id": file_id})
        
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Documento con file_id '{file_id}' no encontrado"
            )
        
        return DocumentResponse(
            id=str(doc.get("_id")),
            file_id=doc.get("file_id"),
            filename=doc.get("filename"),
            file_size=doc.get("file_size"),
            file_type=doc.get("file_type"),
            description=doc.get("description"),
            status=doc.get("status", "unknown"),
            uploaded_at=doc.get("uploaded_at").isoformat() if doc.get("uploaded_at") else "",
            processed_at=doc.get("processed_at").isoformat() if doc.get("processed_at") else None,
            chunks_count=len(doc.get("chunks", [])),
            metadata=doc.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener documento: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener documento: {str(e)}"
        )


@app.post("/documents/{file_id}/process")
async def reprocess_document(file_id: str):
    """
    Reprocesa un documento: vuelve a extraer texto, segmentar y generar embeddings.
    Útil si hubo un error en el procesamiento inicial o se actualizó el modelo de embeddings.
    
    Args:
        file_id: ID único del documento a reprocesar
    
    Returns:
        Confirmación de reprocesamiento
    """
    try:
        db = get_database()
        if db is None:
            raise HTTPException(
                status_code=503,
                detail="MongoDB no está disponible"
            )
        
        # Buscar documento
        doc = await db.documents.find_one({"file_id": file_id})
        
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Documento con file_id '{file_id}' no encontrado"
            )
        
        file_path = doc.get("file_path")
        if not file_path:
            raise HTTPException(
                status_code=400,
                detail="El documento no tiene ruta de archivo asociada"
            )
        
        # Verificar que el archivo existe
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise HTTPException(
                status_code=404,
                detail=f"El archivo físico no existe: {file_path}"
            )
        
        # Eliminar vectores antiguos de Qdrant
        try:
            await delete_document_vectors(file_id)
            logger.info(f"Vectores antiguos eliminados de Qdrant para documento {file_id}")
        except Exception as e:
            logger.warning(f"No se pudieron eliminar los vectores antiguos: {e}")
        
        # Reprocesar documento
        filename = doc.get("filename", "unknown")
        file_type = doc.get("file_type", "")
        chunks_count = await process_document_after_upload(
            file_id=file_id,
            file_path=path_obj,
            filename=filename,
            file_type=file_type
        )
        
        return {
            "success": True,
            "message": f"Documento {file_id} reprocesado exitosamente",
            "chunks_count": chunks_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al reprocesar documento: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al reprocesar documento: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal para hacer preguntas sobre los documentos usando RAG.
    
    Flujo RAG:
    1. Convierte la pregunta en embedding
    2. Busca chunks similares en Qdrant
    3. Envía los chunks relevantes + pregunta a Ollama
    4. Retorna la respuesta generada con las fuentes
    
    Args:
        request: Objeto con la pregunta y parámetros opcionales
    
    Returns:
        Respuesta generada con fuentes y metadatos
    """
    try:
        logger.info(f"Chat request received: {request.question}, file_id: {request.file_id}, model: {request.model}")
        # Validar que haya documentos procesados
        db = get_database()
        if db is None:
            logger.error("MongoDB no está disponible para la operación de chat.")
            raise HTTPException(
                status_code=503,
                detail="MongoDB no está disponible"
            )
        
        # Determinar modelo a usar
        model = request.model or "mistral:7b-instruct"
        
        # Verificar que el modelo esté disponible
        is_available = await check_model_available(model)
        if not is_available:
            raise HTTPException(
                status_code=400,
                detail=f"El modelo '{model}' no está disponible en Ollama. Usa GET /models para ver modelos disponibles."
            )
        
        # Generar embedding de la pregunta
        logger.info("Generando embedding de la pregunta...")
        question_embedding = generate_embeddings([request.question])[0]
        
        # Buscar chunks similares en Qdrant
        logger.info(f"Buscando chunks similares en Qdrant (file_id: {request.file_id}, max_chunks: {request.max_chunks})...")
        similar_chunks = await search_similar(
            query_embedding=question_embedding,
            file_id=request.file_id,
            limit=request.max_chunks
        )
        
        if not similar_chunks or len(similar_chunks) == 0:
            logger.warning("No se encontraron chunks relevantes para la pregunta")
            return ChatResponse(
                answer="No se encontró información relevante en los documentos para responder tu pregunta. Por favor, asegúrate de que hay documentos procesados y que la pregunta está relacionada con el contenido de los documentos.",
                sources=[],
                model_name=model
            )
        
        # Extraer los textos de los chunks para el contexto
        # Limitar el tamaño de cada chunk para evitar prompts muy largos
        context_texts = []
        max_chunk_length = 800  # Limitar cada chunk a 800 caracteres
        for chunk in similar_chunks:
            chunk_text = chunk["text"]
            if len(chunk_text) > max_chunk_length:
                # Truncar pero mantener contexto
                chunk_text = chunk_text[:max_chunk_length] + "..."
            context_texts.append(chunk_text)
        
        total_context_length = sum(len(ct) for ct in context_texts)
        logger.info(f"Chat: Encontrados {len(similar_chunks)} chunks relevantes ({total_context_length} caracteres totales), enviando a Ollama...")
        
        # Generar respuesta usando Ollama con contexto RAG
        try:
            answer = await generate_response(
                prompt=request.question,
                model=model,
                context=context_texts,
                temperature=request.temperature
            )
        except Exception as e:
            logger.error(f"Error al generar respuesta con Ollama: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Error al comunicarse con Ollama: {str(e)}"
            )
        
        # Preparar fuentes (chunks usados)
        sources = []
        for chunk in similar_chunks:
            sources.append({
                "chunk_id": chunk.get("chunk_id"),
                "file_id": chunk.get("file_id"),
                "filename": chunk.get("filename", ""),
                "text": chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", ""),
                "relevance_score": chunk.get("score", 0.0),
                "chunk_index": chunk.get("chunk_index", 0)
            })
        
        logger.info(f"Chat: pregunta respondida usando {len(similar_chunks)} chunks, modelo: {model}. Respuesta: {answer[:100]}...")
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            model_name=model
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la pregunta: {str(e)}"
        )


@app.get("/models")
async def list_models():
    """
    Lista todos los modelos disponibles en Ollama.
    
    Returns:
        Lista de modelos disponibles
    """
    try:
        models = await list_available_models()
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        return {
            "ollama_url": ollama_url,
            "models": models
        }
    except Exception as e:
        logger.error(f"Error al listar modelos: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Error al comunicarse con Ollama: {str(e)}"
        )


@app.get("/models/{model}/check")
async def check_model(model: str):
    """
    Verifica si un modelo específico está disponible en Ollama.
    
    Args:
        model: Nombre del modelo a verificar
    
    Returns:
        Estado de disponibilidad del modelo
    """
    try:
        is_available = await check_model_available(model)
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        return {
            "model": model,
            "available": is_available,
            "ollama_url": ollama_url
        }
    except Exception as e:
        logger.error(f"Error al verificar modelo: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Error al comunicarse con Ollama: {str(e)}"
        )


# ==================== NOTA SOBRE LIMPIEZA ====================
# Los endpoints de limpieza han sido removidos por seguridad.
# Para limpiar las bases de datos, usa el script cleanup.py dentro del contenedor:
# docker exec -it legalbot-backend-1 python cleanup.py --help
