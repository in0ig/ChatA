<template>
  <div class="settings-panel">
    <h3>配置</h3>
    
    <!-- 配置组1：核心配置 -->
    <div class="config-group">
      <h4>核心配置</h4>
      <div class="config-item">
        <label>数据表</label>
        <el-button type="primary" size="small">管理</el-button>
      </div>
      <div class="config-item">
        <label>知识库</label>
        <el-button type="primary" size="small">管理</el-button>
      </div>
      <div class="config-item">
        <label>报告分析思路</label>
        <el-button type="primary" size="small">管理</el-button>
      </div>
      <div class="config-item">
        <label>嵌出管理</label>
        <el-button type="primary" size="small">管理</el-button>
      </div>
    </div>
    
    <!-- 配置组2：权限管理 -->
    <div class="config-group">
      <h4>权限管理</h4>
      <div class="config-item">
        <label>功能权限</label>
        <el-button type="primary" size="small">管理</el-button>
      </div>
      <div class="config-item">
        <label>数据表权限</label>
        <el-button type="primary" size="small">管理</el-button>
      </div>
    </div>
    
    <!-- 配置组3：智能工具 -->
    <div class="config-group">
      <h4>智能工具</h4>
      <div class="config-item">
        <label>数据解读</label>
        <el-switch v-model="dataInterpretation" active-color="#1890ff" inactive-color="#ccc" />
      </div>
      <div class="config-item">
        <label>波动归因</label>
        <el-switch v-model="fluctuationAnalysis" active-color="#1890ff" inactive-color="#ccc" />
      </div>
      <div class="config-item">
        <label>智能选表</label>
        <el-switch v-model="smartTableSelection" active-color="#1890ff" inactive-color="#ccc" />
      </div>
    </div>
    
    <!-- 配置组4：高级设置 -->
    <div class="config-group">
      <h4>高级设置</h4>
      <div class="config-item">
        <label>高级设置</label>
        <el-button type="primary" size="small">设置</el-button>
      </div>
      <div class="config-item">
        <label>对话ID设置</label>
        <el-button type="primary" size="small">设置</el-button>
      </div>
      <div class="config-item">
        <label>格式管理</label>
        <el-button type="primary" size="small">管理</el-button>
      </div>
    </div>
    
    <!-- 退出按钮 -->
    <div class="logout-section">
      <button @click="handleLogout" class="btn-secondary">退出登录</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 状态
const dataInterpretation = ref(true)
const fluctuationAnalysis = ref(false)
const smartTableSelection = ref(true)

// 退出登录
const handleLogout = () => {
  console.log('用户退出登录')
}
</script>

<style scoped>
.settings-panel {
  width: 280px;
  height: 100%;
  padding: 16px;
  background-color: white;
  box-shadow: -2px 0 8px rgba(0,0,0,0.1);
  overflow-y: auto;
}

.settings-panel h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.config-group {
  margin-bottom: 24px;
}

.config-group h4 {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.config-item label {
  font-size: 14px;
  color: #333;
}

.btn-secondary {
  background-color: #fff;
  color: #333;
  border: 1px solid #ddd;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-secondary:hover {
  background-color: #f0f0f0;
}

.logout-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}
</style>