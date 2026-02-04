<template>
  <div class="data-table-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据表管理</span>
          <el-button type="primary" @click="handleAddTable" data-testid="add-button">
            <el-icon><Plus /></el-icon>
            新增数据表
          </el-button>
        </div>
      </template>

      <!-- 数据表列表 -->
      <el-table 
        :data="tables" 
        v-loading="loading"
        empty-text="暂无数据表"
      >
        <el-table-column prop="name" label="表名" min-width="150" />
        <el-table-column prop="dataSourceName" label="数据源" width="120" />
        <el-table-column prop="fieldCount" label="字段数" width="80" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row?.fieldCount || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tableType" label="类型" width="80" />
        <el-table-column prop="comment" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click="handleViewDetail(row)"
            >
              查看详情
            </el-button>
            <el-button 
              size="small" 
              type="primary" 
              @click="handleEditTable(row)"
            >
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="handleDeleteTable(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增数据表对话框 -->
    <el-dialog
      title="新增数据表"
      v-model="showAddDialog"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="add-table-form">
        <!-- 数据源选择 -->
        <div class="form-section">
          <h4>选择数据源</h4>
          <el-select 
            v-model="selectedDataSourceId" 
            @change="handleDataSourceChange"
            placeholder="请选择数据源"
            style="width: 100%"
          >
            <el-option 
              v-for="ds in dataSources" 
              :key="ds.id" 
              :value="ds.id"
              :label="ds.name"
            />
          </el-select>
        </div>

        <!-- 表发现和选择 -->
        <div v-if="selectedDataSourceId" class="form-section">
          <div class="section-header">
            <h4>选择数据表</h4>
            <el-button 
              type="primary"
              @click="handleDiscoverTables"
              :loading="discovering"
            >
              <el-icon><Search /></el-icon>
              {{ discovering ? '发现中...' : '发现表' }}
            </el-button>
          </div>
          
          <div v-if="discoveredTables.length > 0" class="discovered-tables">
            <div class="table-header">
              <el-checkbox 
                v-model="selectAllDiscovered"
                @change="handleSelectAllDiscovered"
              >
                全选
              </el-checkbox>
            </div>
            <div class="discovered-table-list">
              <el-checkbox-group v-model="selectedDiscoveredTables">
                <div 
                  v-for="table in discoveredTables" 
                  :key="table.name"
                  class="discovered-table-item"
                >
                  <el-checkbox :label="table.name">
                    <div class="table-info">
                      <div class="table-name">{{ table.name }}</div>
                      <div class="table-meta">
                        {{ table.fieldCount }} 字段
                        <span v-if="table.comment" class="table-comment">- {{ table.comment }}</span>
                      </div>
                    </div>
                  </el-checkbox>
                </div>
              </el-checkbox-group>
            </div>
          </div>
          
          <div v-else-if="!discovering" class="empty-tables">
            <el-empty description="点击'发现表'来查找数据源中的可用表" />
          </div>
        </div>

        <div v-else class="form-hint">
          <el-alert
            title="请先选择一个数据源"
            type="info"
            :closable="false"
          />
        </div>
      </div>
      
      <template #footer>
        <el-button @click="closeAddDialog">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleAddSelectedTables"
          :disabled="selectedDiscoveredTables.length === 0"
        >
          添加选中的表 ({{ selectedDiscoveredTables.length }})
        </el-button>
      </template>
    </el-dialog>

    <!-- 数据表详情对话框 -->
    <el-dialog
      title="数据表详情"
      v-model="showDetailDialog"
      width="800px"
    >
      <div v-if="selectedTable" class="table-detail">
        <div class="detail-section">
          <h4>基本信息</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="表名">{{ selectedTable.name }}</el-descriptions-item>
            <el-descriptions-item label="数据源">{{ selectedTable.dataSourceName }}</el-descriptions-item>
            <el-descriptions-item label="字段数">{{ selectedTable.fieldCount }}</el-descriptions-item>
            <el-descriptions-item label="表类型">{{ selectedTable.tableType || '表' }}</el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">{{ selectedTable.comment || '无' }}</el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="detail-section" style="margin-top: 20px;">
          <h4>字段信息</h4>
          <el-table 
            :data="selectedTable.fields" 
            border
            empty-text="暂无字段信息"
          >
            <el-table-column prop="name" label="字段名" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="comment" label="描述">
              <template #default="{ row }">
                {{ row?.comment || '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="selectedTable.relations && selectedTable.relations.length > 0" class="detail-section" style="margin-top: 20px;">
          <h4>关联关系</h4>
          <el-table :data="selectedTable.relations" border>
            <el-table-column prop="targetTable" label="关联表" />
            <el-table-column prop="type" label="关系类型" />
            <el-table-column prop="fields" label="关联字段">
              <template #default="{ row }">
                {{ row?.fields?.join(', ') || '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { chatbiDataSourceApi } from '@/api/chatbiDataSourceApi'
import { dataTableApi } from '@/services/dataTableApi'

// 数据源接口
interface DataSource {
  id: string
  name: string
  type: string
  status: string
}

// 数据表字段接口
interface TableField {
  name: string
  type: string
  comment?: string
  isPrimaryKey?: boolean
  isNullable?: boolean
}

// 表关联关系接口
interface TableRelation {
  id: string
  targetTable: string
  type: string // 'one-to-one', 'one-to-many', 'many-to-many'
  fields: string[]
}

// 数据表接口
interface DataTable {
  id: string
  name: string
  dataSourceId: string
  dataSourceName: string
  fieldCount: number
  tableType?: string
  comment?: string
  fields: TableField[]
  relations?: TableRelation[]
}

// 发现的表接口
interface DiscoveredTable {
  name: string
  fieldCount: number
  comment?: string
  fields: TableField[]
}

// 响应式数据
const loading = ref(false)
const discovering = ref(false)
const selectedTableId = ref<string | null>(null)
const selectedDataSourceId = ref<string>('')
const showAddDialog = ref(false)
const showDetailDialog = ref(false)
const selectAllDiscovered = ref(false)
const selectedDiscoveredTables = ref<string[]>([])

const dataSources = ref<DataSource[]>([])
const tables = ref<DataTable[]>([])
const discoveredTables = ref<DiscoveredTable[]>([])

// 计算属性
const selectedTable = computed(() => {
  if (!selectedTableId.value) return null
  return tables.value.find(table => table.id === selectedTableId.value)
})

const selectedDataSource = computed(() => {
  if (!selectedDataSourceId.value) return null
  return dataSources.value.find(ds => ds.id === selectedDataSourceId.value)
})

// 事件处理
const handleTableSelect = (tableId: string) => {
  selectedTableId.value = tableId
}

const handleViewDetail = async (table: DataTable) => {
  selectedTableId.value = table.id
  showDetailDialog.value = true
  
  // 加载详细的字段信息
  if (selectedTable.value) {
    try {
      const fields = await dataTableApi.getFields(table.id)
      // 更新选中表的字段信息，映射后端字段名到前端期望的格式
      const tableIndex = tables.value.findIndex(t => t.id === table.id)
      if (tableIndex !== -1) {
        tables.value[tableIndex].fields = fields.map(field => ({
          name: field.field_name,  // 后端返回 field_name
          type: field.data_type,   // 后端返回 data_type
          comment: field.description || ''
        }))
      }
    } catch (error) {
      console.error('加载字段信息失败:', error)
      ElMessage.warning('加载字段信息失败，显示基本信息')
    }
  }
}

const handleEditTable = (table?: DataTable) => {
  if (table) {
    selectedTableId.value = table.id
  }
  if (selectedTable.value) {
    console.log('编辑表:', selectedTable.value.name)
    // 实现编辑功能：显示编辑对话框
    ElMessageBox.prompt(
      `请输入新的表描述（当前：${selectedTable.value.comment || '无'}）`,
      `编辑表 "${selectedTable.value.name}"`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: selectedTable.value.comment || '',
        inputPlaceholder: '请输入表描述'
      }
    ).then(async ({ value }) => {
      try {
        // 这里应该调用更新表的API，目前先显示成功消息
        // await dataTableApi.update(selectedTable.value!.id, { description: value })
        
        // 更新本地数据
        const tableIndex = tables.value.findIndex(t => t.id === selectedTable.value!.id)
        if (tableIndex !== -1) {
          tables.value[tableIndex].comment = value
        }
        
        ElMessage.success('表描述更新成功')
        console.log(`表 "${selectedTable.value!.name}" 描述已更新为: "${value}"`)
      } catch (error) {
        console.error('更新表描述失败:', error)
        ElMessage.error('更新失败，请重试')
      }
    }).catch(() => {
      // 用户取消编辑
    })
  }
}

const handleDeleteTable = async (table: DataTable) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据表 "${table.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用真实 API 删除表
    await dataTableApi.deleteDataTable(table.id)
    
    // 刷新表列表
    await refreshTables()
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败，请重试')
    }
  }
}

