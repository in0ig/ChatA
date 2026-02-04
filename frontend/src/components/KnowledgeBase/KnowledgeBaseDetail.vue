<template>
  <div class="knowledge-base-detail">
    <div v-if="selectedKnowledgeBase" class="detail-container">
      <!-- 知识库标题 -->
      <div class="detail-header">
        <div class="header-left">
          <h3>{{ selectedKnowledgeBase.name }}</h3>
          <div class="kb-type">类型：{{ typeLabel(selectedKnowledgeBase.type) }}</div>
        </div>
      </div>
      
      <!-- 单行布局：搜索框 + 新增按钮（右对齐） -->
      <div class="actions-row-1">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索知识项..."
          clearable
          class="search-input"
          prefix-icon="Search"
        />
        <el-button type="primary" @click="handleAddKnowledge">新增知识</el-button>
      </div>
      
      <!-- 知识项列表 -->
      <div class="knowledge-list">
        <div v-for="item in filteredKnowledgeItems" :key="item.id" class="knowledge-item">
          <div class="item-content">
            <!-- 名词类型：显示名称 -->
            <div v-if="item.type === 'TERM' && item.name" class="item-field">
              <span class="field-label">名称：</span>
              <span class="field-value">{{ item.name }}</span>
            </div>
            
            <!-- 事件类型：显示时间范围 -->
            <div v-if="item.type === 'EVENT' && (item.event_date_start || item.event_date_end)" class="item-field">
              <span class="field-label">时间：</span>
              <span class="field-value">
                {{ formatDate(item.event_date_start) || '?' }} 至 {{ formatDate(item.event_date_end) || '?' }}
              </span>
            </div>
            
            <!-- 解释（所有类型必填） -->
            <div class="item-field">
              <span class="field-label">解释：</span>
              <span :class="{ 'collapsed': !item.expanded }" class="field-value">
                {{ item.expanded ? item.explanation : (item.explanation && item.explanation.length > 80 ? item.explanation.substring(0, 80) + '...' : item.explanation) }}
              </span>
            </div>
            
            <!-- 提问示例（名词和业务逻辑） -->
            <div v-if="item.type !== 'EVENT' && item.example_question" class="item-field">
              <span class="field-label">示例：</span>
              <span class="field-value">{{ item.example_question }}</span>
            </div>
            
            <!-- 展开/收起按钮 -->
            <span v-if="item.explanation && item.explanation.length > 80" class="toggle-button" @click="toggleItemExpansion(item)">
              {{ item.expanded ? '收起' : '展开' }}
            </span>
          </div>
          <div class="item-actions">
            <el-button 
              type="primary" 
              size="small" 
              @click="handleEditItem(item)"
              class="edit-button"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="handleDeleteItem(item.id)"
              class="delete-button"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
      
      <!-- 删除知识库按钮 -->
      <div class="footer-actions">
        <el-button type="danger" size="small" @click="handleDeleteKnowledgeBase">删除知识库</el-button>
      </div>
    </div>
    
    <div v-else class="empty-state">
      <p>请选择左侧的知识库以查看详细信息</p>
    </div>
    
    <!-- 新增知识项弹窗 -->
    <AddKnowledgeItemModal
      v-model:visible="isAddKnowledgeItemModalVisible"
      :knowledge-base-id="selectedKnowledgeBase?.id || 0"
      :knowledge-base-type="selectedKnowledgeBase?.type || 'TERM'"
      @submit="handleAddKnowledgeItemSuccess"
    />
    
    <!-- 编辑知识项弹窗 -->
    <EditKnowledgeItemModal
      v-model:visible="isEditKnowledgeItemModalVisible"
      :knowledge-item="currentEditItem"
      @submit="handleEditKnowledgeItemSuccess"
    />
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch, onMounted } from 'vue'
import { ElMessageBox, ElMessage, ElForm } from 'element-plus'
import { Edit, Delete, Search } from '@element-plus/icons-vue'
import AddKnowledgeItemModal from './AddKnowledgeItemModal.vue'
import EditKnowledgeItemModal from './EditKnowledgeItemModal.vue'
import { knowledgeBaseApi, knowledgeItemApi } from '@/services/api'

