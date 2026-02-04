# ChatBI - 智能数据分析助手

ChatBI 是一个模仿腾讯云 ChatBI 的智能数据分析平台，支持通过自然语言查询进行数据可视化和分析。

## 🚀 快速启动

### 一键启动（推荐）

```bash
# 进入项目目录
cd /path/to/ChatBI

# 启动所有服务
./scripts/start.sh

# 访问应用
# 前端: http://localhost:3000
# API文档: http://localhost:8000/docs
```

### 停止服务

```bash
./scripts/stop.sh
```

## 📦 首次安装

### 1. 环境要求

- Python 3.12+
- Node.js 18+
- npm 8+
- MySQL 8+

### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -e .
```

### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 4. 数据库初始化

```bash
# 启动 MySQL
brew services start mysql

# 初始化数据库
mysql -u root < database/init.sql
```

### 5. 环境配置

编辑 `backend/.env` 文件：

```env
# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=chatbi

# 模型配置
MODEL_TYPE=local
QWEN_MODEL_NAME=qwen-agent

# 日志配置
LOG_LEVEL=INFO
DEBUG=false
```

## 🔧 手动启动

如果不使用启动脚本，可以手动启动各服务：

### 启动后端

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动前端

```bash
cd frontend
npm run dev
```

## 📊 日志系统

ChatBI 提供完善的日志系统，方便开发调试和问题排查。

### 后端日志

后端使用 Python logging 模块，所有模块统一输出到日志文件。

**日志文件位置**: `backend/backend/backend.log`

**日志格式**:
- 普通日志: `[时间] [级别] [模块名] - 消息`
- 错误日志: `[时间] [级别] [模块名] [文件:行号 函数名] - 消息`

**查看日志**:
```bash
# 实时查看后端日志
tail -f backend/backend/backend.log

# 或查看项目根目录的日志（启动脚本输出）
tail -f backend.log
```

**日志级别配置**: 在 `backend/.env` 中设置 `LOG_LEVEL`
- `DEBUG`: 详细调试信息
- `INFO`: 一般运行信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息

**已启用日志的模块**:
- API 层: `query_api`, `session_api`, `data_source_api`, `history_api`, `settings_api`
- 服务层: `query_service`, `session_service`, `nlu_service`, `context_manager`, `token_manager`
- 核心: `sql_generator_qwen`, `qwen_integration`, `cache_service`

### 前端日志

前端使用浏览器控制台和 localStorage 存储日志。

**查看方式**:
1. 打开浏览器开发者工具 (F12)
2. 切换到 Console 标签
3. 日志按类型分组显示（API Request/Response/Error, State Change, Action 等）

**日志类型**:
- `API Request/Response/Error`: API 调用日志
- `State Changed`: Pinia Store 状态变更
- `Action Started/Success/Error`: Store Action 执行日志
- `Router Navigation`: 路由导航日志

**localStorage 日志**:
- 日志同时保存到 localStorage，可在 Application > Local Storage 中查看
- 日志 key: `chatbi_api_logs`, `chatbi_store_logs`, `chatbi_router_logs`

### 调试技巧

1. **后端调试**: 设置 `LOG_LEVEL=DEBUG` 获取详细日志
2. **前端调试**: 使用浏览器 Network 标签查看 API 请求
3. **数据库调试**: 检查 MySQL 慢查询日志
4. **实时监控**: 使用 `tail -f` 实时查看日志文件

## 🏗️ 项目架构

```
ChatBI/
├── backend/           # Python FastAPI 后端
│   ├── src/
│   │   ├── api/       # API 路由
│   │   ├── services/  # 业务逻辑
│   │   ├── models/    # 数据模型
│   │   └── utils.py   # 工具函数（含日志配置）
│   ├── tests/         # 测试文件
│   └── .env           # 环境配置
├── frontend/          # Vue 3 前端
│   ├── src/
│   │   ├── components/  # Vue 组件
│   │   ├── store/       # Pinia Store
│   │   ├── services/    # API 服务
│   │   └── router/      # 路由配置
│   └── tests/           # 测试文件
├── database/          # 数据库脚本
├── scripts/           # 启动/停止脚本
└── .kiro/             # Kiro 配置和规范
```

## ✨ 功能特性

- ✅ 自然语言查询（NLQ）
- ✅ 支持 Excel 和 MySQL 数据源
- ✅ 时间表达式识别（"上月"、"本周"等）
- ✅ 图表和数据表格双模式显示
- ✅ 多轮对话和上下文记忆
- ✅ Token 使用统计和管理
- ✅ 会话历史管理
- ✅ 数据准备功能（建表、数据填报）
- ✅ 权限配置（功能权限、数据表权限）
- ✅ 完善的日志系统

## 🧪 运行测试

### 后端测试

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

### 前端测试

```bash
cd frontend
npm run test -- --run
```

### 性能测试

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/performance/ -v
```

## 🔍 故障排查

### 启动失败：虚拟环境不存在

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 启动失败：导入错误

如果启动时出现 `ImportError: cannot import name 'NLUParser'` 或其他导入错误，请参考 [DEPLOYMENT_FIXES.md](DEPLOYMENT_FIXES.md) 获取详细的修复说明。

### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000  # 后端
lsof -i :3000  # 前端

# 终止进程
kill -9 <PID>
```

### 数据库连接失败

```bash
# 检查 MySQL 是否运行
brew services list | grep mysql

# 启动 MySQL
brew services start mysql

# 验证连接
mysql -u root -p -e "SELECT 1"
```

### 查看详细错误

```bash
# 后端日志
tail -100 backend/backend/backend.log

# 启动脚本日志
tail -100 backend.log
tail -100 frontend.log
```

## 📚 更多文档

- [部署指南](DEPLOYMENT.md) - 详细部署说明
- [快速启动](QUICK_START.md) - 30秒快速上手
- [项目概览](PROJECT_OVERVIEW.md) - 完整功能说明
- [API 文档](http://localhost:8000/docs) - 在线 API 文档

## 🤝 开发规范

1. 遵循 Spec-Driven Development 流程
2. 所有代码变更必须有测试用例
3. 使用中文编写注释和文档
4. 代码审查通过后才能合并

## 📞 联系我们

如有问题，请联系项目团队。
