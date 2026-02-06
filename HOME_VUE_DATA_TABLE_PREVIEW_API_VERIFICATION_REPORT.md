# Home.vue 数据表预览 API 验证报告

## 验证环境
- 前端地址: http://127.0.0.1:5173
- 验证页面: / (首页)
- 验证时间: 2026-02-06 15:29

## 问题分析

### 原始问题
用户报告点击预览按钮时出现错误：
- 错误请求: `http://127.0.0.1:5173/api/table-relations?limit=100`
- 控制台错误: "加载表预览数据失败，请稍后重试"

### 代码修复情况

#### ✅ 已修复: `frontend/src/services/dataTableApi.ts`
- `getFields()` 方法已正确修改为调用 `/data-tables/${tableId}/columns`
- `getPreview()` 方法已正确修改为返回空数组（后端未实现）

#### ❌ 未修复: 浏览器缓存问题
- 浏览器返回 304 (Not Modified)，使用了缓存的旧版本
- 即使执行硬刷新 (Ctrl+Shift+R)，HTTP 缓存仍然生效

#### ⚠️ 发现新问题: `DataPreviewModal.vue` 中的 API 调用
- 文件位置: `frontend/src/components/DataSource/DataPreviewModal.vue:300`
- 问题代码: `axios.get('/api/table-relations', { params: { limit: 100 } })`
- 这个调用是为了加载表关联关系，与数据表字段预览无关
- 但这个调用也会失败，因为它没有使用正确的 API 路径

## 浏览器验证结果

### 验证步骤
1. ✅ 打开首页 http://127.0.0.1:5173/
2. ✅ 选择数据源 "mysql_test_source"
3. ✅ 自动加载数据表 "orders" 和其他表
4. ✅ 点击"预览"按钮
5. ✅ 预览模态框打开，显示"多表预览 (2 个表)"

### 网络请求分析
- **reqid=411, 412, 413**: `GET /api/table-relations?limit=100` - 返回 200，但这是错误的 API 调用

### 控制台错误
- **msgid=183, 184, 185**: "加载表预览数据失败" - 来自 `Home.vue:539`

### 截图
- 文件: `verification_preview_error_still_exists.png`
- 显示: 预览模态框打开，但显示"暂无数据可预览"

## 根本原因

### 问题 1: 浏览器缓存
- Vite 开发服务器返回 304 状态码
- 浏览器使用缓存的旧版本 JavaScript 文件
- 需要清除浏览器缓存或重启 Vite 开发服务器

### 问题 2: 错误的 API 调用来源
实际上有两个地方在调用 API：

1. **Home.vue** (handleDataSourcePreview 函数):
   ```typescript
   const fields = await dataTableApi.getFields(table.id)  // ✅ 已修复
   const data = await dataTableApi.getPreview(table.id, 100)  // ✅ 已修复
   ```

2. **DataPreviewModal.vue** (loadTableRelations 函数):
   ```typescript
   const response = await axios.get('/api/table-relations', {  // ❌ 未修复
     params: { limit: 100 }
   })
   ```

## 解决方案

### 方案 1: 清除浏览器缓存（临时）
```bash
# 在浏览器中
1. 打开开发者工具 (F12)
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"
```

### 方案 2: 重启 Vite 开发服务器（推荐）
```bash
# 停止当前服务器
Ctrl+C

# 重新启动
cd frontend
npm run dev
```

### 方案 3: 修复 DataPreviewModal.vue 中的 API 调用
需要修改 `frontend/src/components/DataSource/DataPreviewModal.vue:300` 行：
```typescript
// 修改前
const response = await axios.get('/api/table-relations', {
  params: { limit: 100 }
})

// 修改后 - 使用正确的 API 路径
const response = await axios.get('/api/table-relations/', {  // 添加尾部斜杠
  params: { limit: 100 }
})
```

或者使用 tableRelationApi:
```typescript
import { tableRelationApi } from '@/services/tableRelationApi'

// 使用 API 服务
const relations = await tableRelationApi.getAll()
```

## 验收结论

### ❌ 验证未完全通过

**已完成的修复:**
- ✅ `dataTableApi.getFields()` 调用正确的端点
- ✅ `dataTableApi.getPreview()` 返回空数组（后端未实现）

**仍需修复:**
- ❌ 浏览器缓存导致旧代码仍在运行
- ❌ `DataPreviewModal.vue` 中的表关联 API 调用需要修复
- ❌ 需要重启 Vite 开发服务器以清除缓存

## 下一步行动

1. **立即**: 重启 Vite 开发服务器
2. **可选**: 修复 `DataPreviewModal.vue` 中的表关联 API 调用
3. **验证**: 重新测试预览功能，确保无错误

## 技术说明

### 为什么硬刷新无效？
- Vite 使用 HTTP 缓存头 (ETag, If-None-Match)
- 即使硬刷新，如果文件内容的 ETag 匹配，服务器返回 304
- 只有重启服务器才能强制重新编译和提供新文件

### 为什么会有两个 API 调用？
- `handleDataSourcePreview` 负责加载表字段和数据
- `DataPreviewModal` 负责显示预览，并额外加载表关联关系
- 这两个功能是独立的，但都在预览流程中执行