// 定义props接收父组件传递的知识库ID
const props = defineProps({
  knowledgeBaseId: {
    type: String,
    default: null
  }
})

// 定义emits，支持删除事件
const emit = defineEmits(['delete'])

// 搜索关键词
const searchKeyword = ref('')

// 知识库数据 - 从 API 加载
const knowledgeBases = ref([])

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    const response = await knowledgeBaseApi.getKnowledgeBases()
    knowledgeBases.value = response || []
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
  }
}

// 组件挂载时加载知识库列表
onMounted(() => {
  loadKnowledgeBases()
})

// 添加知识项弹窗状态
const isAddKnowledgeItemModalVisible = ref(false)
const isEditKnowledgeItemModalVisible = ref(false)
const currentEditItem = ref(null)

// 知识项数据 - 初始化为空数组，将从API加载
const knowledgeItems = ref([])

// 格式化日期（从 ISO 格式提取日期部分）
const formatDate = (dateStr: string | null) => {
  if (!dateStr) return null
  // 如果是 ISO 格式（如 "2026-01-01T00:00:00"），提取日期部分
  if (dateStr.includes('T')) {
    return dateStr.split('T')[0]
  }
  return dateStr
}

// 加载指定知识库的知识项
const loadKnowledgeItems = async (knowledgeBaseId: string) => {
  if (!knowledgeBaseId) {
    knowledgeItems.value = []
    return
  }
  
  try {
    const response = await knowledgeItemApi.getItemsByKnowledgeBase(knowledgeBaseId)
    // API 拦截器已经返回了 response.data，所以 response 就是数据数组
    knowledgeItems.value = response.map((item: any) => ({
      ...item,
      expanded: false
    }))
  } catch (error) {
    ElMessage.error('加载知识项失败')
    console.error('Failed to load knowledge items:', error)
    knowledgeItems.value = []
  }
}

// 监听knowledgeBaseId变化，自动加载知识项
watch(
  () => props.knowledgeBaseId,
  async (newId) => {
    await loadKnowledgeItems(newId)
  },
  { immediate: true }
)

// 添加展开/收起功能
const toggleItemExpansion = (item: any) => {
  item.expanded = !item.expanded
}

// 计算选中的知识库
const selectedKnowledgeBase = computed(() => {
  if (!props.knowledgeBaseId) return null
  return knowledgeBases.value.find(kb => kb.id === props.knowledgeBaseId) || null
})

// 过滤当前知识库的知识项
const filteredKnowledgeItems = computed(() => {
  if (!selectedKnowledgeBase.value) return []
  
  let items = knowledgeItems.value.filter(item => item.knowledge_base_id === selectedKnowledgeBase.value.id)
  
  // 按搜索关键词过滤
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    items = items.filter(item => item.explanation.toLowerCase().includes(keyword))
  }
  
  return items
})

// 类型标签映射
const typeLabel = (type: string): string => {
  switch (type) {
    case 'TERM': return '名词'
    case 'LOGIC': return '业务逻辑'
    case 'EVENT': return '事件'
    default: return '未知'
  }
}

// 新增知识
const handleAddKnowledge = () => {
  isAddKnowledgeItemModalVisible.value = true
}

// 处理新增知识项成功
const handleAddKnowledgeItemSuccess = async (newItem) => {
  try {
    const response = await knowledgeItemApi.createKnowledgeItem(newItem)
    // API 拦截器已经返回了 response.data，所以直接使用 response
    knowledgeItems.value.push({
      ...response,
      expanded: false
    })
    ElMessage.success('知识项添加成功')
    // 成功后关闭模态框
    isAddKnowledgeItemModalVisible.value = false
  } catch (error) {
    ElMessage.error('添加知识项失败')
    console.error('Failed to create knowledge item:', error)
  }
}

