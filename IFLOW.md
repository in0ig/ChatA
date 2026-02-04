# ChatBI - 智能数据分析助手

ChatBI 是一个模仿腾讯云 ChatBI 的智能数据分析平台，支持通过自然语言查询进行数据可视化和分析。

## 项目架构

```
ChatBI/
├── backend/        # Python FastAPI 后端服务
├── frontend/       # Vue 3 前端应用
├── database/       # 数据库初始化脚本
├── scripts/        # 启动和停止脚本
└── specs/          # 项目设计文档
```

## 技术栈

- **前端**: Vue 3 + TypeScript + Vite + ECharts + Element Plus
- **后端**: Python 3.12 + FastAPI + Qwen 大模型
- **数据库**: MySQL 8+
- **部署**: Docker Compose (可选)

## 安装与运行

### 1. 准备工作

确保已安装以下软件：
- Python 3.12+
- Node.js 18+
- npm 8+
- MySQL 8+

### 2. 启动数据库

```bash
# 启动 MySQL 服务
brew services start mysql

# 初始化数据库
mysql -u root < database/init.sql
```

### 3. 启动后端服务

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

### 5. 使用启动脚本（推荐）

```bash
# 启动所有服务
./scripts/start.sh

# 停止所有服务
./scripts/stop.sh
```

## 功能特性

- ✅ 自然语言查询（NLQ）
- ✅ 支持 Excel 和 MySQL 数据源
- ✅ 时间表达式识别（"上月"、"本周"等）
- ✅ 图表和数据表格双模式显示
- ✅ 历史查询记录
- ✅ 多轮对话和上下文记忆
- ✅ 数据准备功能（建表、数据填报、字典表）
- ✅ 设置面板（主题、语言、通知）
- ✅ 前端使用 3000 端口，后端使用 8000 端口
- ✅ 前端代理 API 请求到后端（/api → http://localhost:8000）

## API 文档

后端 API 文档可通过访问 `http://localhost:8000/docs` 查看。

## 开发规范

本项目遵循 Spec-Driven Development 模式，所有开发必须先创建 Spec 文档：
- `specs/01_requirements.md` - 需求分析
- `specs/02_design.md` - 系统设计
- `specs/03_plan_and_tests.md` - 测试与任务规划

## 项目愿景

ChatBI 致力于让数据分析变得简单直观，通过自然语言交互，让非技术人员也能轻松获取数据洞察。

> "让每个人都能像对话一样分析数据"

## 贡献指南

1. 所有功能开发必须遵循 Spec-Driven Development 流程
2. 不允许直接编写业务代码，必须先完成 Spec 文档
3. 每次提交只包含一个功能点
4. 所有代码变更必须有对应的测试用例
5. 代码审查通过后才能合并到主分支
6. 使用中文编写所有注释和文档

## 开发环境配置

### 前端配置

前端项目使用 Vite 构建工具，配置文件位于 `frontend/vite.config.ts`：
- 服务端口：3000
- API 代理：`/api` 路径代理到后端 `http://localhost:8000`
- 构建输出目录：`dist`

### 后端配置

后端使用 FastAPI 框架，主入口文件为 `backend/src/main.py`，包含以下路由：
- `/api/datasources` - 数据源管理
- `/api/query` - 自然语言查询处理
- `/api/data-prep` - 数据准备功能
- `/api/settings` - 设置管理

## 项目文件结构

### 前端组件结构

```
frontend/src/
├── App.vue
├── main.js
├── assets/
│   └── styles.css
├── components/
│   ├── ChartRenderer.vue
│   ├── DataPreparation.vue
│   ├── DataSourcePanel.vue
│   ├── DataTable.vue
│   ├── ExampleQuestions.vue
│   ├── HistoryPanel.vue
│   ├── QueryInput.vue
│   ├── SessionChat.vue
│   └── Settings.vue
├── router/
│   └── index.ts
├── services/
│   └── api.ts
└── store/
    ├── index.js
    └── index.ts
```

### 后端模块结构

