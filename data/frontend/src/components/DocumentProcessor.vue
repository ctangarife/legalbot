<template>
  <div class="document-processor">
    <div class="processor-header">
      <h2>Procesar Documentos</h2>
      <p>Sube documentos legales (PDF) para procesarlos y hacer consultas sobre ellos</p>
    </div>

    <div class="upload-section">
      <div 
        class="upload-area"
        :class="{ 'dragover': isDragging, 'has-files': uploadedFiles.length > 0 }"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          multiple
          @change="handleFileSelect"
          class="file-input"
        />
        <div class="upload-content">
          <div class="upload-icon">📄</div>
          <h3>Arrastra archivos aquí</h3>
          <p>o haz clic para seleccionar</p>
          <p class="upload-hint">Formatos permitidos: PDF</p>
        </div>
      </div>

      <div v-if="uploadedFiles.length > 0" class="files-list">
        <h3>Archivos seleccionados ({{ uploadedFiles.length }})</h3>
        <div class="file-items">
          <div 
            v-for="(file, index) in uploadedFiles" 
            :key="index"
            class="file-item"
          >
            <div class="file-info">
              <span class="file-icon">📄</span>
              <div class="file-details">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
              </div>
            </div>
            <button 
              @click="removeFile(index)"
              class="remove-button"
              title="Eliminar archivo"
            >
              ✕
            </button>
          </div>
        </div>
        <div class="upload-actions">
          <button 
            @click="uploadFiles"
            :disabled="uploading || uploadedFiles.length === 0"
            class="upload-button"
          >
            <span v-if="!uploading">⬆️ Subir Documentos</span>
            <span v-else class="uploading-text">
              <span class="spinner">⏳</span> Subiendo...
            </span>
          </button>
          <button 
            @click="clearFiles"
            :disabled="uploading"
            class="clear-button"
          >
            Limpiar
          </button>
        </div>
      </div>
    </div>

    <div v-if="uploadStatus" class="upload-status" :class="uploadStatus.type">
      <span class="status-icon">
        {{ uploadStatus.type === 'success' ? '✅' : uploadStatus.type === 'error' ? '❌' : 'ℹ️' }}
      </span>
      <span>{{ uploadStatus.message }}</span>
    </div>

    <div v-if="processedDocuments.length > 0" class="processed-documents">
      <h3>Documentos procesados</h3>
      <div class="documents-list">
        <div 
          v-for="(doc, index) in processedDocuments" 
          :key="index"
          class="document-item"
        >
          <span class="doc-icon">📋</span>
          <div class="doc-info">
            <span class="doc-name">{{ doc.filename || doc.name }}</span>
            <span class="doc-date">Subido: {{ formatDate(doc.processedAt || doc.uploaded_at) }}</span>
            <span v-if="doc.fileId" class="doc-id">ID: {{ doc.fileId || doc.file_id }}</span>
          </div>
          <span class="doc-status success">✓ Listo</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DocumentProcessor',
  data() {
    return {
      uploadedFiles: [],
      isDragging: false,
      uploading: false,
      uploadStatus: null,
      processedDocuments: [],
      apiUrl: import.meta.env.VITE_API_URL || '/api'
    }
  },
  methods: {
    triggerFileInput() {
      this.$refs.fileInput?.click()
    },
    handleFileSelect(event) {
      const files = Array.from(event.target.files)
      this.addFiles(files)
    },
    handleDrop(event) {
      this.isDragging = false
      const files = Array.from(event.dataTransfer.files).filter(file => 
        file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
      )
      this.addFiles(files)
    },
    addFiles(files) {
      // Solo se permiten archivos PDF
      const allowedType = 'application/pdf'
      const allowedExtension = '.pdf'
      
      const validFiles = files.filter(file => {
        const extension = '.' + file.name.split('.').pop().toLowerCase()
        return file.type === allowedType || extension === allowedExtension
      })
      
      if (validFiles.length === 0 && files.length > 0) {
        this.showStatus('error', 'Por favor, selecciona solo archivos PDF')
        return
      }

      if (validFiles.length < files.length) {
        const rejectedCount = files.length - validFiles.length
        this.showStatus('info', `${rejectedCount} archivo(s) rechazado(s). Solo se aceptan archivos PDF`)
      }

      // Evitar duplicados
      validFiles.forEach(file => {
        const exists = this.uploadedFiles.some(f => f.name === file.name && f.size === file.size)
        if (!exists) {
          this.uploadedFiles.push(file)
        }
      })

      if (validFiles.length > 0) {
        this.showStatus('info', `${validFiles.length} archivo(s) agregado(s)`)
      }
    },
    removeFile(index) {
      this.uploadedFiles.splice(index, 1)
      if (this.uploadedFiles.length === 0) {
        this.uploadStatus = null
      }
    },
    clearFiles() {
      this.uploadedFiles = []
      this.uploadStatus = null
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    async uploadFiles() {
      if (this.uploadedFiles.length === 0 || this.uploading) return

      this.uploading = true
      this.uploadStatus = null

      try {
        const formData = new FormData()
        this.uploadedFiles.forEach(file => {
          formData.append('files', file)
        })

        // Usar endpoint /api/upload/multiple para múltiples archivos
        const endpoint = this.uploadedFiles.length === 1 
          ? `${this.apiUrl}/upload` 
          : `${this.apiUrl}/upload/multiple`

        const response = await axios.post(endpoint, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
            // Podrías mostrar el progreso aquí si lo deseas
          }
        })

        // Manejar respuesta según el endpoint usado
        let uploadedDocs = []
        let successCount = 0
        let failedCount = 0

        if (this.uploadedFiles.length === 1) {
          // Respuesta de /api/upload (archivo único)
          const data = response.data
          if (data.success) {
            uploadedDocs.push({
              name: data.filename,
              fileId: data.file_id,
              processedAt: data.uploaded_at || new Date()
            })
            successCount = 1
          } else {
            failedCount = 1
          }
        } else {
          // Respuesta de /api/upload/multiple (array de resultados)
          const results = Array.isArray(response.data) ? response.data : [response.data]
          
          results.forEach(result => {
            if (result.success) {
              uploadedDocs.push({
                name: result.filename,
                fileId: result.file_id,
                processedAt: result.uploaded_at || new Date()
              })
              successCount++
            } else {
              failedCount++
            }
          })
        }

        // Agregar documentos procesados exitosamente a la lista
        if (uploadedDocs.length > 0) {
          this.processedDocuments.push(...uploadedDocs)
        }

        // Mostrar mensaje de resultado
        if (successCount > 0 && failedCount === 0) {
          this.showStatus('success', `¡${successCount} documento(s) subido(s) exitosamente!`)
        } else if (successCount > 0 && failedCount > 0) {
          this.showStatus('info', `${successCount} documento(s) subido(s), ${failedCount} fallido(s)`)
        } else {
          this.showStatus('error', 'No se pudo subir ningún documento. Verifica los archivos e intenta de nuevo.')
        }

        // Limpiar solo si todos fueron exitosos
        if (failedCount === 0) {
          this.clearFiles()
        }
      } catch (error) {
        console.error('Error al subir documentos:', error)
        
        if (error.response?.status === 400) {
          // Error de validación del backend
          this.showStatus('error', error.response?.data?.detail || 'Error de validación. Verifica que los archivos sean del tipo correcto y no excedan 50MB.')
        } else if (error.response?.status === 404) {
          this.showStatus('error', 'El endpoint de carga de documentos aún no está disponible. Asegúrate de que el backend esté ejecutándose.')
        } else if (error.response?.status === 413) {
          this.showStatus('error', 'Archivo demasiado grande. El tamaño máximo permitido es 50MB por archivo.')
        } else {
          this.showStatus('error', error.response?.data?.detail || 'Error al procesar los documentos. Por favor, intenta de nuevo.')
        }
      } finally {
        this.uploading = false
      }
    },
    showStatus(type, message) {
      this.uploadStatus = { type, message }
      if (type === 'success') {
        setTimeout(() => {
          this.uploadStatus = null
        }, 5000)
      }
    },
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    formatDate(date) {
      return new Date(date).toLocaleString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.document-processor {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
  height: 100%;
  overflow-y: auto;
}

.processor-header {
  margin-bottom: 32px;
}

.processor-header h2 {
  margin: 0 0 8px 0;
  font-size: 1.5em;
  color: #2c3e50;
}

.processor-header p {
  margin: 0;
  color: #6c757d;
  font-size: 0.9em;
}

.upload-section {
  margin-bottom: 24px;
}

.upload-area {
  border: 3px dashed #dee2e6;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f8f9fa;
  position: relative;
}

.upload-area:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.upload-area.dragover {
  border-color: #667eea;
  background: #e8f0fe;
  transform: scale(1.02);
}

.upload-area.has-files {
  border-color: #28a745;
  background: #f0fff4;
}

.file-input {
  display: none;
}

.upload-content {
  pointer-events: none;
}

.upload-icon {
  font-size: 64px;
  margin-bottom: 16px;
  display: block;
}

.upload-content h3 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 1.2em;
}

