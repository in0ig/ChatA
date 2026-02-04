<template>
  <div class="navigation-sidebar">
    <div class="sidebar-header">
      <div class="logo">ChatBI</div>
      <button class="toggle-btn" @click="toggleSidebar" title="折叠/展开侧边栏">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
          <path d="M4.646 1.646a.5.5 0 0 1 .708 0L8 4.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 5l2.647 2.646a.5.5 0 0 1-.708.708L8 5.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 5 4.646 2.354a.5.5 0 0 1 0-.708z"/>
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <!-- 一级菜单 -->
      <div class="nav-section">
        <div class="nav-item" :class="{ active: currentSection === 'dashboard' }" @click="navigateTo('dashboard')">
          <span class="nav-icon">📊</span>
          <span class="nav-text">数据看板</span>
        </div>
        <div class="nav-item" :class="{ active: currentSection === 'analysis' }" @click="navigateTo('analysis')">
          <span class="nav-icon">🔍</span>
          <span class="nav-text">数据分析</span>
        </div>
        <div class="nav-item" :class="{ active: currentSection === 'applications' }" @click="navigateTo('applications')">
          <span class="nav-icon">🚀</span>
          <span class="nav-text">项目应用</span>
        </div>
        <div class="nav-item" :class="{ active: currentSection === 'data-prep' }" @click="navigateTo('data-prep')">
          <span class="nav-icon">🗂️</span>
          <span class="nav-text">数据准备</span>
        </div>
      </div>

      <!-- 数据准备二级菜单 -->
      <div class="nav-section" v-if="currentSection === 'data-prep'">
        <div class="nav-sub-item" :class="{ active: currentSubSection === 'tables' }" @click="navigateTo('data-prep/tables')">
          <span class="nav-icon">📋</span>
          <span class="nav-text">数据表</span>
        </div>
        <div class="nav-sub-item" :class="{ active: currentSubSection === 'sources' }" @click="navigateTo('chatbi/datasources')">
          <span class="nav-icon">📁</span>
          <span class="nav-text">数据源</span>
        </div>
        <div class="nav-sub-item" :class="{ active: currentSubSection === 'dictionaries' }" @click="navigateTo('data-prep/dictionaries')">
          <span class="nav-icon">📚</span>
          <span class="nav-text">字典表</span>
        </div>
        <div class="nav-sub-item" :class="{ active: currentSubSection === 'relations' }" @click="navigateTo('data-prep/relations')">
          <span class="nav-icon">🔗</span>
          <span class="nav-text">表关联</span>
        </div>
      </div>

      <!-- 其他二级菜单 -->
      <div class="nav-section" v-if="currentSection === 'analysis'">
        <div class="nav-sub-item" :class="{ active: currentSubSection === 'query' }" @click="navigateTo('analysis/query')">
          <span class="nav-icon">💬</span>
          <span class="nav-text">智能问数</span>
        </div>
        <div class="nav-sub-item" :class="{ active: currentSubSection === 'report' }" @click="navigateTo('analysis/report')">
          <span class="nav-icon">📈</span>
          <span class="nav-text">生成报告</span>
        </div>
      </div>
    </nav>

    <div class="sidebar-footer">
      <div class="version">v1.0.0</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const currentSection = computed(() => {
  const path = route.path
  if (path === '/') return 'dashboard'
  if (path.startsWith('/analysis')) return 'analysis'
  if (path.startsWith('/applications')) return 'applications'
  if (path.startsWith('/data-prep') || path.startsWith('/chatbi/datasources')) return 'data-prep'
  return 'dashboard'
})

const currentSubSection = computed(() => {
  const path = route.path
  if (path === '/data-prep/tables') return 'tables'
  if (path === '/data-prep/sources' || path === '/chatbi/datasources') return 'sources'
  if (path === '/data-prep/dictionaries') return 'dictionaries'
  if (path === '/data-prep/relations') return 'relations'
  if (path === '/analysis/query') return 'query'
  if (path === '/analysis/report') return 'report'
  return ''
})

const toggleSidebar = () => {
  // 这里可以添加侧边栏折叠/展开的逻辑
  // 例如：通过 Pinia 状态管理来控制
}

const navigateTo = (path) => {
  if (path === 'dashboard') {
    router.push('/')
  } else if (path === 'data-prep') {
    router.push('/data-prep')
  } else if (path.startsWith('/')) {
    router.push(path)
  } else {
    router.push(`/${path}`)
  }
}
</script>

<style scoped>
.navigation-sidebar {
  width: 220px;
  height: 100vh;
  background-color: #1f1f1f;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  overflow-y: auto;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #333;
}

.logo {
  font-size: 18px;
  font-weight: 700;
  color: #1890ff;
}

.toggle-btn {
  background: none;
  border: none;
  color: #aaa;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.toggle-btn:hover {
  background-color: #333;
  color: #fff;
}

.sidebar-nav {
  flex: 1;
  padding: 10px 0;
}

.nav-section {
  padding: 0 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  margin: 4px 0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.nav-item:hover {
  background-color: #333;
}

.nav-item.active {
  background-color: #1890ff;
  color: white;
}

.nav-icon {
  margin-right: 10px;
  font-size: 16px;
}

.nav-text {
  flex: 1;
}

.nav-sub-item {
  display: flex;
  align-items: center;
  padding: 10px 25px;
  margin: 2px 0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  color: #ccc;
}

.nav-sub-item:hover {
  background-color: #333;
  color: #fff;
}

.nav-sub-item.active {
  background-color: #1890ff;
  color: white;
}

.sidebar-footer {
  padding: 15px;
  text-align: center;
  border-top: 1px solid #333;
  color: #666;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navigation-sidebar {
    width: 60px;
  }
  
  .logo {
    font-size: 16px;
  }
  
  .nav-text {
    display: none;
  }
  
  .nav-item {
    justify-content: center;
    padding: 12px 8px;
  }
  
  .nav-sub-item {
    justify-content: center;
    padding: 10px 8px;
    font-size: 12px;
  }
}
</style>