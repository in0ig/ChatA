<template>
  <div class="data-table-detail">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state" data-testid="loading-state">
      <el-skeleton :rows="6" animated />
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state" data-testid="error-state">
      <el-alert
        :title="error"
        type="error"
        :closable="false"
        show-icon
      />
    </div>
    
    <!-- 正常状态 -->
    <div v-else class="detail-content">
      <!-- 表基本信息 -->
      <div class="table-info-section">
        <div class="section-header">
          <h3 class="section-title">基本信息</h3>
          <div class="section-actions">
            <el-button
              type="primary"
              size="small"
              @click="syncTableStructure"
              :loading="syncing"
              data-testid="sync-button"
            >
              <el-icon><Refresh /></el-icon>
              同步表结构
            </el-button>
          </div>
        </div>
        
        <div class="info-grid">
          <div class="info-item" data-testid="table-info-item">
            <span class="info-label">表名：</span>
            <span class="info-value" data-testid="table-name-value">{{ tableName }}</span>
          </div>
          <div class="info-item" data-testid="table-info-item">
            <span class="info-label">数据源：</span>
            <span class="info-value" data-testid="source-name-value">{{ dataSourceName }}</span>
          </div>
          <div class="info-item" data-testid="table-info-item">
            <span class="info-label">状态：</span>
            <el-tag 
              :type="statusType"
              data-testid="status-tag"
            >
              {{ statusText }}
            </el-tag>
          </div>
          <div class="info-item" data-testid="table-info-item">
            <span class="info-label">记录数：</span>
            <span class="info-value" data-testid="row-count-value">{{ formatNumber(rowCount) }}</span>
          </div>
          <div class="info-item" data-testid="table-info-item">
            <span class="info-label">字段数：</span>
            <span class="info-value" data-testid="field-count-value">{{ fieldCount }}</span>
          </div>
          <div class="info-item" data-testid="table-info-item">
            <span class="info-label">创建时间：</span>
            <span class="info-value" data-testid="created-at-value">{{ formatDate(createdAt) }}</span>
          </div>
          <div class="info-item full-width" data-testid="table-info-item">
            <span class="info-label">描述：</span>
            <span class="info-value" data-testid="description-value">{{ description || '无' }}</span>
          </div>
        </div>
      </div>
      
      <!-- 字段列表 -->
      <div class="fields-section">
        <div class="section-header">
          <h3 class="section-title">字段列表</h3>
          <div class="section-actions">
            <el-button
              type="primary"
              size="small"
              @click="addField"
              :disabled="!tableInfo"
              data-testid="add-field-button"
            >
              <el-icon><Plus /></el-icon>
              添加字段
            </el-button>
          </div>
        </div>
        
        <el-table
          :data="fields"
          stripe
          border
          style="width: 100%"
          data-testid="fields-table"
        >
          <el-table-column prop="name" label="字段名" width="150" data-testid="field-header-name" />
          <el-table-column prop="displayName" label="显示名称" width="150" data-testid="field-header-display-name" />
          <el-table-column prop="type" label="数据类型" width="120" data-testid="field-header-type" />
          <el-table-column prop="isPrimaryKey" label="主键" width="80" align="center" data-testid="field-header-primary-key" />
          <el-table-column prop="isNullable" label="可为空" width="80" align="center" data-testid="field-header-nullable" />
          <el-table-column prop="description" label="描述" min-width="150" data-testid="field-header-description" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Plus } from '@element-plus/icons-vue'
import { useDataPreparationStore } from '@/store/modules/dataPreparation'
import { dataTableApi } from '@/api/dataTableApi'

// 定义类型
interface DataTableInfo {
  id: number
  tableName: string
  sourceId: number
  isActive: boolean
  rowCount: number
  description: string | null
  createdAt: string
  updatedAt: string
  fields: TableField[]
}

interface TableField {
  id: number
  name: string
  displayName: string
  type: string
  isPrimaryKey: boolean
  isNullable: boolean
  dictionaryCode: string | null
  description: string | null
}

// Store
const dataPrepStore = useDataPreparationStore()

