# Home.vue 数据表选择器"无数据"问题修复

## 问题描述

用户报告在 Home.vue 页面中，选择数据源后，数据表选择器显示"无数据"（No data），而不是显示该数据源下的可用数据表。

## 问题分析

### 根本原因

`handleDataSourceChange` 函数在数据源变更时，**没有调用 `dataPrepStore.loadDataTables(value)` 来加载选中数据源的数据表**。

### 原始代码（有问题）

```typescript
// 数据源变更
const handleDataSourceChange = (value) => {
  currentDataSource.value = value
  // 清空数据表选择
  currentDataTables.value = []
  chatStore.setDataSource(value)
}
```

### 问题点

1. ❌ 没有调用 `dataPrepStore.loadDataTables(value)` 加载数据表
2. ❌ 函数不是 `async`，无法等待异步操作
3. ❌ 传递给 `chatStore.setDataSource()` 的参数格式不正确（应该是数组）
4. ❌ 没有类型注解

## 解决方案

### 修复后的代码

```typescript
// 数据源变更
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

### 修复要点

1. ✅ 添加 `async` 关键字，使函数支持异步操作
2. ✅ 添加 TypeScript 类型注解 `value: string | null`
3. ✅ 调用 `dataPrepStore.loadDataTables(value)` 加载数据表
4. ✅ 使用 `await` 等待数据表加载完成
5. ✅ 修正 `chatStore.setDataSource()` 的参数格式（转换为数组）
6. ✅ 添加 `if (value)` 检查，避免空值时调用 API

## 数据流程

### 修复前

```
用户选择数据源
  ↓
handleDataSourceChange 被调用
  ↓
更新 currentDataSource
  ↓
清空 currentDataTables
  ↓
❌ 没有加载新数据表
  ↓
availableDataTables 返回空数组
  ↓
数据表选择器显示"无数据"
```

### 修复后

```
用户选择数据源
  ↓
handleDataSourceChange 被调用
  ↓
更新 currentDataSource
  ↓
清空 currentDataTables
  ↓
✅ 调用 dataPrepStore.loadDataTables(value)
  ↓
✅ 从后端 API 加载数据表
  ↓
✅ 更新 store 中的 dataTables
  ↓
availableDataTables 计算属性返回过滤后的数据表
  ↓
数据表选择器显示可用数据表
```

## 相关代码

### availableDataTables 计算属性

```typescript
const availableDataTables = computed(() => {
  if (!currentDataSource.value) {
    return []
  }
  // 获取单个数据源下的数据表
  return dataPrepStore.getDataTablesBySourceId(currentDataSource.value) || []
})
```

### dataPrepStore.loadDataTables 方法

位置：`frontend/src/store/modules/dataPrep.ts`

```typescript
async loadDataTables(sourceId?: string, useCache: boolean = true) {
  const uiStore = useUIStore()
  const cacheKey = sourceId || 'all'
  
  // 检查缓存...
  
  try {
    let data: any
    if (sourceId) {
      data = await dataTableApi.getBySourceId(sourceId)
    } else {
      data = await dataTableApi.getAll()
    }
    
    // 确保 data 是数组
    let dataArray: DataTable[] = []
    if (Array.isArray(data)) {
      dataArray = data
    } else if (data && typeof data === 'object') {
      if (Array.isArray(data.items)) {
        dataArray = data.items
      } else if (Array.isArray(data.data)) {
        dataArray = data.data
      }
    }
    
    this.dataTables = dataArray
    
    // 更新缓存...
  } catch (error: any) {
    console.error('加载数据表失败:', error)
    this.dataTables = []
    uiStore.showToast(error?.message || '加载数据表失败', 'error')
  }
}
```

## 验证结果

### TypeScript 检查

```bash
✅ No TypeScript errors
```

### 预期行为

1. ✅ 用户选择数据源
2. ✅ 数据表选择器自动加载该数据源下的数据表
3. ✅ 数据表选择器显示可用的数据表列表
4. ✅ 用户可以选择一个或多个数据表

## 修改文件

- `frontend/src/views/Home.vue` (第 436-449 行)

## 相关问题

这个问题是在之前的数据源单选修复（HOME_VUE_DATASOURCE_SINGLE_SELECT_FIX.md）中引入的，当时修改了数据源选择器从多选改为单选，但没有正确实现数据表的加载逻辑。

## 下一步

建议进行浏览器验证，确保：
1. 选择数据源后，数据表选择器正确显示数据表列表
2. 切换数据源时，数据表列表正确更新
3. 没有控制台错误
4. 数据表选择功能正常工作
