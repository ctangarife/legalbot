"""
Modelos de datos para LegalBot
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Wrapper para ObjectId de MongoDB compatible con Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class DocumentModel(BaseModel):
    """
    Modelo para documentos almacenados en MongoDB
    """
    file_id: str = Field(..., description="ID único del archivo (UUID)")
    filename: str = Field(..., description="Nombre original del archivo")
    file_size: int = Field(..., description="Tamaño del archivo en bytes")
    file_path: str = Field(..., description="Ruta del archivo en el servidor")
    file_type: str = Field(..., description="Tipo/extensión del archivo")
    content_hash: str = Field(..., description="Hash SHA-256 del contenido del archivo para detectar duplicados")
    description: Optional[str] = Field(None, description="Descripción opcional del documento")
    status: str = Field(default="uploaded", description="Estado del documento: uploaded, processing, processed, error")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de subida")
    processed_at: Optional[datetime] = Field(None, description="Fecha de procesamiento")
    chunks: List[str] = Field(default_factory=list, description="IDs de los chunks generados")
    metadata: dict = Field(default_factory=dict, description="Metadatos adicionales del documento")
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class DocumentResponse(BaseModel):
    """
    Modelo de respuesta para documentos (sin incluir file_path por seguridad)
    """
    id: Optional[str] = Field(None, alias="_id")
    file_id: str
    filename: str
    file_size: int
    file_type: str
    description: Optional[str] = None
    status: str
    uploaded_at: str
    processed_at: Optional[str] = None
    chunks_count: int = 0
    metadata: dict = {}
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }

