"""
Procesador de documentos - Extracción de texto y segmentación
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional
import fitz  # PyMuPDF
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Procesador de documentos para extraer texto y segmentarlo.
    """
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 200):
        """
        Inicializa el procesador.
        
        Args:
            chunk_size: Tamaño máximo de cada chunk en caracteres
            chunk_overlap: Solapamiento entre chunks en caracteres
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extrae texto de un archivo PDF.
        
        Args:
            file_path: Ruta al archivo PDF
        
        Returns:
            Texto extraído del PDF
        """
        try:
            doc = fitz.open(str(file_path))
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
            
            doc.close()
            full_text = "\n\n".join(text_parts)
            logger.info(f"Texto extraído de PDF: {len(full_text)} caracteres")
            return full_text
            
        except Exception as e:
            logger.error(f"Error al extraer texto del PDF: {e}")
            raise
    
    def extract_text_from_docx(self, file_path: Path) -> str:
        """
        Extrae texto de un archivo DOCX.
        
        Args:
            file_path: Ruta al archivo DOCX
        
        Returns:
            Texto extraído del DOCX
        """
        try:
            doc = DocxDocument(str(file_path))
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Texto extraído de DOCX: {len(full_text)} caracteres")
            return full_text
            
        except Exception as e:
            logger.error(f"Error al extraer texto del DOCX: {e}")
            raise
    
    def extract_text_from_txt(self, file_path: Path) -> str:
        """
        Extrae texto de un archivo de texto plano.
        
        Args:
            file_path: Ruta al archivo TXT
        
        Returns:
            Contenido del archivo
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            logger.info(f"Texto extraído de TXT: {len(text)} caracteres")
            return text
        except Exception as e:
            logger.error(f"Error al leer archivo TXT: {e}")
            raise
    
    def extract_text(self, file_path: Path, file_type: str) -> str:
        """
        Extrae texto de un archivo según su tipo.
        
        Args:
            file_path: Ruta al archivo
            file_type: Tipo de archivo (.pdf, .docx, .txt, .md)
        
        Returns:
            Texto extraído
        """
        file_type_lower = file_type.lower()
        
        if file_type_lower == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type_lower in [".docx", ".doc"]:
            return self.extract_text_from_docx(file_path)
        elif file_type_lower in [".txt", ".md"]:
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {file_type}")
    
    def segment_text(self, text: str, filename: str = "", file_type: str = "") -> List[Dict]:
        """
        Segmenta el texto en chunks con solapamiento.
        
        Args:
            text: Texto a segmentar
            filename: Nombre del archivo (para metadatos)
            file_type: Tipo de archivo (para metadatos)
        
        Returns:
            Lista de chunks con metadatos
        """
        if not text.strip():
            return []
        
        # Limpiar texto
        text = text.strip()
        
        # Intentar segmentar por párrafos primero
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Si el párrafo es muy largo, dividirlo por oraciones
            if len(paragraph) > self.chunk_size:
                sentences = paragraph.split(". ")
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(current_chunk) + len(sentence) + 2 <= self.chunk_size:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            chunks.append({
                                "text": current_chunk.strip(),
                                "filename": filename,
                                "file_type": file_type
                            })
                        current_chunk = sentence + ". "
            else:
                # Si agregar el párrafo excede el tamaño, guardar chunk actual
                if len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                    if current_chunk:
                        chunks.append({
                            "text": current_chunk.strip(),
                            "filename": filename,
                            "file_type": file_type
                        })
                    current_chunk = paragraph + "\n\n"
                else:
                    current_chunk += paragraph + "\n\n"
        
        # Agregar último chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "filename": filename,
                "file_type": file_type
            })
        
        # Aplicar solapamiento entre chunks
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i, chunk in enumerate(chunks):
                text = chunk["text"]
                
                # Agregar texto del chunk anterior al inicio
                if i > 0:
                    prev_text = chunks[i-1]["text"]
                    overlap_text = prev_text[-self.chunk_overlap:]
                    text = overlap_text + "\n\n" + text
                
                # Agregar texto del siguiente chunk al final
                if i < len(chunks) - 1:
                    next_text = chunks[i+1]["text"]
                    overlap_text = next_text[:self.chunk_overlap]
                    text = text + "\n\n" + overlap_text
                
                overlapped_chunks.append({
                    "text": text.strip(),
                    "filename": chunk["filename"],
                    "file_type": chunk["file_type"]
                })
            
            chunks = overlapped_chunks
        
        logger.info(f"Texto segmentado en {len(chunks)} chunks")
        return chunks
    
    def process_document(
        self,
        file_path: Path,
        filename: str,
        file_type: str
    ) -> List[Dict]:
        """
        Procesa un documento completo: extrae texto y lo segmenta.
        
        Args:
            file_path: Ruta al archivo
            filename: Nombre del archivo
            file_type: Tipo de archivo
        
        Returns:
            Lista de chunks con texto y metadatos
        """
        # Extraer texto
        text = self.extract_text(file_path, file_type)
        
        # Segmentar texto
        chunks = self.segment_text(text, filename, file_type)
        
        return chunks

