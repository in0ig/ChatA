# Home.vue 数据源/数据表选择修复方案

## 问题描述
当前 Home.vue 中的数据源选择逻辑有误：
- 数据源选择器使用了多选模式
- 预览按钮直接打开数据源选择对话框
- 缺少数据表选择功能

## 需求
1. 第一行：数据源下拉框（单选）+ 模式切换开关
2. 第二行：数据表下拉框（多选，支持复选框）+ 预览按钮
3. 预览按钮用于预览选中的数据表数据

## 修改内容

### 1. 模板部分修改

#### 原代码（第一行）：
```vue
<div class="input-row" style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
  <div class="data-source-selector" style="display: flex; align-items: center;">
    <label class="label">数据源：</label>
    <el-select 
      v-model="currentDataSource" 
      placeholder="请选择数据源" 
      class="source-select"
      multiple
      collapse-tags
      @change="handleDataSourceChange"
    >
      <el-option 
        v-for="item in dataSources" 
        :key="item.id" 
        :label="item.name" 
        :value="item.id" 
      />
    </el-select>
  </div>
  
  <el-button 
    type="primary" 
    size="small" 
    class="preview-btn"
    @click="openDataSourceSelector"
  >
    预览
  </el-button>
  
  <div class="mode-toggle" style="display: flex; align-items: center; margin-left: auto;">
    <label class="label" style="margin-right: 8px;">智能问数</label>
    <el-switch
      v-model="chatMode"
      active-text=""
      inactive-text=""
      :active-color="'#1890ff'"
      :inactive-color="'#ccc'"
      size="small"
    />
    <label class="label" style="margin-left: 8px;">生成报告</label>
  </div>
</div>
```

#### 修改后（两行）：
```vue
<!-- 第一行：数据源选择器、模式切换开关 -->
<div class="input-row" style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
  <div class="data-source-selector" style="display: flex; align-items: center;">
    <label class="label">数据源：</label>
    <el-select 
      v-model="currentDataSource" 
      placeholder="请选择数据源" 
      class="source-select"
      @change="handleDataSourceChange"
    >
      <el-option 
        v-for="item in dataSources" 
        :key="item.id" 
        :label="item.name" 
        :value="item.id" 
      />
    </el-select>
  </div>
  
  <div class="mode-toggle" style="display: flex; align-items: center; margin-left: auto;">
    <label class="label" style="margin-right: 8px;">智能问数</label>
    <el-switch
      v-model="chatMode"
      active-text=""
      inactive-text=""
      :active-color="'#1890ff'"
      :inactive-color="'#ccc'"
      size="small"
    />
    <label class="label" style="margin-left: 8px;">生成报告</label>
  </div>
</div>

<!-- 第二行：数据表选择器、预览按钮 -->
<div class="input-row" style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
  <div class="data-table-selector" style="display: flex; align-items: center; flex: 1;">
    <label class="label">数据表：</label>
    <el-select 
      v-model="currentDataTables" 
      placeholder="请选择数据表" 
      class="table-select"
      multiple
      collapse-tags
      collapse-tags-tooltip
      :disabled="!currentDataSource"
      @change="handleDataTableChange"
    >
      <el-option 
        v-for="item in availableDataTables" 
        :key="item.id" 
        :label="item.name" 
        :value="item.id" 
      />
    </el-select>
  </div>
  
  <el-button 
    type="primary" 
    size="small" 
    class="preview-btn"
    :disabled="currentDataTables.length === 0"
    @click="openDataTablePreview"
  >
    预览
  </el-button>
</div>
```

### 2. Script 部分修改

#### 状态变量：
```typescript
// 原代码
const currentDataSource = ref([])

// 修改后
const currentDataSource = ref('')
const currentDataTables = ref<string[]>([])
```

