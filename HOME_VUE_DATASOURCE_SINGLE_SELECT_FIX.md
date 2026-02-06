# Home.vue 数据源单选修复计划

## 问题描述

当前 Home.vue 中的数据源选择器和数据表选择器都支持多选，但用户需求是：
- **数据源：单选**（只能选择一个数据源）
- **数据表：多选**（可以选择多个数据表）

## 当前实现分析

### 数据源选择器（第 241-254 行）
```vue
<el-select 
  v-model="currentDataSource" 
  placeholder="请选择数据源" 
  class="source-select"
  multiple                    <!-- ❌ 需要移除 -->
  collapse-tags               <!-- ❌ 需要移除 -->
  collapse-tags-tooltip       <!-- ❌ 需要移除 -->
  @change="handleDataSourceChange"
>
```

### 数据表选择器（第 274-286 行）
```vue
<el-select 
  v-model="currentDataTables" 
  placeholder="请选择数据表" 
  class="table-select"
  multiple                    <!-- ✅ 保留 -->
  collapse-tags               <!-- ✅ 保留 -->
  collapse-tags-tooltip       <!-- ✅ 保留 -->
  :disabled="!currentDataSource || currentDataSource.length === 0"
  @change="handleDataTableChange"
>
```

## 修复方案

### 1. 修改数据源选择器为单选

#### 1.1 修改模板（第 241-254 行）
```vue
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
```

#### 1.2 修改数据类型（第 418 行）
```typescript
// 修改前
const currentDataSource = ref<string[]>([])

// 修改后
const currentDataSource = ref<string | null>(null)
```

#### 1.3 修改数据表选择器的禁用条件（第 281 行）
```vue
<!-- 修改前 -->
:disabled="!currentDataSource || currentDataSource.length === 0"

<!-- 修改后 -->
:disabled="!currentDataSource"
```

### 2. 修改相关处理函数

#### 2.1 handleDataSourceChange（第 530-543 行）
```typescript
// 修改前
const handleDataSourceChange = async (values) => {
  currentDataSource.value = values
  currentDataTables.value = []
  chatStore.setDataSource(values)
  
  if (values && values.length > 0) {
    for (const sourceId of values) {
      await dataPrepStore.loadDataTables(sourceId)
    }
  }
}

// 修改后
const handleDataSourceChange = async (value: string | null) => {
  currentDataSource.value = value
  // 清空数据表选择
  currentDataTables.value = []
  
  // 更新 chatStore（需要传递数组格式以保持兼容性）
  chatStore.setDataSource(value ? [value] : [])
  
  // 加载选中数据源下的数据表
  if (value) {
    await dataPrepStore.loadDataTables(value)
  }
}
```

#### 2.2 修改 availableDataTables 计算属性（第 467-481 行）
```typescript
// 修改前
const availableDataTables = computed(() => {
  if (!currentDataSource.value || currentDataSource.value.length === 0) {
    return []
  }
  // 如果选择了多个数据源，合并所有数据源的数据表
  const allTables = currentDataSource.value.flatMap(sourceId => 
    dataPrepStore.getDataTablesBySourceId(sourceId) || []
  )
  // 去重（基于 id）
  const uniqueTables = Array.from(
    new Map(allTables.map(table => [table.id, table])).values()
  )
  return uniqueTables
})

// 修改后
const availableDataTables = computed(() => {
  if (!currentDataSource.value) {
    return []
  }
  // 获取单个数据源下的数据表
  return dataPrepStore.getDataTablesBySourceId(currentDataSource.value) || []
})
```

#### 2.3 修改 canSend 计算属性（第 510-515 行）
```typescript
// 修改前
const canSend = computed(() => {
  return inputText.value.trim().length > 0 && 
         currentDataSource.value && 
         currentDataSource.value.length > 0 &&
         currentDataTables.value.length > 0
})

// 修改后
const canSend = computed(() => {
  return inputText.value.trim().length > 0 && 
         currentDataSource.value !== null &&
         currentDataTables.value.length > 0
})
```