// 编辑知识项
const handleEditItem = (item: any) => {
  currentEditItem.value = item
  isEditKnowledgeItemModalVisible.value = true
}

// 处理编辑知识项成功
const handleEditKnowledgeItemSuccess = async (updatedItem) => {
  try {
    const response = await knowledgeItemApi.updateKnowledgeItem(updatedItem.id.toString(), updatedItem)
    // API 拦截器已经返回了 response.data，所以直接使用 response
    const index = knowledgeItems.value.findIndex(item => item.id === updatedItem.id)
    if (index > -1) {
      knowledgeItems.value[index] = {
        ...response,
        expanded: knowledgeItems.value[index].expanded
      }
      ElMessage.success('知识项更新成功')
      // 成功后关闭模态框
      isEditKnowledgeItemModalVisible.value = false
    }
  } catch (error) {
    ElMessage.error('更新知识项失败')
    console.error('Failed to update knowledge item:', error)
  }
}

// 删除单个知识项
const handleDeleteItem = async (id: number) => {
  ElMessageBox.confirm('确定要删除这个知识项吗？', '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await knowledgeItemApi.deleteKnowledgeItem(id.toString())
      // 从列表中移除
      const index = knowledgeItems.value.findIndex(item => item.id === id)
      if (index > -1) {
        knowledgeItems.value.splice(index, 1)
        ElMessage.success('知识项删除成功')
      }
    } catch (error) {
      ElMessage.error('删除知识项失败')
      console.error('Failed to delete knowledge item:', error)
    }
  }).catch(() => {
    // 取消删除
  })
}

// 删除整个知识库
const handleDeleteKnowledgeBase = async () => {
  if (selectedKnowledgeBase.value) {
    ElMessageBox.confirm(`确定要删除知识库 "${selectedKnowledgeBase.value.name}" 吗？这将删除所有关联的知识项。`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    }).then(async () => {
      try {
        await knowledgeBaseApi.deleteKnowledgeBase(selectedKnowledgeBase.value.id.toString())
        ElMessage.success('知识库删除成功')
        // 触发删除事件给父组件
        emit('delete')
      } catch (error) {
        ElMessage.error('删除知识库失败')
        console.error('Failed to delete knowledge base:', error)
      }
    }).catch(() => {
      // 取消删除
    })
  }
}
</script>

<style scoped>
.knowledge-base-detail {
  height: 100%;
}

.detail-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 500;
}

.kb-type {
  color: #909399;
  font-size: 14px;
}

/* 单行布局：搜索框 + 新增按钮（右对齐） */
.actions-row-1 {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  width: 100%;
  margin-bottom: 20px;
}

.actions-row-1 .search-input {
  width: 400px;
}

.knowledge-list {
  flex: 1;
  overflow-y: auto;
}

.knowledge-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafafa;
  transition: all 0.2s ease;
}

.knowledge-item:hover {
  border-color: #c0c4cc;
  background-color: #f5f7fa;
}

.item-content {
  flex: 1;
  color: #303133;
  font-size: 14px;
  line-height: 1.8;
  margin-right: 16px;
}

.item-field {
  margin-bottom: 6px;
}

.item-field:last-of-type {
  margin-bottom: 0;
}

.field-label {
  font-weight: 600;
  color: #606266;
  margin-right: 8px;
}

.field-value {
  color: #303133;
}

.item-content .collapsed {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.toggle-button {
  color: #409EFF;
  cursor: pointer;
  font-size: 13px;
  margin-left: 8px;
  text-decoration: none;
}

.toggle-button:hover {
  text-decoration: underline;
}

.item-actions {
 
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.footer-actions {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
  text-align: left;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 14px;
}

.empty-state p {
  margin: 0;
}
</style>