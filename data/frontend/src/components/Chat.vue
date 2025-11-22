<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>Chat con LegalBot</h2>
      <p>Haz preguntas sobre tus documentos legales</p>
    </div>
    
    <div class="messages" ref="messagesContainer">
      <div 
        v-for="(message, index) in messages" 
        :key="index" 
        :class="['message', message.type]"
      >
        <div class="message-avatar">
          <span v-if="message.type === 'user'">👤</span>
          <span v-else-if="message.type === 'assistant'">🤖</span>
          <span v-else>⚠️</span>
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessageContent(message.content)"></div>
          <div v-if="message.sources && message.sources.length > 0" class="message-sources">
            <div class="sources-header">📚 Fuentes:</div>
            <div v-for="(source, idx) in message.sources" :key="idx" class="source-item">
              <span class="source-filename">{{ source.filename }}</span>
              <span class="source-score">Relevancia: {{ (source.relevance_score * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <div v-if="message.timestamp" class="message-time">
            {{ formatTime(message.timestamp) }}
          </div>
        </div>
      </div>
      <div v-if="loading" class="message assistant">
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="input-container">
      <textarea
        v-model="currentMessage"
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.shift.enter.exact="currentMessage += '\n'"
        placeholder="Escribe tu pregunta sobre los documentos legales..."
        :disabled="loading"
        rows="1"
        ref="textareaRef"
        class="message-input"
      ></textarea>
      <button 
        @click="sendMessage" 
        :disabled="loading || !currentMessage.trim()"
        class="send-button"
      >
        <span v-if="!loading">📤</span>
        <span v-else class="spinner">⏳</span>
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Chat',
  data() {
    return {
      messages: [],
      currentMessage: '',
      loading: false,
      apiUrl: import.meta.env.VITE_API_URL || '/api',
      selectedFileId: null, // file_id opcional para filtrar por documento
      model: 'mistral:7b-instruct', // Modelo por defecto
      maxChunks: 5,
      temperature: 0.7
    }
  },
  mounted() {
    // Mensaje de bienvenida
    this.messages.push({
      type: 'assistant',
      content: '¡Hola! Soy LegalBot. Puedo ayudarte a entender documentos legales en lenguaje sencillo. ¿En qué puedo ayudarte?',
      timestamp: new Date()
    })
    this.autoResizeTextarea()
  },
  methods: {
    async sendMessage() {
      if (!this.currentMessage.trim() || this.loading) return

      const userMessage = this.currentMessage.trim()
      this.currentMessage = ''
      this.autoResizeTextarea()
      
      // Agregar mensaje del usuario
      const userMsg = {
        type: 'user',
        content: userMessage,
        timestamp: new Date()
      }
      this.messages.push(userMsg)
      this.scrollToBottom()

      this.loading = true

      try {
        // Preparar el body según la API
        const requestBody = {
          question: userMessage,
          model: this.model,
          max_chunks: this.maxChunks,
          temperature: this.temperature
        }
        
        // Agregar file_id solo si está seleccionado
        if (this.selectedFileId) {
          requestBody.file_id = this.selectedFileId
        }

        // Llamada al endpoint de chat
        const response = await axios.post(`${this.apiUrl}/chat`, requestBody, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        // La respuesta viene con answer y sources según la API
        const assistantMessage = {
          type: 'assistant',
          content: response.data.answer || 'Respuesta recibida',
          sources: response.data.sources || [],
          modelUsed: response.data.model_used,
          timestamp: new Date()
        }
        
        this.messages.push(assistantMessage)
      } catch (error) {
        console.error('Error al enviar mensaje:', error)
        
        let errorMessage = 'Error al procesar tu mensaje. Por favor, intenta de nuevo.'
        
        if (error.response) {
          const status = error.response.status
          const detail = error.response.data?.detail || ''
          
          if (status === 404) {
            errorMessage = detail || 'No se encontraron documentos relevantes. Asegúrate de haber subido y procesado documentos.'
          } else if (status === 400) {
            errorMessage = detail || 'Error en la solicitud. Verifica que el documento esté procesado.'
          } else if (status === 503) {
            errorMessage = detail || 'El modelo no está disponible. Verifica que esté instalado en Ollama.'
          } else {
            errorMessage = detail || errorMessage
          }
        } else if (error.code === 'ERR_NETWORK') {
          errorMessage = 'Error de conexión. Verifica que el backend esté ejecutándose.'
        }
        
        this.messages.push({
          type: 'error',
          content: errorMessage,
          timestamp: new Date()
        })
      } finally {
        this.loading = false
        this.scrollToBottom()
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    formatTime(date) {
      return new Date(date).toLocaleTimeString('es-ES', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    },
    autoResizeTextarea() {
      this.$nextTick(() => {
        const textarea = this.$refs.textareaRef
        if (textarea) {
          textarea.style.height = 'auto'
          textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
        }
      })
    },
    formatMessageContent(content) {
      // Convertir saltos de línea a <br> para HTML
      if (!content) return ''
      return content.replace(/\n/g, '<br>')
    }
  },
  watch: {
    currentMessage() {
      this.autoResizeTextarea()
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f9fa;
}

.chat-header {
  padding: 24px;
  background: white;
  border-bottom: 1px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.chat-header h2 {
  margin: 0 0 8px 0;
  font-size: 1.5em;
  color: #2c3e50;
}

.chat-header p {
  margin: 0;
  color: #6c757d;
  font-size: 0.9em;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #f8f9fa;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 75%;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant,
.message.error {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  background: #e9ecef;
}

.message.user .message-avatar {
  background: #667eea;
}

.message.assistant .message-avatar {
  background: #28a745;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-text {
  padding: 12px 16px;
  border-radius: 18px;
  word-wrap: break-word;
  line-height: 1.5;
}

.message-text :deep(br) {
  display: block;
  content: "";
  margin: 4px 0;
}

.message.user .message-text {
  background: #667eea;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: white;
  color: #2c3e50;
  border: 1px solid #e9ecef;
  border-bottom-left-radius: 4px;
}

.message.error .message-text {
  background: #fee;
  color: #c33;
  border: 1px solid #fcc;
  border-bottom-left-radius: 4px;
}

.message-sources {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.message.user .message-sources {
  border-top-color: rgba(255, 255, 255, 0.2);
}

.sources-header {
  font-size: 0.85em;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 8px;
}

.message.user .sources-header {
  color: rgba(255, 255, 255, 0.9);
}

.source-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  margin: 4px 0;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  font-size: 0.8em;
}

.message.user .source-item {
  background: rgba(255, 255, 255, 0.15);
}

.source-filename {
  font-weight: 500;
  color: #495057;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message.user .source-filename {
  color: rgba(255, 255, 255, 0.95);
}

.source-score {
  color: #6c757d;
  margin-left: 12px;
  font-size: 0.9em;
}

.message.user .source-score {
  color: rgba(255, 255, 255, 0.8);
}

.message-time {
  font-size: 0.75em;
  color: #6c757d;
  margin-top: 4px;
  padding: 0 4px;
}

.message.user .message-time {
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6c757d;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.input-container {
  display: flex;
  padding: 20px;
  background: white;
  border-top: 1px solid #e9ecef;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 24px;
  font-size: 16px;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 0.3s;
  max-height: 120px;
  overflow-y: auto;
}

.message-input:focus {
  border-color: #667eea;
}

.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  width: 48px;
  height: 48px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.send-button:hover:not(:disabled) {
  background: #5568d3;
  transform: scale(1.05);
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .message {
    max-width: 85%;
  }
  
  .chat-header {
    padding: 16px;
  }
  
  .chat-header h2 {
    font-size: 1.2em;
  }
}
</style>