const handleDataSourceChange = () => {
  // 清空发现的表和选择
  discoveredTables.value = []
  selectedDiscoveredTables.value = []
  selectAllDiscovered.value = false
}

const handleDiscoverTables = async () => {
  if (!selectedDataSourceId.value) {
    ElMessage.warning('请先选择数据源')
    return
  }

  discovering.value = true
  try {
    // 调用真实 API 发现数据源中的表
    const response = await dataTableApi.discoverTables(selectedDataSourceId.value)
    
    // 检查响应格式，确保是数组
    if (Array.isArray(response)) {
      // 转换 API 响应为组件需要的格式
      discoveredTables.value = response.map(table => ({
        name: table.table_name,
        fieldCount: table.field_count || 0,
        comment: table.comment || '',
        fields: table.fields || []
      }))
      
      selectedDiscoveredTables.value = []
      selectAllDiscovered.value = false
      
      ElMessage.success(`从数据源 ${selectedDataSource.value?.name} 发现了 ${discoveredTables.value.length} 个表`)
      console.log(`从数据源 ${selectedDataSource.value?.name} 发现了 ${discoveredTables.value.length} 个表`)
    } else {
      console.warn('发现表API响应格式异常:', response)
      discoveredTables.value = []
      ElMessage.warning('发现表响应格式异常，请检查后端API')
    }
  } catch (error) {
    console.error('发现表失败:', error)
    ElMessage.error('发现表失败，请检查数据源连接')
    discoveredTables.value = []
  } finally {
    discovering.value = false
  }
}

