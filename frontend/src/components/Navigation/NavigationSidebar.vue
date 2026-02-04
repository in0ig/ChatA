<template>
  <div class="navigation-sidebar">
    <!-- Logo 区域 -->
    <div class="logo-section">
      <div class="logo-content">
        <span class="logo-icon"></span>
        <span class="logo-text">ChatBI</span>
      </div>
      <div class="logo-separator"></div>
    </div>
    
    <nav class="nav-menu">
      <ul>
        <!-- 数据分析组 - 只保留ChatBI -->
        <li class="menu-item group-header" @click="toggleGroup('analysis')">
          <div class="menu-link group-link">
            <span class="menu-icon"></span>
            <span class="menu-text">数据分析</span>
            <span class="toggle-icon" :class="{ 'expanded': expandedGroups.analysis }">▼</span>
          </div>
        </li>
        <li v-for="item in analysisItems" :key="item.path" class="menu-item" v-show="expandedGroups.analysis">
          <router-link 
            :to="item.path" 
            :class="{ 'active': isActive(item.path) }"
            class="menu-link"
          >
            <span class="menu-icon"></span>
            <span class="menu-text">{{ item.label }}</span>
          </router-link>
        </li>
        
        <!-- 数据准备组 -->
        <li class="menu-item group-header" @click="toggleGroup('dataPrep')">
          <div class="menu-link group-link">
            <span class="menu-icon"></span>
            <span class="menu-text">数据准备</span>
            <span class="toggle-icon" :class="{ 'expanded': expandedGroups.dataPrep }">▼</span>
          </div>
        </li>
        <li v-for="item in dataPrepItems" :key="item.path" class="menu-item" v-show="expandedGroups.dataPrep">
          <router-link 
            :to="item.path" 
            :class="{ 'active': isActive(item.path) }"
            class="menu-link"
          >
            <span class="menu-icon"></span>
            <span class="menu-text">{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router';
import { ref } from 'vue';

const router = useRouter();
const route = useRoute();

// 分析数据项 - 只保留ChatBI
const analysisItems = ref([
  { label: 'ChatBI', path: '/' }
]);

// 数据准备项
const dataPrepItems = ref([
  { label: '数据表', path: '/data-prep/tables' },
  { label: '数据源', path: '/chatbi/datasources' },
  { label: '字典表', path: '/data-prep/dictionaries' },
  { label: '表关联', path: '/data-prep/relations' }
]);

// 折叠/展开状态管理
const expandedGroups = ref({
  analysis: true,
  dataPrep: true
});

// 切换分组展开/折叠状态
function toggleGroup(groupName) {
  expandedGroups.value[groupName] = !expandedGroups.value[groupName];
}

// 检查当前路由是否匹配
function isActive(path) {
  return route.path === path;
}
</script>

<style scoped>
.navigation-sidebar {
  width: 200px;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  background-color: #1a1a2e;
  border-right: none;
  overflow-y: auto;
  color: #e0e0e0;
}

/* Logo 区域 */
.logo-section {
  height: 56px;
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.logo-content {
  display: flex;
  align-items: center;
}

.logo-icon {
  font-size: 20px;
  margin-right: 8px;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

.logo-separator {
  height: 1px;
  background-color: rgba(255, 255, 255, 0.1);
  margin-top: 8px;
}

.nav-menu ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.menu-item {
  margin-bottom: 2px;
}

.menu-link {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  text-decoration: none;
  color: #e0e0e0;
  font-weight: 500;
  border-radius: 4px;
  transition: all 0.2s ease;
  width: 100%;
  box-sizing: border-box;
}

.menu-link:hover {
  background-color: rgba(24, 144, 255, 0.1);
}

.menu-link.active {
  background-color: rgba(24, 144, 255, 0.2);
  border-left: 3px solid #1890ff;
  font-weight: 600;
  color: #ffffff;
}

.menu-icon {
  margin-right: 0;
  font-size: 18px;
  width: 18px;
}

.menu-text {
  flex: 1;
  font-size: 14px;
}

/* 分组标题样式 */
.group-header {
  margin-top: 16px;
  margin-bottom: 8px;
}

.group-header .menu-link {
  font-weight: 500;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #8c8c8c;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: 6px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.group-header .menu-link .toggle-icon {
  font-size: 10px;
  margin-left: 8px;
  transition: transform 0.2s ease;
}

.group-header .menu-link .toggle-icon.expanded {
  transform: rotate(180deg);
}

/* 子菜单项样式 - 缩进 16px */
.menu-item .menu-link {
  padding-left: 16px;
  padding-right: 16px;
}

/* 底部链接样式 */
.back-link {
  padding: 14px 16px;
  background-color: rgba(26, 26, 46, 0.3);
  border-radius: 6px;
}
</style>