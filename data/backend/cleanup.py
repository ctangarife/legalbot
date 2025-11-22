#!/usr/bin/env python3
"""
Script de limpieza de bases de datos para LegalBot.
Este script solo debe ejecutarse dentro del contenedor Docker.

Uso:
    docker exec -it legalbot-backend-1 python cleanup.py --help
    docker exec -it legalbot-backend-1 python cleanup.py --all
    docker exec -it legalbot-backend-1 python cleanup.py --document <file_id>
    docker exec -it legalbot-backend-1 python cleanup.py --mongodb-only
    docker exec -it legalbot-backend-1 python cleanup.py --qdrant-only
"""
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional

from database import connect_to_mongo, close_mongo_connection, get_database
from qdrant_service import delete_document_vectors, get_qdrant_client, COLLECTION_NAME
from qdrant_client.models import Filter

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorio de uploads
UPLOAD_DIR = Path("/app/uploads")


async def delete_single_document(file_id: str):
    """
    Elimina un documento específico de MongoDB, Qdrant y el sistema de archivos.
    
    Args:
        file_id: ID del documento a eliminar
    """
    db = get_database()
    if db is None:
        logger.error("MongoDB no está disponible")
        return False
    
    try:
        # Buscar el documento en MongoDB
        document = await db.documents.find_one({"file_id": file_id})
        if not document:
            logger.error(f"Documento con file_id '{file_id}' no encontrado")
            return False
        
        filename = document.get("filename", "unknown")
        logger.info(f"Eliminando documento: {filename} ({file_id})")
        
        # Eliminar archivo del sistema de archivos
        file_path = document.get("file_path")
        if file_path:
            try:
                path_obj = Path(file_path)
                if path_obj.exists():
                    path_obj.unlink()
                    logger.info(f"✓ Archivo eliminado: {file_path}")
                else:
                    logger.warning(f"Archivo no existe: {file_path}")
            except Exception as e:
                logger.error(f"Error al eliminar archivo {file_path}: {e}")
        
        # Eliminar vectores de Qdrant
        try:
            await delete_document_vectors(file_id)
            logger.info(f"✓ Vectores eliminados de Qdrant")
        except Exception as e:
            logger.error(f"Error al eliminar vectores de Qdrant: {e}")
        
        # Eliminar documento de MongoDB
        result = await db.documents.delete_one({"file_id": file_id})
        
        if result.deleted_count > 0:
            logger.info(f"✓ Documento eliminado de MongoDB")
            return True
        else:
            logger.error(f"No se pudo eliminar el documento de MongoDB")
            return False
        
    except Exception as e:
        logger.error(f"Error al eliminar documento: {e}", exc_info=True)
        return False


async def delete_all_documents():
    """
    Elimina TODOS los documentos de MongoDB, Qdrant y el sistema de archivos.
    """
    db = get_database()
    if db is None:
        logger.error("MongoDB no está disponible")
        return False
    
    try:
        # Obtener todos los documentos antes de eliminarlos
        all_documents = await db.documents.find({}).to_list(length=None)
        total_docs = len(all_documents)
        
        if total_docs == 0:
            logger.info("No hay documentos para eliminar")
            return True
        
        logger.warning(f"⚠️  Se eliminarán {total_docs} documentos")
        
        deleted_files = 0
        deleted_vectors = 0
        errors = []
        
        # Eliminar cada documento individualmente
        for i, doc in enumerate(all_documents, 1):
            file_id = doc.get("file_id")
            filename = doc.get("filename", "unknown")
            logger.info(f"[{i}/{total_docs}] Eliminando: {filename} ({file_id})")
            
            # Eliminar archivo del sistema
            file_path = doc.get("file_path")
            if file_path:
                try:
                    path_obj = Path(file_path)
                    if path_obj.exists():
                        path_obj.unlink()
                        deleted_files += 1
                except Exception as e:
                    error_msg = f"Error eliminando archivo {file_path}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Eliminar vectores de Qdrant
            try:
                await delete_document_vectors(file_id)
                deleted_vectors += 1
            except Exception as e:
                error_msg = f"Error eliminando vectores de {file_id}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Eliminar todos los documentos de MongoDB
        result = await db.documents.delete_many({})
        
        logger.info("=" * 60)
        logger.info("RESUMEN DE ELIMINACIÓN:")
        logger.info(f"  Documentos MongoDB: {result.deleted_count}/{total_docs}")
        logger.info(f"  Archivos eliminados: {deleted_files}/{total_docs}")
        logger.info(f"  Documentos Qdrant: {deleted_vectors}/{total_docs}")
        if errors:
            logger.warning(f"  Errores: {len(errors)}")
            for error in errors[:5]:  # Mostrar solo los primeros 5
                logger.warning(f"    - {error}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error al eliminar todos los documentos: {e}", exc_info=True)
        return False