#### 2.4 修改 inputPlaceholder 计算属性（第 502-508 行）
```typescript
// 修改前
const inputPlaceholder = computed(() => {
  if (!currentDataSource.value || currentDataSource.value.length === 0) {
    return '请先选择数据源...'
  }
  if (currentDataTables.value.length === 0) {
    return '请先选择数据表...'
  }
  return chatStore.chatMode === 'query' 
    ? '输入您的问题，让 AI 分析数据...' 
    : '输入您想要生成的报告内容...'
})

// 修改后
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
```

#### 2.5 修改 sendMessage 函数（第 1001-1029 行）
```typescript
// 修改前
websocketService.send({
  type: 'query',
  content: message,
  sessionId: chatStore.currentSessionId,
  dataSourceIds: currentDataSource.value,  // 这里是数组
  mode: chatStore.chatMode
})

// 修改后
websocketService.send({
  type: 'query',
  content: message,
  sessionId: chatStore.currentSessionId,
  dataSourceIds: currentDataSource.value ? [currentDataSource.value] : [],  // 转换为数组
  mode: chatStore.chatMode
})
```

#### 2.6 修改 onMounted 初始化逻辑（第 1145-1161 行）
```typescript
// 修改前
if (dataPrepStore.dataSources.length > 0) {
  const activeSource = dataPrepStore.dataSources.find(ds => ds.isActive)
  if (activeSource) {
    currentDataSource.value = activeSource.id
    chatStore.setDataSource(activeSource.id)
  } else {
    currentDataSource.value = dataPrepStore.dataSources[0].id
    chatStore.setDataSource(dataPrepStore.dataSources[0].id)
  }
}

// 修改后
if (dataPrepStore.dataSources.length > 0) {
  const activeSource = dataPrepStore.dataSources.find(ds => ds.isActive)
  if (activeSource) {
    currentDataSource.value = activeSource.id
    chatStore.setDataSource([activeSource.id])
  } else {
    currentDataSource.value = dataPrepStore.dataSources[0].id
    chatStore.setDataSource([dataPrepStore.dataSources[0].id])
  }
}
```

## 修复步骤

1. ✅ 修改数据源选择器模板，移除 `multiple`、`collapse-tags`、`collapse-tags-tooltip` 属性
2. ✅ 修改 `currentDataSource` 的类型从 `string[]` 改为 `string | null`
3. ✅ 修改数据表选择器的禁用条件
4. ✅ 修改 `handleDataSourceChange` 函数
5. ✅ 修改 `availableDataTables` 计算属性
6. ✅ 修改 `canSend` 计算属性
7. ✅ 修改 `inputPlaceholder` 计算属性
8. ✅ 修改 `sendMessage` 函数中的数据源传递
9. ✅ 修改 `onMounted` 中的初始化逻辑

## 验证计划

### 功能验证
1. ✅ 数据源选择器只能选择一个数据源
2. ✅ 选择数据源后，数据表选择器显示该数据源下的所有数据表
3. ✅ 数据表选择器可以多选
4. ✅ 切换数据源时，数据表选择被清空
5. ✅ 发送消息时，正确传递数据源和数据表信息

### UI 验证
1. ✅ 数据源选择器显示为单选下拉框
2. ✅ 数据表选择器显示为多选下拉框（带标签折叠）
3. ✅ 未选择数据源时，数据表选择器禁用
4. ✅ 未选择数据表时，发送按钮禁用

## 注意事项

1. **向后兼容性**：chatStore.setDataSource 仍然接收数组参数，保持与其他组件的兼容性
2. **类型安全**：确保所有类型定义正确，避免 TypeScript 编译错误
3. **用户体验**：切换数据源时自动清空数据表选择，避免数据不一致
4. **错误处理**：确保在数据源为 null 时，相关逻辑能正确处理

## 相关文件

- `frontend/src/views/Home.vue` - 主要修改文件
- `frontend/src/store/modules/chat.ts` - 确认 setDataSource 方法的参数类型
- `frontend/src/store/modules/dataPrep.ts` - 确认 getDataTablesBySourceId 方法
