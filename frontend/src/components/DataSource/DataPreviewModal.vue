<template>
  <el-dialog
    v-model="visible"
    :title="previewTitle"
    width="90%"
    :fullscreen="true"
    :before-close="handleClose"
    :destroy-on-close="true"
    class="data-preview-modal"
    :modal-append-to-body="true"
  >
    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="preview-tabs" @tab-click="handleTabClick">
      <el-tab-pane label="字段预览" name="schema" />
      <el-tab-pane label="数据预览" name="data" />
    </el-tabs>
    
    <!-- 字段预览 -->
    <div v-if="activeTab === 'schema'" class="schema-preview">
      <div 
        v-for="field in previewData.schema" 
        :key="field.name"
        class="field-item"
      >
        <el-collapse v-model="activeField" accordion>
          <el-collapse-item :title="field.name + ' (' + field.type + ')'" :name="field.name">
            <div class="field-details">
              <div class="detail-item">
                <span class="label">字段名：</span>
                <span>{{ field.name }}</span>
              </div>
              <div class="detail-item">
                <span class="label">类型：</span>
                <span>{{ field.type }}</span>
              </div>
              <div class="detail-item">
                <span class="label">描述：</span>
                <span>{{ field.description || '无描述' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">单位：</span>
                <span>{{ field.unit || '无' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">类别：</span>
                <span>{{ field.category || '无' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">是否主键：</span>
                <span>{{ field.isPrimaryKey ? '是' : '否' }}</span>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
    
    <!-- 数据预览 -->
    <div v-if="activeTab === 'data'" class="data-preview">
      <el-table
        :data="previewData.data"
        style="width: 100%;"
        :max-height="tableMaxHeight"
        border
        highlight-current-row
        class="data-table"
      >
        <el-table-column
          v-for="column in previewData.schema"
          :key="column.name"
          :prop="column.name"
          :label="column.name"
          :min-width="column.minWidth || 120"
          :width="column.width || null"
          :show-overflow-tooltip="true"
          class-name="table-column"
        >
          <template #default="scope">
            <div class="cell-content">
              <span class="cell-text" :style="{ 'max-width': '300px', 'word-wrap': 'break-word', 'white-space': 'normal' }">
                {{ scope.row[column.name] || '-' }}
              </span>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页信息 -->
      <div class="pagination-info" v-if="previewData.data && previewData.data.length > 0">
        共 {{ previewData.data.length }} 条记录
      </div>
    </div>
    
    <!-- 多表选择提示 -->
    <div v-if="isMultiTable" class="multi-table-tip">
      <el-alert
        title="已选择多个数据表，显示第一个表的预览数据"
        type="info"
        show-icon
        :closable="false"
      />
    </div>
    
    <!-- 无数据提示 -->
    <div v-if="!previewData.data || previewData.data.length === 0" class="no-data">
      <p>暂无数据可预览</p>
    </div>
    
    <!-- 底部按钮 -->
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  previewData: {
    type: Object,
    default: () => ({
      schema: [],
      data: []
    })
  },
  isMultiTable: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue'])

// State
const visible = ref(props.modelValue)
const activeTab = ref('schema')
const activeField = ref('')

// 计算属性：预览标题
const previewTitle = computed(() => {
  if (props.isMultiTable) {
    return '多表预览（显示第一个表）'
  }
  
  if (props.previewData.schema && props.previewData.schema.length > 0) {
    return props.previewData.schema[0].name || '数据预览'
  }
  
  return '数据预览'
})

// 计算属性：表格最大高度
const tableMaxHeight = computed(() => {
  return window.innerHeight - 200 // 200px 是标题、标签页和底部按钮的高度
})

// 监听 props 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
})

// 处理对话框关闭
const handleClose = () => {
  visible.value = false
  emit('update:modelValue', false)
}

// 处理标签页切换
const handleTabClick = (tab) => {
  activeTab.value = tab.name
}

// 监听 visible 变化以同步到父组件
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})
</script>

<style scoped>
.data-preview-modal {
  --el-dialog-padding-primary: 16px;
}

.preview-tabs {
  margin-bottom: 16px;
}

.schema-preview {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 16px 0;
}

.field-item {
  margin-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color);
}

.field-item:last-child {
  border-bottom: none;
}

.field-details {
  padding: 12px;
  background-color: #f8f8f8;
  border-radius: 8px;
  margin-top: 8px;
}

.detail-item {
  display: flex;
  margin-bottom: 8px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.label {
  font-weight: 600;
  color: var(--el-text-color-secondary);
  min-width: 80px;
}

.data-preview {
  height: calc(100vh - 200px);
  overflow: auto;
}

.data-table {
  margin-bottom: 16px;
}

.table-column {
  word-wrap: break-word;
}

.cell-content {
  padding: 8px;
}

.cell-text {
  display: inline-block;
  max-width: 300px;
  word-wrap: break-word;
  white-space: normal;
}

.pagination-info {
  text-align: right;
  color: var(--el-text-color-secondary);
  padding: 8px 16px;
}

.multi-table-tip {
  margin: 16px 0;
}

.no-data {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 40px;
  font-size: 16px;
}
</style>