async def clear_qdrant_only():
    """
    Limpia TODOS los vectores de Qdrant sin tocar MongoDB ni archivos.
    """
    try:
        qdrant = get_qdrant_client()
        
        # Obtener información de la colección antes de limpiar
        collection_info = qdrant.get_collection(COLLECTION_NAME)
        points_count_before = collection_info.points_count
        
        if points_count_before == 0:
            logger.info("Qdrant ya está vacío")
            return True
        
        logger.warning(f"⚠️  Se eliminarán {points_count_before} vectores de Qdrant")
        
        # Eliminar todos los puntos de la colección
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(must=[])  # Filtro vacío = todos los puntos
        )
        
        # Verificar que se eliminaron
        collection_info_after = qdrant.get_collection(COLLECTION_NAME)
        points_count_after = collection_info_after.points_count
        
        logger.info("=" * 60)
        logger.info("QDRANT LIMPIADO:")
        logger.info(f"  Vectores antes: {points_count_before}")
        logger.info(f"  Vectores después: {points_count_after}")
        logger.info(f"  Vectores eliminados: {points_count_before - points_count_after}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error al limpiar Qdrant: {e}", exc_info=True)
        return False


async def clear_mongodb_only():
    """
    Limpia TODOS los documentos de MongoDB sin tocar archivos ni Qdrant.
    """
    try:
        db = get_database()
        if db is None:
            logger.error("MongoDB no está disponible")
            return False
        
        # Contar documentos antes de eliminar
        count_before = await db.documents.count_documents({})
        
        if count_before == 0:
            logger.info("MongoDB ya está vacío")
            return True
        
        logger.warning(f"⚠️  Se eliminarán {count_before} documentos de MongoDB")
        
        # Eliminar todos los documentos
        result = await db.documents.delete_many({})
        
        logger.info("=" * 60)
        logger.info("MONGODB LIMPIADO:")
        logger.info(f"  Documentos antes: {count_before}")
        logger.info(f"  Documentos eliminados: {result.deleted_count}")
        logger.info(f"  Documentos después: 0")
        logger.info("  NOTA: Los archivos físicos y vectores en Qdrant NO fueron eliminados")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error al limpiar MongoDB: {e}", exc_info=True)
        return False


async def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Script de limpieza de bases de datos para LegalBot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Eliminar un documento específico
  python cleanup.py --document 550e8400-e29b-41d4-a716-446655440000
  
  # Eliminar todos los documentos (MongoDB + Qdrant + archivos)
  python cleanup.py --all
  
  # Limpiar solo MongoDB
  python cleanup.py --mongodb-only
  
  # Limpiar solo Qdrant
  python cleanup.py --qdrant-only
        """
    )
    
    parser.add_argument(
        "--document",
        type=str,
        help="ID del documento específico a eliminar"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Eliminar TODOS los documentos (MongoDB + Qdrant + archivos)"
    )
    
    parser.add_argument(
        "--mongodb-only",
        action="store_true",
        help="Limpiar solo MongoDB (sin tocar archivos ni Qdrant)"
    )
    
    parser.add_argument(
        "--qdrant-only",
        action="store_true",
        help="Limpiar solo Qdrant (sin tocar MongoDB ni archivos)"
    )
    
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirmar operaciones destructivas (requerido para --all)"
    )
    
    args = parser.parse_args()
    
    # Validar que se haya especificado una opción
    if not any([args.document, args.all, args.mongodb_only, args.qdrant_only]):
        parser.print_help()
        return
    
    # Conectar a las bases de datos
    try:
        await connect_to_mongo()
        logger.info("Conectado a MongoDB")
    except Exception as e:
        logger.error(f"Error al conectar con MongoDB: {e}")
        return
    
    try:
        success = False
        
        if args.document:
            # Eliminar documento específico
            success = await delete_single_document(args.document)
        
        elif args.all:
            # Eliminar todos los documentos
            if not args.confirm:
                logger.error("⚠️  Para eliminar TODOS los documentos, debes usar --confirm")
                logger.error("   Ejemplo: python cleanup.py --all --confirm")
                return
            
            success = await delete_all_documents()
        
        elif args.mongodb_only:
            # Limpiar solo MongoDB
            if not args.confirm:
                logger.error("⚠️  Para limpiar MongoDB, debes usar --confirm")
                logger.error("   Ejemplo: python cleanup.py --mongodb-only --confirm")
                return
            
            success = await clear_mongodb_only()
        
        elif args.qdrant_only:
            # Limpiar solo Qdrant
            if not args.confirm:
                logger.error("⚠️  Para limpiar Qdrant, debes usar --confirm")
                logger.error("   Ejemplo: python cleanup.py --qdrant-only --confirm")
                return
            
            success = await clear_qdrant_only()
        
        if success:
            logger.info("✓ Operación completada exitosamente")
        else:
            logger.error("✗ La operación falló")
            exit(1)
    
    finally:
        await close_mongo_connection()
        logger.info("Conexión cerrada")


if __name__ == "__main__":
    asyncio.run(main())