.upload-content p {
  margin: 4px 0;
  color: #6c757d;
  font-size: 0.9em;
}

.upload-hint {
  font-size: 0.85em !important;
  color: #adb5bd !important;
}

.files-list {
  margin-top: 24px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.files-list h3 {
  margin: 0 0 16px 0;
  font-size: 1.1em;
  color: #2c3e50;
}

.file-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.file-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #2c3e50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 0.85em;
  color: #6c757d;
}

.remove-button {
  width: 32px;
  height: 32px;
  border: none;
  background: #dc3545;
  color: white;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  flex-shrink: 0;
}

.remove-button:hover {
  background: #c82333;
  transform: scale(1.1);
}

.upload-actions {
  display: flex;
  gap: 12px;
}

.upload-button,
.clear-button {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-button {
  background: #667eea;
  color: white;
}

.upload-button:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.upload-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.uploading-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.clear-button {
  background: #6c757d;
  color: white;
}

.clear-button:hover:not(:disabled) {
  background: #5a6268;
}

.clear-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-status {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.upload-status.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.upload-status.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.upload-status.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.status-icon {
  font-size: 20px;
}

.processed-documents {
  margin-top: 32px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.processed-documents h3 {
  margin: 0 0 16px 0;
  font-size: 1.1em;
  color: #2c3e50;
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.doc-icon {
  font-size: 24px;
}

.doc-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.doc-name {
  font-weight: 500;
  color: #2c3e50;
}

.doc-date {
  font-size: 0.85em;
  color: #6c757d;
}

.doc-id {
  font-size: 0.75em;
  color: #adb5bd;
  font-family: monospace;
  margin-top: 2px;
}

.doc-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 500;
}

.doc-status.success {
  background: #d4edda;
  color: #155724;
}

@media (max-width: 768px) {
  .document-processor {
    padding: 16px;
  }
  
  .upload-area {
    padding: 32px 16px;
  }
  
  .upload-actions {
    flex-direction: column;
  }
}
</style>