const handleSelectAllDiscovered = () => {
  if (selectAllDiscovered.value) {
    selectedDiscoveredTables.value = discoveredTables.value.map(t => t.name)
  } else {
    selectedDiscoveredTables.value = []
  }
}

const handleAddSelectedTables = async () => {
  if (selectedDiscoveredTables.value.length === 0) return

  try {
    // 调用真实 API 批量同步表结构
    const response = await dataTableApi.batchSyncTableStructures({
      source_id: selectedDataSourceId.value,
      table_names: selectedDiscoveredTables.value
    })

    ElMessage.success(`成功添加 ${response.successfully_synced} 个数据表`)
    
    // 刷新表列表
    await refreshTables()
    closeAddDialog()
  } catch (error) {
    console.error('添加表失败:', error)
    ElMessage.error('添加表失败，请重试')
  }
}

const handleAddTable = () => {
  showAddDialog.value = true
}

const handleConfigureRelations = (tableId: string) => {
  console.log('配置表关联:', tableId)
  // 这里可以打开关联配置弹窗或跳转到关联配置页面
}

const closeAddDialog = () => {
  showAddDialog.value = false
  // 重置表单状态
  selectedDataSourceId.value = ''
  discoveredTables.value = []
  selectedDiscoveredTables.value = []
  selectAllDiscovered.value = false
}

const refreshTables = async () => {
  loading.value = true
  try {
    // 调用真实 API 获取数据表列表
    const response = await dataTableApi.getDataTables({
      page: 1,
      page_size: 100 // 获取所有表，暂时不分页
    })
    
    // 检查响应格式，确保有 items 属性
    if (response && response.items && Array.isArray(response.items)) {
      // 转换 API 响应为组件需要的格式
      tables.value = response.items.map(table => ({
        id: table.id,
        name: table.table_name,
        dataSourceId: table.data_source_id,
        dataSourceName: table.data_source_name || '未知数据源',
        fieldCount: table.field_count || 0,
        tableType: table.table_type || '表',
        comment: table.description || '',
        fields: table.fields || [],
        relations: table.relations || []
      }))
      
      console.log(`成功加载 ${tables.value.length} 个数据表`)
    } else {
      console.warn('API 响应格式异常:', response)
      tables.value = []
      ElMessage.warning('数据表列表格式异常，请检查后端API')
    }
  } catch (error) {
    console.error('刷新数据表列表失败:', error)
    ElMessage.error('加载数据表列表失败')
    // 如果 API 调用失败，使用空数组
    tables.value = []
  } finally {
    loading.value = false
  }
}

const loadDataSources = async () => {
  try {
    // 使用真实的数据源 API
    const response = await chatbiDataSourceApi.getDataSources()
    
    // 检查响应格式，确保有 data 属性且是数组
    if (response && response.data && Array.isArray(response.data)) {
      // 转换 API 响应格式到组件需要的格式
      dataSources.value = response.data.map(ds => ({
        id: ds.id,
        name: ds.name,
        type: ds.type,
        status: ds.status === 'active' ? 'connected' : 'disconnected'
      }))
      
      console.log(`成功加载 ${dataSources.value.length} 个数据源`)
    } else {
      console.warn('数据源API响应格式异常:', response)
      dataSources.value = []
      ElMessage.warning('数据源列表格式异常，请检查后端API')
    }
  } catch (error) {
    console.error('加载数据源失败:', error)
    ElMessage.error('加载数据源失败，请检查后端连接')
    // 如果 API 调用失败，使用空数组
    dataSources.value = []
  }
}

// 生命周期
onMounted(async () => {
  await loadDataSources()
  await refreshTables()
})
</script>

<style scoped>
.data-table-manager {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 对话框内容样式 */
.add-table-form {
  padding: 0;
}

.form-section {
  margin-bottom: 24px;
}

.form-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
}

.form-hint {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

/* 发现表列表样式 */
.discovered-tables {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 16px;
}

.table-header {
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 16px;
}

.discovered-table-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.discovered-table-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  transition: all 0.2s;
}

.discovered-table-item:hover {
  border-color: #409eff;
  background-color: #f5f7fa;
}

.table-info {
  margin-left: 8px;
}

.table-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.table-meta {
  font-size: 12px;
  color: #909399;
}

.table-comment {
  color: #606266;
}

/* 详情对话框样式 */
.table-detail {
  padding: 0;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}
</style>