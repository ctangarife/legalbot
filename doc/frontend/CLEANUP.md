# Limpieza de Bases de Datos - Guía para el Frontend

## ⚠️ Importante

**Las operaciones de limpieza NO están disponibles como endpoints públicos** por razones de seguridad. Solo se pueden ejecutar desde dentro del contenedor Docker del backend.

## ¿Por qué no hay endpoints de limpieza?

Por seguridad, las operaciones de limpieza son destructivas y no deben estar expuestas públicamente. Solo los administradores con acceso al servidor pueden ejecutarlas.

## Cómo Limpiar las Bases de Datos

### Opción 1: Desde la Terminal (Recomendado)

Los administradores pueden usar el script `cleanup.py` directamente desde la terminal:

```bash
# Ver ayuda
docker exec -it legalbot-backend-1 python cleanup.py --help

# Eliminar un documento específico
docker exec -it legalbot-backend-1 python cleanup.py --document <file_id>

# Eliminar todos los documentos (requiere confirmación)
docker exec -it legalbot-backend-1 python cleanup.py --all --confirm

# Limpiar solo MongoDB
docker exec -it legalbot-backend-1 python cleanup.py --mongodb-only --confirm

# Limpiar solo Qdrant
docker exec -it legalbot-backend-1 python cleanup.py --qdrant-only --confirm
```

### Opción 2: Panel Administrativo (Si se Implementa)

Si necesitas implementar una funcionalidad de limpieza en el UI, puedes crear un panel administrativo que:

1. **Requiera autenticación fuerte** (JWT con rol de administrador)
2. **Ejecute comandos Docker** a través de un servicio backend protegido
3. **Muestre confirmaciones claras** antes de operaciones destructivas

**Ejemplo de implementación:**

```javascript
// Componente AdminPanel.vue
<template>
  <div class="admin-panel">
    <h2>Panel de Administración</h2>
    
    <section class="cleanup-section">
      <h3>Limpieza de Bases de Datos</h3>
      
      <!-- Eliminar documento específico -->
      <div class="action-group">
        <input 
          v-model="fileIdToDelete" 
          placeholder="File ID del documento"
          type="text"
        />
        <button 
          @click="deleteDocument"
          :disabled="!fileIdToDelete"
        >
          Eliminar Documento
        </button>
      </div>
      
      <!-- Limpiar todo -->
      <div class="action-group">
        <button 
          @click="confirmCleanupAll"
          class="danger"
        >
          Limpiar Todo
        </button>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  data() {
    return {
      fileIdToDelete: '',
      showConfirmDialog: false
    }
  },
  methods: {
    async deleteDocument() {
      if (!this.fileIdToDelete) return;
      
      try {
        // Esto llamaría a un endpoint protegido que ejecuta el script
        const response = await fetch('/api/admin/cleanup/document', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.adminToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            file_id: this.fileIdToDelete
          })
        });
        
        if (response.ok) {
          alert('Documento eliminado exitosamente');
          this.fileIdToDelete = '';
        } else {
          const error = await response.json();
          alert(`Error: ${error.detail}`);
        }
      } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar documento');
      }
    },
    
    async confirmCleanupAll() {
      const confirmed = confirm(
        '⚠️ ADVERTENCIA: Esto eliminará TODOS los documentos.\n\n' +
        'Esta operación es IRREVERSIBLE.\n\n' +
        '¿Estás seguro?'
      );
      
      if (!confirmed) return;
      
      try {
        const response = await fetch('/api/admin/cleanup/all', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.adminToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            confirm: true
          })
        });
        
        if (response.ok) {
          const result = await response.json();
          alert(`Limpieza completada:\n${JSON.stringify(result, null, 2)}`);
        } else {
          const error = await response.json();
          alert(`Error: ${error.detail}`);
        }
      } catch (error) {
        console.error('Error:', error);
        alert('Error al limpiar bases de datos');
      }
    }
  }
}
</script>
```

### Opción 3: No Implementar en el Frontend (Más Seguro)

La opción más segura es **NO exponer la limpieza en el frontend**. Los administradores pueden usar el script directamente desde la terminal cuando sea necesario.

## Recomendaciones

1. **Para desarrollo/testing:** Usa el script directamente desde la terminal
2. **Para producción:** 
   - Si necesitas UI: Crea un panel administrativo con autenticación fuerte
   - Si no necesitas UI: Usa el script directamente desde el servidor
3. **Nunca:** Expongas endpoints de limpieza sin autenticación

## Documentación Técnica

Para más detalles sobre el script de limpieza, consulta:
- `doc/back/CLEANUP.MD` - Documentación técnica completa del script