// Props
const props = defineProps({
  tableId: {
    type: String,
    required: true
  }
})

// 状态
const loading = ref(true)
const error = ref<string | null>(null)
const syncing = ref(false)
const tableInfo = ref<DataTableInfo | null>(null)
const editingFieldId = ref<number | null>(null)

// 字段类型选项
const fieldTypes = ref<string[]>([
  'VARCHAR', 'TEXT', 'INT', 'BIGINT', 'DECIMAL', 'DATE', 'DATETIME', 
  'TIMESTAMP', 'BOOLEAN', 'JSON', 'CHAR', 'FLOAT', 'DOUBLE', 'BLOB'
])

// 计算属性
const tableName = computed(() => {
  return tableInfo.value ? tableInfo.value.tableName : ''
})

const dataSourceName = computed(() => {
  const source = dataPrepStore.dataSources.data.find(ds => ds.id === tableInfo.value?.sourceId)
  return source ? source.name : '未知数据源'
})

const statusType = computed(() => {
  return (tableInfo.value && tableInfo.value.isActive) ? 'success' : 'warning'
})

const statusText = computed(() => {
  return (tableInfo.value && tableInfo.value.isActive) ? '激活' : '未激活'
})

const rowCount = computed(() => {
  return (tableInfo.value && tableInfo.value.rowCount) || 0
})

const fieldCount = computed(() => {
  return (tableInfo.value && tableInfo.value.fields && tableInfo.value.fields.length) || 0
})

const createdAt = computed(() => {
  return tableInfo.value ? tableInfo.value.createdAt : undefined
})

const description = computed(() => {
  return tableInfo.value && tableInfo.value.description
})

const fields = computed(() => {
  return (tableInfo.value && tableInfo.value.fields) || []
})

// 加载数据表详情
const loadDataTableDetail = async () => {
  loading.value = true
  error.value = null
  try {
    if (!props.tableId) {
      throw new Error('缺少数据表ID')
    }
    
    const data = await dataTableApi.getById(Number(props.tableId))
    
    // Map API response structure to component expected structure
    const mappedFields = data.columns?.map(col => ({
      id: col.id,
      name: col.name,
      displayName: col.name,
      type: col.type,
      isPrimaryKey: col.is_primary_key,
      isNullable: col.is_nullable,
      dictionaryCode: col.dictionary_code || null,
      description: col.description || null
    })) || []
    
    tableInfo.value = {
      id: data.id,
      tableName: data.table_name,
      sourceId: data.source_id,
      isActive: data.is_active || false,
      rowCount: data.row_count || 0,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
      description: data.description || '',
      fields: mappedFields
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载数据表详情失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 格式化数字
const formatNumber = (num: number): string => {
  return num.toLocaleString('zh-CN')
}

// 同步表结构
const syncTableStructure = async () => {
  if (!tableInfo.value) return
  
  syncing.value = true
  try {
    const result = await dataTableApi.syncStructure({
      source_id: tableInfo.value.sourceId,
      table_name: tableInfo.value.tableName
    })
    
    // 重新加载表信息
    await loadDataTableDetail()
    
    ElMessage.success('表结构同步成功')
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : '同步表结构失败'
    ElMessage.error(errorMessage)
  } finally {
    syncing.value = false
  }
}

// 添加新字段
const addField = async () => {
  if (!tableInfo.value) return
  
  try {
    const newField = await dataTableApi.addField(tableInfo.value.id, {
      name: '新字段',
      type: 'VARCHAR',
      isNullable: true,
      displayName: '新字段'
    })
    
    if (tableInfo.value.fields) {
      tableInfo.value.fields.push(newField)
    }
    
    ElMessage.success('字段添加成功')
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : '添加字段失败'
    ElMessage.error(errorMessage)
  }
}

// 初始化
onMounted(() => {
  loadDataTableDetail()
})
</script>

<style scoped>
.data-table-detail {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}

.loading-state,
.error-state {
  padding: 20px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.table-info-section,
.fields-section {
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #fafafa;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
}

.info-value {
  color: #303133;
  flex: 1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .data-table-detail {
    padding: 12px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 16px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .section-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>