```
backend/src/
├── main.py
├── api/
│   ├── data_preparation_api.py
│   ├── data_source_api.py
│   ├── query_api.py
│   └── settings_api.py
├── models/
│   ├── data_preparation_model.py
│   ├── data_source_model.py
│   ├── query_result_model.py
│   ├── session_model.py
│   └── settings_model.py
├── services/
│   ├── cache_service.py
│   ├── data_preparation_service.py
│   ├── data_source_service.py
│   ├── excel_service.py
│   ├── nlu_service.py
│   ├── query_service.py
│   ├── session_service.py
│   ├── settings_service.py
│   └── utils.py
└── utils/
```

## 启动/停止脚本说明

### start.sh

自动启动前后端服务：
- 后端：在后台运行 `python3 src/main.py`，输出日志到 `backend.log`
- 前端：在后台运行 `npm run dev`，输出日志到 `frontend.log`
- 显示服务访问地址：
  - 后端：http://localhost:8000
  - 前端：http://localhost:5173
- 自动清理日志文件并保持进程运行

### stop.sh

停止所有服务：
- 查找并杀死后端进程（python3 src/main.py）
- 查找并杀死前端进程（npm run dev）
- 清理日志文件（backend.log, frontend.log）
- 创建新的空日志文件

## 依赖管理

### 前端依赖 (package.json)

```json
{
  "dependencies": {
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.7.7",
    "echarts": "^5.5.1",
    "vue": "^3.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.5.4",
    "vite": "^7.3.1",
    "vue-tsc": "^2.0.23"
  }
}
```

### 后端依赖 (pyproject.toml)

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.6",
    "pydantic>=2.8.0",
    "python-dotenv>=1.0.1",
    "mysql-connector-python>=8.4.0",
    "sqlalchemy>=2.0.31",
    "python-multipart>=0.0.9",
    "jinja2>=3.1.4",
    "aiofiles>=23.2.1",
    "openpyxl>=3.1.5",
    "pandas>=2.2.3",
    "numpy>=1.26.4",
    "qwen-agent>=0.1.0"
]
```

## 数据库 Schema

### 数据源配置表 (data_sources)
```sql
CREATE TABLE data_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type ENUM('mysql', 'excel', 'api') NOT NULL,
    connection_string TEXT,
    file_path VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 查询历史表 (query_history)
```sql
CREATE TABLE query_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    query_text TEXT NOT NULL,
    generated_sql TEXT,
    chart_type VARCHAR(50),
    result_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 查询会话表 (query_sessions)
```sql
CREATE TABLE query_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    session_id VARCHAR(100) NOT NULL,
    conversation JSON DEFAULT '{}',
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 数据字典表 (data_dictionary)
```sql
CREATE TABLE data_dictionary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_id INT,
    column_name VARCHAR(100) NOT NULL,
    alias_name VARCHAR(100),
    data_type VARCHAR(50),
    unit VARCHAR(50),
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);
```

### 字典表（用于数据标准化）
```sql
CREATE TABLE dictionary_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    value VARCHAR(100) NOT NULL,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_entry (table_name, field_name, value)
);
```

## 开发流程

1. **初始化前端项目**:
   ```bash
   cd frontend
   npm init vue
   # 选择 TypeScript, Vue Router, Pinia, Vitest
   ```

2. **初始化后端项目**:
   ```bash
   cd backend
   uv init
   uv add fastapi uvicorn python-dotenv mysql-connector-python sqlalchemy pandas numpy qwen-agent
   ```

3. **启动开发服务器**:
   ```bash
   # 启动前端
   cd ../frontend && npm run dev
   
   # 启动后端
   cd ../backend && uv run main.py
   ```

## 重要注意事项

- 前端默认端口为 3000（vite.config.ts 中配置），但启动脚本中显示为 5173，这是 Vite 的默认端口。实际运行时请以启动脚本输出为准。
- 后端 API 代理配置在前端的 vite.config.ts 中，确保开发时前端能正确访问后端服务。
- 所有开发必须遵循 Spec-Driven Development 流程，先创建 Spec 文档再进行编码。
- 使用中文编写所有注释和文档。
- 项目使用 MySQL 作为数据库，数据库初始化脚本位于 database/init.sql。
- 数据源支持 Excel 文件上传和 MySQL 数据库连接两种方式。
- 项目支持多轮对话和上下文记忆，会话信息存储在 query_sessions 表中。

## 联系我们

如有任何问题，请联系项目团队。