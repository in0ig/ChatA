# 多表预览和表关联功能改进

## 改进内容

### 1. 多表预览功能改进
- ✅ 在预览对话框中添加下拉框，允许用户选择要预览的表
- ✅ 添加"表关联"标签页，显示选中表之间的关联关系
- ✅ 使用实际的表关联数据（从后端API获取）

### 2. 表关联数据
- ✅ 已创建订单表(orders)和用户表(users)的关联关系
- 关联ID: 7da27458-46d3-4c88-8726-1cba33d69643
- 关联名称: 订单-用户关联
- 主表: orders.user_id
- 从表: users.id
- 连接类型: LEFT JOIN

## 已完成的修改

### 1. DataPreviewModal.vue 组件改进

#### 新增功能：
1. **表选择下拉框**：当选择多个表时，显示下拉框让用户选择要预览的表
2. **表关联标签页**：新增"表关联"标签页，显示表之间的关联关系
3. **实时加载关联数据**：从后端API `/api/table-relations` 获取实际的关联数据

#### 新增Props：
- `selectedTables`: 选中的表列表，格式为 `[{ id, name }, ...]`

#### 新增Events：
- `table-change`: 当用户切换预览的表时触发，传递新的表ID

#### 新增State：
- `currentTableId`: 当前选中要预览的表ID
- `loadingRelations`: 表关联数据加载状态
- `tableRelations`: 表关联数据列表

### 2. Home.vue 组件改进

#### 新增State：
- `selectedTablesForPreview`: 保存选中的表列表，用于传递给DataPreviewModal

#### 修改逻辑：
1. 在`openDataTablePreview`函数中保存选中的表列表
2. 多表预览时默认预览第一个表
3. 新增`handlePreviewTableChange`函数处理表切换事件

### 3. 后端表关联数据

已通过脚本 `backend/create_order_user_relation.py` 创建了订单表和用户表的关联关系：

```python
# 关联信息
- 关联名称: 订单-用户关联
- 主表: orders (user_id字段)
- 从表: users (id字段)
- 连接类型: LEFT JOIN
- 描述: 订单表通过 user_id 关联到用户表的 id
```

## 使用方法

### 前端使用

1. 在Home页面选择多个数据表
2. 点击"预览"按钮
3. 在预览对话框中：
   - 使用顶部的下拉框切换要预览的表
   - 切换到"表关联"标签页查看表之间的关联关系
   - 查看字段信息和数据预览

### 后端API

获取表关联列表：
```
GET /api/table-relations
Query参数：
- primary_table_id: 主表ID（可选）
- foreign_table_id: 从表ID（可选）
- status: 是否启用（可选）
- skip: 分页偏移（默认0）
- limit: 每页数量（默认10）
```

响应格式：
```json
[
  {
    "id": "uuid",
    "relation_name": "订单-用户关联",
    "primary_table_id": "uuid",
    "primary_table_name": "orders",
    "primary_field_id": "uuid",
    "primary_field_name": "user_id",
    "primary_field_type": "INTEGER",
    "foreign_table_id": "uuid",
    "foreign_table_name": "users",
    "foreign_field_id": "uuid",
    "foreign_field_name": "id",
    "foreign_field_type": "INTEGER",
    "join_type": "LEFT",
    "description": "订单表通过 user_id 关联到用户表的 id",
    "status": true,
    "created_by": "system",
    "created_at": "2026-02-06T...",
    "updated_at": "2026-02-06T..."
  }
]
```

## 测试验证

### 1. 验证表关联数据
```bash
cd backend
python create_order_user_relation.py
```

### 2. 测试前端功能
1. 启动后端服务：`cd backend && python -m uvicorn src.main:app --reload`
2. 启动前端服务：`cd frontend && npm run dev`
3. 访问Home页面
4. 选择多个数据表（包括orders和users）
5. 点击预览按钮
6. 验证：
   - 下拉框是否显示所有选中的表
   - 切换表时数据是否正确更新
   - "表关联"标签页是否显示订单-用户关联

## 文件清单

### 修改的文件：
1. `frontend/src/components/DataSource/DataPreviewModal.vue` - 数据预览模态框组件
2. `frontend/src/views/Home.vue` - 主页组件

### 新增的文件：
1. `backend/create_order_user_relation.py` - 创建表关联关系的脚本

### 相关的后端API：
1. `backend/src/api/table_relation.py` - 表关联API接口

## 注意事项

1. **API路径**：确保前端axios配置正确，能够访问 `/api/table-relations` 端点
2. **数据格式**：后端返回的字段名使用下划线命名（如 `primary_table_id`），前端需要正确映射
3. **错误处理**：当API调用失败时，会显示空状态或错误提示
4. **性能优化**：表关联数据在切换到"表关联"标签页时才加载，避免不必要的请求

## 后续改进建议

1. **缓存机制**：对表关联数据进行缓存，避免重复请求
2. **关联图可视化**：使用图形化方式展示表之间的关联关系
3. **关联管理**：在预览界面中提供创建、编辑、删除关联的功能
4. **智能推荐**：根据字段名和类型自动推荐可能的关联关系
