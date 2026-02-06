# Home.vue 数据源/数据表选择修复完成总结

## 任务概述

修复 Home.vue 中的数据源和数据表选择 UI/UX 问题，实现正确的单选数据源和多选数据表功能。

## 完成内容

### 1. Store 修改

#### `frontend/src/store/modules/chat.ts`
- ✅ 添加 `selectedDataTables: string[]` 状态字段
- ✅ 添加 `setDataTables(tableIds: string[])` 方法
- ✅ 修改 `setDataSource` 方法支持单个字符串或数组参数

#### `frontend/src/store/modules/dataPrep.ts`
- ✅ 添加 `getDataTablesBySourceId(sourceId: string)` 方法（别名）
- ✅ 保持与现有 `getTablesBySourceId` 方法的兼容性

#### `frontend/src/types/chat.ts`
- ✅ 在 `ChatState` 接口中添加 `selectedDataTables: string[]` 字段

### 2. Home.vue 组件修改

#### 模板部分
- ✅ 已有两行结构（第一行：数据源 + 模式切换，第二行：数据表 + 预览）
- ✅ 数据源选择器为单选模式
- ✅ 数据表选择器为多选模式（带 collapse-tags）
- ✅ 数据表选择器在未选择数据源时禁用
- ✅ 预览按钮在未选择数据表时禁用

#### Script 部分
- ✅ 添加 `handleDataSourceChange(value)` - 数据源变更处理
- ✅ 添加 `handleDataTableChange(values)` - 数据表变更处理
- ✅ 添加 `openDataTablePreview()` - 打开数据表预览
- ✅ 添加 `handleDataTablePreview(table)` - 处理数据表预览
- ✅ 删除重复的旧版本 `handleDataSourceChange` 函数

#### 样式部分
- ✅ 添加 `.table-select` 样式（width: 100%, max-width: 400px）
- ✅ 添加 `.data-table-selector` 样式（flex: 1, max-width: 500px）
- ✅ 保持现有 `.source-select` 样式（width: 180px）

## 功能验收

### ✅ 已实现的功能

1. **数据源选择**
   - 单选模式（不再是多选）
   - 选择数据源后自动清空已选数据表
   - 更新 store 中的数据源状态

2. **数据表选择**
   - 多选模式（支持复选框）
   - 根据选中的数据源动态显示可用数据表
   - 未选择数据源时禁用
   - 更新 store 中的数据表状态

3. **预览功能**
   - 预览按钮在未选择数据表时禁用
   - 单表选择时直接预览
   - 多表选择时显示选择对话框
   - 显示表结构和数据（当前使用 Mock 数据）

4. **UI 布局**
   - 第一行：数据源下拉框 + 模式切换开关
   - 第二行：数据表下拉框 + 预览按钮
   - 响应式设计保持完整

## 技术验证

### TypeScript 检查
```bash
✅ 无 TypeScript 编译错误
- frontend/src/views/Home.vue: No diagnostics
- frontend/src/store/modules/chat.ts: No diagnostics
- frontend/src/store/modules/dataPrep.ts: No diagnostics
- frontend/src/types/chat.ts: No diagnostics
```

### 代码质量
- ✅ 使用 Composition API
- ✅ 正确使用 Pinia Store
- ✅ 中文注释完整
- ✅ 命名符合规范（camelCase）
- ✅ 无重复代码

## 文件清单

修改的文件：
1. `frontend/src/views/Home.vue` - 主要修改
2. `frontend/src/store/modules/chat.ts` - 添加数据表状态和方法
3. `frontend/src/store/modules/dataPrep.ts` - 添加获取数据表方法
4. `frontend/src/types/chat.ts` - 更新类型定义

## 后续建议

1. **API 集成**
   - 当前 `handleDataTablePreview` 使用 Mock 数据
   - 需要集成真实的后端 API 获取表结构和数据

2. **测试**
   - 建议添加单元测试验证数据源/数据表选择逻辑
   - 测试数据源变更时清空数据表的行为
   - 测试预览按钮的启用/禁用逻辑

3. **用户体验优化**
   - 考虑添加加载状态指示器
   - 添加数据表预览的缓存机制
   - 优化大量数据表时的性能

## 验收标准对照

根据 `HOME_VUE_FIX_PLAN.md` 的要求：

- ✅ 数据源选择器改为单选模式
- ✅ 添加数据表选择器（多选，带复选框）
- ✅ 预览按钮预览数据表数据（不是数据源选择器）
- ✅ 数据表选择器在未选数据源时禁用
- ✅ 选择新数据源时清空已选数据表
- ✅ 预览按钮在未选数据表时禁用
- ✅ Store 方法完整实现
- ✅ 样式正确应用
- ✅ 无 TypeScript 错误

## 总结

Home.vue 的数据源/数据表选择功能已成功修复，所有需求均已实现。代码质量良好，无 TypeScript 错误，符合项目开发规范。
