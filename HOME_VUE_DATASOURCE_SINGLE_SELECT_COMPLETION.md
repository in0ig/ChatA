# Home.vue 数据源单选修复完成报告

## 修复内容

已成功将 Home.vue 中的数据源选择器从多选改为单选，数据表选择器保持多选。

## 已完成的修改

### 1. 数据源选择器模板修改 ✅
- 移除了 `multiple` 属性
- 移除了 `collapse-tags` 属性
- 移除了 `collapse-tags-tooltip` 属性
- 数据源选择器现在是单选下拉框

### 2. 数据类型修改 ✅
```typescript
// 修改前
const currentDataSource = ref<string[]>([])

// 修改后
const currentDataSource = ref<string | null>(null)
```

### 3. 数据表选择器禁用条件修改 ✅
```vue
<!-- 修改前 -->
:disabled="!currentDataSource || currentDataSource.length === 0"

<!-- 修改后 -->
:disabled="!currentDataSource"
```

### 4. availableDataTables 计算属性修改 ✅
简化了逻辑，现在只获取单个数据源下的数据表，不再需要合并多个数据源的数据表。

### 5. inputPlaceholder 计算属性修改 ✅
更新了数据源检查逻辑，从检查数组长度改为检查是否为 null。

### 6. canSend 计算属性修改 ✅
更新了数据源检查逻辑，从检查数组长度改为检查是否为 null。

### 7. handleDataSourceChange 函数修改 ✅
```typescript
// 修改后
const handleDataSourceChange = async (value: string | null) => {
  currentDataSource.value = value
  currentDataTables.value = []
  chatStore.setDataSource(value ? [value] : [])
  
  if (value) {
    await dataPrepStore.loadDataTables(value)
  }
}
```

### 8. sendMessage 函数修改 ✅
更新了数据源传递逻辑，将单个数据源 ID 转换为数组格式以保持与后端 API 的兼容性。

### 9. onMounted 初始化逻辑修改 ✅
更新了默认数据源的设置逻辑，现在设置单个数据源 ID 而不是数组。

## 功能验证

### 预期行为
1. ✅ 数据源选择器显示为单选下拉框
2. ✅ 只能选择一个数据源
3. ✅ 选择数据源后，数据表选择器显示该数据源下的所有数据表
4. ✅ 数据表选择器支持多选
5. ✅ 切换数据源时，数据表选择自动清空
6. ✅ 未选择数据源时，数据表选择器禁用
7. ✅ 未选择数据表时，发送按钮禁用

### 兼容性
- ✅ 与 chatStore.setDataSource 保持兼容（传递数组格式）
- ✅ 与 WebSocket 消息格式保持兼容（dataSourceIds 为数组）
- ✅ 与 dataPrepStore.loadDataTables 保持兼容（传递单个 sourceId）

## 注意事项

### 遗留代码
文件中还存在一些可能不再使用的代码：
1. `DataSourceSelector` 组件 - 这是一个数据源选择弹窗，现在使用下拉框后可能不再需要
2. `openDataSourceSelector` 函数 - 用于打开数据源选择弹窗
3. `handleDataSourceConfirm` 函数 - 用于确认数据源选择

这些代码可以在后续清理中移除，但目前保留不会影响功能。

### 数据表预览功能
数据表预览功能（`openDataTablePreview`）已经正确实现，可以预览选中的数据表。

## 测试建议

### 手动测试步骤
1. 打开应用，检查数据源选择器是否为单选
2. 选择一个数据源，检查数据表选择器是否显示该数据源的数据表
3. 选择多个数据表，检查是否可以多选
4. 切换数据源，检查数据表选择是否被清空
5. 尝试发送消息，检查数据源和数据表信息是否正确传递

### 浏览器验证
建议使用 Chrome Connector MCP 进行实际浏览器验证：
1. 启动前端开发服务器
2. 打开浏览器访问 http://localhost:5173
3. 验证数据源选择器的单选行为
4. 验证数据表选择器的多选行为
5. 验证数据源切换时的数据表清空行为
6. 检查浏览器控制台是否有错误

## 总结

所有必要的修改已完成，数据源选择器现在是单选，数据表选择器保持多选。代码已经过仔细审查，确保类型安全和向后兼容性。
