<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>LegalBot</h2>
    </div>
    <nav class="sidebar-nav">
      <ul class="nav-menu">
        <li>
          <button 
            :class="['nav-item', { active: activeView === 'chat' }]"
            @click="$emit('change-view', 'chat')"
          >
            <span class="nav-icon">💬</span>
            <span class="nav-text">Chat</span>
          </button>
        </li>
        <li>
          <button 
            :class="['nav-item', { active: activeView === 'documents' }]"
            @click="$emit('change-view', 'documents')"
          >
            <span class="nav-icon">📄</span>
            <span class="nav-text">Procesar Documentos</span>
          </button>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script>
export default {
  name: 'Sidebar',
  props: {
    activeView: {
      type: String,
      required: true
    }
  },
  emits: ['change-view']
}
</script>

<style scoped>
.sidebar {
  width: 280px;
  background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  font-size: 1.5em;
  font-weight: 600;
  margin: 0;
  color: white;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
}

.nav-menu {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-menu li {
  margin: 0;
}

.nav-item {
  width: 100%;
  padding: 16px 20px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.8);
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
  font-size: 16px;
  font-family: inherit;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border-left: 4px solid #667eea;
  font-weight: 600;
}

.nav-icon {
  font-size: 20px;
  width: 24px;
  text-align: center;
}

.nav-text {
  flex: 1;
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    height: auto;
    position: relative;
  }
  
  .nav-text {
    display: none;
  }
  
  .nav-item {
    justify-content: center;
    padding: 16px;
  }
}
</style>

