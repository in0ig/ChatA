# 任务5.7：核心对话功能集成测试指南

## 测试概述

本文档描述了任务5.7的端到端集成测试，这些测试**必须使用真实数据和真实AI调用**，验证完整的对话流程和数据安全机制。

## 🔒 预定义测试标准（不可更改）

### 测试用例列表
1. ✅ 完整对话流程测试：意图识别→智能选表→意图澄清→SQL生成→执行→分析
2. ✅ 多轮对话上下文管理测试
3. ✅ 错误处理和自愈机制测试
4. ✅ 数据安全和隐私保护测试
5. ✅ 云端模型不接触业务数据验证
6. ✅ 本地模型数据处理验证
7. ✅ 双层历史记录数据隔离测试

### 测试覆盖率要求
- **目标覆盖率**: ≥ 80%
- **验证通过标准**: 100% 测试通过率
- **功能验收标准**: 所有核心对话流程稳定，数据安全得到完全保障

## 测试文件

### 1. test_core_dialogue_e2e.py
**核心对话功能端到端集成测试**

测试内容：
- 完整对话流程（意图识别→智能选表→意图澄清→SQL生成→执行→分析）
- 多轮对话上下文管理
- 错误处理和自愈机制
- 完整用户体验流程

### 2. test_data_privacy_security.py
**数据安全和隐私保护集成测试**

测试内容：
- 云端模型零业务数据暴露
- 数据消毒器有效性
- 本地历史记录完整性
- 上下文压缩安全性
- SQL仅传输到云端
- 会话隔离
- 元数据仅传输到云端

## 前置条件

### 1. 环境配置

```bash
# 1. 确保数据库已启动
# MySQL或SQL Server需要运行

# 2. 配置AI模型API密钥
# 在 backend/.env 中配置：
QWEN_API_KEY=your_qwen_api_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=http://localhost:11434/v1  # 本地OpenAI兼容API

# 3. 准备测试数据
# 确保数据库中有测试数据源和数据表
```

### 2. 数据准备

```sql
-- 创建测试数据源
INSERT INTO data_sources (name, db_type, host, port, database_name, username, password)
VALUES ('test_datasource', 'mysql', 'localhost', 3306, 'test_db', 'root', 'password');

-- 创建测试数据表
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    sales INT,
    revenue DECIMAL(10,2)
);

-- 插入测试数据
INSERT INTO products VALUES
(1, '产品A', 100, 15000.00),
(2, '产品B', 85, 12750.00),
(3, '产品C', 120, 18000.00);
```

## 执行测试

### 方式1：运行所有集成测试

```bash
cd backend
python -m pytest tests/integration/test_core_dialogue_e2e.py -v -s
python -m pytest tests/integration/test_data_privacy_security.py -v -s
```

### 方式2：运行单个测试

```bash
# 测试完整对话流程
python -m pytest tests/integration/test_core_dialogue_e2e.py::TestCoreDialogueE2E::test_complete_dialogue_flow_real_data -v -s

# 测试数据隐私保护
python -m pytest tests/integration/test_data_privacy_security.py::TestDataPrivacySecurity::test_cloud_model_zero_data_exposure -v -s
```

### 方式3：使用测试标记

```bash
# 运行所有集成测试
python -m pytest tests/integration/ -m integration -v -s

# 运行数据安全相关测试
python -m pytest tests/integration/ -m security -v -s
```

## 测试验收标准

### 1. 完整对话流程测试
**验收标准**：
- ✅ 意图识别准确率 > 90%
- ✅ 智能选表相关性 > 85%
- ✅ SQL生成正确率 > 95%
- ✅ 查询执行成功率 = 100%
- ✅ 结果分析完整性 = 100%

**验证方法**：
```python
# 检查结果结构
assert "intent" in result
assert "selected_tables" in result
assert "sql" in result
assert "query_result" in result

# 检查意图识别
assert result["intent"]["confidence"] > 0.7

# 检查SQL生成
assert "SELECT" in result["sql"].upper()
```

### 2. 多轮对话上下文管理测试
**验收标准**：
- ✅ 上下文正确维护
- ✅ 历史消息准确记录
- ✅ 后续问题能理解前文

**验证方法**：
```python
# 第一轮对话
result1 = await orchestrator.process_query(session_id, "查询2023年销售数据")

# 第二轮对话 - 基于上下文
result2 = await orchestrator.process_query(session_id, "那2024年的呢？")

# 验证上下文
assert "2024" in result2["sql"]
```

