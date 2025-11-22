"""
Módulo de conexión a MongoDB para LegalBot
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

logger = logging.getLogger(__name__)

# Configuración de MongoDB desde variables de entorno
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:admin123@mongodb:27017/?authSource=admin")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "legalbot")

# Cliente MongoDB global
client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """
    Conecta a MongoDB usando las variables de entorno.
    """
    global client, database
    
    try:
        client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Verificar conexión
        await client.admin.command('ping')
        
        database = client[DATABASE_NAME]
        
        # Crear índices necesarios
        await create_indexes()
        
        logger.info(f"Conectado exitosamente a MongoDB: {DATABASE_NAME}")
        return database
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Error al conectar con MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al conectar con MongoDB: {e}")
        raise


async def close_mongo_connection():
    """
    Cierra la conexión con MongoDB.
    """
    global client
    if client is not None:
        client.close()
        logger.info("Conexión a MongoDB cerrada")


async def create_indexes():
    """
    Crea los índices necesarios en las colecciones de MongoDB.
    """
    if database is None:
        return
    
    try:
        # Índices para la colección de documentos
        documents_collection = database.documents
        
        # Índice único en file_id
        await documents_collection.create_index("file_id", unique=True)
        
        # Índice en filename para búsquedas
        await documents_collection.create_index("filename")
        
        # Índice en uploaded_at para ordenamiento
        await documents_collection.create_index("uploaded_at")
        
        # Índice en status para filtros
        await documents_collection.create_index("status")
        
        # Índice único en content_hash para detectar duplicados
        # sparse=True permite que documentos sin content_hash no causen conflictos
        try:
            await documents_collection.create_index("content_hash", unique=True, sparse=True)
            logger.info("Índice único en content_hash creado")
        except Exception as e:
            # Si ya existe o hay error, registrar pero continuar
            logger.debug(f"Índice content_hash: {e}")
        
        logger.info("Índices de MongoDB creados exitosamente")
        
    except Exception as e:
        logger.warning(f"Error al crear índices (puede que ya existan): {e}")


def get_database():
    """
    Retorna la instancia de la base de datos.
    """
    return database

