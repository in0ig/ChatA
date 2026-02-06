# Home.vue 多表预览数据更新修复完成报告

## 问题描述

用户选择2个数据表并点击预览按钮后，预览模态框中的下拉框可以切换表，但"字段预览"和"数据预览"区域的数据没有随之更新，始终显示第一个表的数据。

## 根本原因

`frontend/src/views/Home.vue` 中的 `handleDataSourcePreview` 函数使用的是**硬编码的假数据**，而不是调用真实的后端 API。因此无论切换到哪个表，显示的都是相同的假数据。

## 修复内容

### 1. 添加 dataTableApi 导入
```typescript
import { dataTableApi } from '@/services/dataTableApi'
```

### 2. 重写 handleDataSourcePreview 函数
将硬编码的假数据替换为真实的 API 调用：

**修复前（使用假数据）：**
```typescript
const handleDataSourcePreview = (table) => {
  previewData.value = {
    schema: [
      { name: 'id', type: 'int', description: '主键ID', ... },
      // ... 硬编码的假数据
    ],
    data: [
      { id: 1, name: '张三', age: 25, ... },
      // ... 硬编码的假数据
    ]
  }
  dataPreviewModalVisible.value = true
}
```

**修复后（调用真实 API）：**
```typescript
const handleDataSourcePreview = async (table) => {
  try {
    // 显示加载状态
    uiStore.setLoading(true, '正在加载表预览数据...')
    
    // 调用后端 API 获取表字段信息
    const fields = await dataTableApi.getFields(table.id)
    
    // 调用后端 API 获取表数据预览
    const data = await dataTableApi.getPreview(table.id, 100)
    
    // 转换字段信息为预览格式
    const schema = fields.map(field => ({
      name: field.field_name,
      type: field.data_type,
      description: field.description || '',
      unit: '',
      category: '',
      isPrimaryKey: field.is_primary_key
    }))
    
    // 更新预览数据
    previewData.value = {
      schema,
      data
    }
    
    // 打开预览模态框
    dataPreviewModalVisible.value = true
    
  } catch (error) {
    console.error('加载表预览数据失败:', error)
    ElMessage.error('加载表预览数据失败，请稍后重试')
    
    // 即使失败也显示空数据，避免界面卡住
    previewData.value = {
      schema: [],
      data: []
    }
  } finally {
    uiStore.setLoading(false)
  }
}
```

### 3. 更新 handlePreviewTableChange 函数
添加 async/await 支持：

```typescript
const handlePreviewTableChange = async (tableId) => {
  const table = selectedTablesForPreview.value.find(t => t.id === tableId)
  if (table) {
    await handleDataSourcePreview(table)
  }
}
```

## 修复的文件

- `frontend/src/views/Home.vue`
  - 添加了 `dataTableApi` 导入
  - 重写了 `handleDataSourcePreview` 函数，使用真实 API
  - 更新了 `handlePreviewTableChange` 函数，添加 async/await

## 验证结果

- ✅ TypeScript 检查通过（无类型错误）
- ✅ 导入语句正确添加
- ✅ API 调用逻辑正确实现
- ✅ 错误处理完善（try-catch + ElMessage）
- ✅ 加载状态管理（uiStore.setLoading）

## 功能说明

现在当用户在多表预览模态框中切换表时：

1. **用户操作**：在下拉框中选择不同的表
2. **事件触发**：`DataPreviewModal.vue` 触发 `table-change` 事件
3. **接收事件**：`Home.vue` 的 `handlePreviewTableChange` 接收表ID
4. **查找表对象**：根据ID在 `selectedTablesForPreview` 中查找表对象
5. **调用 API**：
   - 调用 `dataTableApi.getFields(tableId)` 获取字段信息
   - 调用 `dataTableApi.getPreview(tableId, 100)` 获取数据预览
6. **数据转换**：将后端返回的字段格式转换为前端需要的格式
7. **更新状态**：更新 `previewData` 响应式数据
8. **UI 更新**：模态框自动显示新表的字段和数据

## API 使用

### dataTableApi.getFields(tableId)
- **功能**：获取指定表的字段信息
- **返回**：`TableField[]` 数组
- **字段**：
  - `field_name`: 字段名
  - `data_type`: 数据类型
  - `description`: 字段描述
  - `is_primary_key`: 是否主键
  - `is_nullable`: 是否可空

### dataTableApi.getPreview(tableId, limit)
- **功能**：获取指定表的数据预览
- **参数**：
  - `tableId`: 表ID
  - `limit`: 返回记录数（默认100）
- **返回**：`any[]` 数据数组

## 注意事项

1. **字段名映射**：后端返回 `field_name`，前端需要映射为 `name`
2. **数据类型映射**：后端返回 `data_type`，前端需要映射为 `type`
3. **主键标识**：后端返回 `is_primary_key`，前端需要映射为 `isPrimaryKey`
4. **错误处理**：API 调用失败时显示错误提示，并设置空数据避免界面卡住
5. **加载状态**：使用 `uiStore.setLoading()` 显示加载提示

## 测试建议

1. **单表预览**：选择1个表，点击预览，验证数据正确显示
2. **多表切换**：选择2个表，点击预览，在下拉框中切换，验证数据随之更新
3. **错误处理**：模拟 API 失败，验证错误提示正确显示
4. **加载状态**：验证加载过程中显示"正在加载表预览数据..."提示

## 完成时间

2026-02-06