### 3. 数据安全和隐私保护测试
**验收标准**：
- ✅ 云端历史记录不包含任何实际数据值
- ✅ 仅包含SQL语句和状态描述
- ✅ 敏感信息完全过滤（邮箱、电话、姓名、金额）
- ✅ 本地历史包含完整数据
- ✅ 数据消毒机制有效

**验证方法**：
```python
# 获取云端历史
cloud_history = context_manager.get_cloud_history(session_id)

# 验证不包含敏感数据
for message in cloud_history:
    content = str(message.get("content", ""))
    
    # 不应包含邮箱
    assert not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
    
    # 不应包含电话号码
    assert not re.search(r'1[3-9]\d{9}', content)
    
    # 不应包含具体数值
    assert not any(char.isdigit() for char in content if char not in "SELECT FROM WHERE")
```

## 测试结果示例

### 成功的测试输出

```
✅ 完整对话流程测试通过
   - 意图: query
   - 选表数量: 2
   - SQL长度: 156 字符
   - 结果行数: 10

✅ 多轮对话上下文管理测试通过
   - 第一轮消息数: 4
   - 第二轮消息数: 8

✅ 云端模型数据隐私测试通过
   - 云端历史消息数: 6
   - 验证了邮箱、电话、姓名、金额等敏感信息均未泄露

✅ 本地模型数据处理测试通过
   - 本地分析结果完整

✅ 双层历史记录数据隔离测试通过
   - 云端历史消息数: 6
   - 本地历史消息数: 8
```

## 故障排查

### 问题1：AI模型API调用失败
**症状**：测试报错 "API key not found" 或 "Connection refused"

**解决方案**：
1. 检查 `.env` 文件中的API密钥配置
2. 确认本地OpenAI兼容服务已启动（如Ollama）
3. 验证网络连接和API端点可访问

### 问题2：数据库连接失败
**症状**：测试报错 "Can't connect to MySQL server"

**解决方案**：
1. 确认数据库服务已启动
2. 检查数据库连接配置（host、port、username、password）
3. 验证数据库用户权限

### 问题3：测试数据不存在
**症状**：测试报错 "Table not found" 或 "No data returned"

**解决方案**：
1. 运行数据准备SQL脚本
2. 确认测试数据源ID正确
3. 验证数据表结构已同步

### 问题4：上下文管理器方法不存在
**症状**：测试报错 "AttributeError: 'ContextManager' object has no attribute 'add_local_message'"

**解决方案**：
1. 使用正确的API方法：`add_user_message`, `add_sql_response`, `add_analysis_response`
2. 参考 `context_manager.py` 中的实际方法签名
3. 更新测试代码以匹配实际API

## 性能基准

### 响应时间要求
- **意图识别**: < 2秒
- **智能选表**: < 3秒
- **SQL生成**: < 5秒
- **SQL执行**: < 10秒（数据量 < 10万行）
- **数据分析**: < 5秒
- **总体响应**: < 30秒

### 并发性能要求
- **并发用户数**: > 100
- **并发请求成功率**: > 95%
- **平均响应时间**: < 20秒

## 安全性验证清单

- [ ] 云端历史记录不包含任何实际数据值
- [ ] 云端历史记录仅包含SQL和状态描述
- [ ] 敏感信息（邮箱、电话、身份证、金额）完全过滤
- [ ] 本地历史记录包含完整查询结果
- [ ] 数据消毒机制对所有敏感数据类型有效
- [ ] 会话之间完全隔离，无数据泄露
- [ ] 上下文压缩不泄露敏感数据
- [ ] 仅SQL语句传输到云端，不传输查询结果

## 持续集成

### CI/CD配置

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: password
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run integration tests
        env:
          QWEN_API_KEY: ${{ secrets.QWEN_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd backend
          python -m pytest tests/integration/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 总结

任务5.7的集成测试确保了：

1. **功能完整性**：完整的对话流程从意图识别到结果分析全部正常工作
2. **数据安全性**：云端模型零业务数据接触，本地模型完整数据处理
3. **系统稳定性**：错误处理和自愈机制有效，多轮对话上下文管理准确
4. **用户体验**：响应时间合理，结果准确完整

所有测试必须使用真实数据和真实AI调用，确保系统在生产环境中的可靠性。