#### 计算属性：
```typescript
// 新增：根据选中的数据源获取可用的数据表
const availableDataTables = computed(() => {
  if (!currentDataSource.value) {
    return []
  }
  // 从 dataPrepStore 获取当前数据源下的数据表
  return dataPrepStore.getDataTablesBySourceId(currentDataSource.value) || []
})

// 修改：输入框占位符
const inputPlaceholder = computed(() => {
  if (!currentDataSource.value) {
    return '请先选择数据源...'
  }
  if (currentDataTables.value.length === 0) {
    return '请先选择数据表...'
  }
  return chatStore.chatMode === 'query' 
    ? '输入您的问题，让 AI 分析数据...' 
    : '输入您想要生成的报告内容...'
})

// 修改：是否可以发送消息
const canSend = computed(() => {
  return inputText.value.trim().length > 0 && 
         currentDataSource.value && 
         currentDataTables.value.length > 0
})
```

#### 事件处理函数：
```typescript
// 数据源变更
const handleDataSourceChange = (value) => {
  currentDataSource.value = value
  // 清空数据表选择
  currentDataTables.value = []
  chatStore.setDataSource(value)
}

// 数据表变更
const handleDataTableChange = (values) => {
  currentDataTables.value = values
  chatStore.setDataTables(values)
}

// 打开数据表预览
const openDataTablePreview = () => {
  // 获取选中的数据表信息
  const selectedTables = availableDataTables.value.filter(table => 
    currentDataTables.value.includes(table.id)
  )
  
  if (selectedTables.length === 0) {
    ElMessage.warning('请先选择数据表')
    return
  }
  
  // 如果只选择了一张表，直接预览
  if (selectedTables.length === 1) {
    handleDataTablePreview(selectedTables[0])
  } else {
    // 多张表，显示选择对话框
    isMultiTable.value = true
    dataPreviewModalVisible.value = true
  }
}

// 处理数据表预览（新增）
const handleDataTablePreview = (table) => {
  // 调用后端 API 获取表结构和数据
  previewData.value = {
    schema: [
      { name: 'id', type: 'int', description: '主键ID', unit: '', category: '标识', isPrimaryKey: true },
      { name: 'name', type: 'varchar', description: '姓名', unit: '', category: '标识', isPrimaryKey: false },
      { name: 'age', type: 'int', description: '年龄', unit: '岁', category: '人口', isPrimaryKey: false },
      { name: 'email', type: 'varchar', description: '邮箱地址', unit: '', category: '联系方式', isPrimaryKey: false },
      { name: 'created_at', type: 'datetime', description: '创建时间', unit: '', category: '时间', isPrimaryKey: false }
    ],
    data: [
      { id: 1, name: '张三', age: 25, email: 'zhangsan@example.com', created_at: '2023-01-15 10:30:00' },
      { id: 2, name: '李四', age: 30, email: 'lisi@example.com', created_at: '2023-02-20 14:45:00' },
      { id: 3, name: '王五', age: 28, email: 'wangwu@example.com', created_at: '2023-03-10 09:15:00' }
    ]
  }
  dataPreviewModalVisible.value = true
}
```

### 3. Store 修改

需要在 chat store 中添加 `setDataTables` 方法：

```typescript
// frontend/src/store/modules/chat.ts
setDataTables(tableIds: string[]) {
  this.selectedDataTables = tableIds
}
```

需要在 dataPrep store 中添加 `getDataTablesBySourceId` 方法：

```typescript
// frontend/src/store/modules/dataPrep.ts
getDataTablesBySourceId(sourceId: string) {
  // 返回指定数据源下的所有数据表
  return this.dataTables.filter(table => table.dataSourceId === sourceId)
}
```

### 4. 样式修改

```css
.source-select {
  width: 200px;
}

.table-select {
  width: 100%;
  max-width: 400px;
}

.data-table-selector {
  flex: 1;
  max-width: 500px;
}
```

## 实施步骤

1. 备份当前 Home.vue 文件
2. 修改模板部分（拆分为两行）
3. 修改 script 部分（状态变量、计算属性、事件处理）
4. 修改 store（添加必要的方法）
5. 测试功能
6. 调整样式

## 测试要点

1. 数据源选择后，数据表下拉框应该显示对应的数据表
2. 未选择数据源时，数据表下拉框应该禁用
3. 选择数据源后，之前选择的数据表应该被清空
4. 预览按钮在未选择数据表时应该禁用
5. 点击预览按钮应该显示数据表预览对话框
6. 发送消息时应该同时包含数据源和数据表信息
