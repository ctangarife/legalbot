<template>
  <div id="app">
    <Sidebar :active-view="currentView" @change-view="changeView" />
    <main class="main-content">
      <Chat v-if="currentView === 'chat'" />
      <DocumentProcessor v-if="currentView === 'documents'" />
    </main>
  </div>
</template>

<script>
import Sidebar from './components/Sidebar.vue'
import Chat from './components/Chat.vue'
import DocumentProcessor from './components/DocumentProcessor.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    Chat,
    DocumentProcessor
  },
  data() {
    return {
      currentView: 'chat'
    }
  },
  methods: {
    changeView(view) {
      this.currentView = view
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #f8f9fa;
  min-height: 100vh;
  overflow-x: hidden;
}

#app {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: 280px;
  min-height: 100vh;
  background: #f8f9fa;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }
}
</style>

