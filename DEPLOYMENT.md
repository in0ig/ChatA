# ChatBI 部署指南

本指南详细说明 ChatBI 项目的部署流程、环境配置、故障排查和性能优化建议。

## 部署步骤

### 1. 环境准备

确保系统已安装以下软件：

- **Python 3.12+**：用于后端服务
- **Node.js 18+**：用于前端开发服务器
- **npm 8+**：用于前端依赖管理
- **MySQL 8+**：用于数据存储
- **uv**：Python 包管理器（推荐）

### 2. 创建虚拟环境

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装后端依赖
pip install -e .
```

> **注意**：建议始终在虚拟环境中运行后端服务，以避免依赖冲突。

### 3. 初始化数据库

```bash
# 启动 MySQL 服务
brew services start mysql

# 初始化数据库（创建表结构和初始数据）
mysql -u root < database/init.sql
```

数据库初始化脚本 `database/init.sql` 会：
- 创建 `chatbi` 数据库（如果不存在）
- 创建所有必需的表（users, data_sources, query_history, query_sessions, data_dictionary, dictionary_table）
- 插入默认用户数据
- 创建必要的索引以提高查询性能
- 设置 UTF-8MB4 字符集以支持中文

### 4. 启动服务

推荐使用启动脚本自动完成所有部署步骤：

```bash
# 启动所有服务（推荐）
./scripts/start.sh

# 或者手动启动

# 启动后端服务
# 确保在 backend 目录中
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端服务
# 在 frontend 目录中
npm run dev
```

### 5. 验证部署

部署成功后，验证以下内容：

- **后端服务**：访问 `http://localhost:8000/docs` 查看 API 文档
- **前端界面**：访问 `http://localhost:3000` 查看应用界面
- **健康检查**：访问 `http://localhost:8000/health` 验证后端服务状态
- **数据库连接**：检查后端日志是否有数据库连接成功的记录

## 环境变量配置

后端服务使用 `.env` 文件管理环境变量。默认配置位于 `backend/.env`：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=chatbi
DB_POOL_SIZE=5

# 模型配置
MODEL_TYPE=local
QWEN_MODEL_NAME=qwen-agent

# 应用配置
LOG_LEVEL=INFO
DEBUG=false
```

**关键配置项说明**：

- `DB_HOST`: 数据库主机地址
- `DB_PORT`: 数据库端口
- `DB_USER`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `DB_NAME`: 数据库名称
- `DB_POOL_SIZE`: 数据库连接池大小（默认5）
- `MODEL_TYPE`: 模型类型（local 或 remote）
- `QWEN_MODEL_NAME`: Qwen 模型名称
- `LOG_LEVEL`: 日志级别（DEBUG, INFO, WARNING, ERROR）
- `DEBUG`: 是否启用调试模式

## 故障排查指南

### 1. 启动失败：虚拟环境未创建

**症状**：启动脚本提示 "虚拟环境不存在"

**解决方案**：
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. 端口占用错误

**症状**：启动脚本提示端口 8000 或 3000 被占用

**解决方案**：
- 启动脚本会自动尝试终止占用进程
- 如果自动终止失败，请手动查找并终止进程：
```bash
# 查找占用 8000 端口的进程
lsof -i :8000

# 终止进程（替换 PID）
kill -9 PID
```

### 3. 数据库连接失败

**症状**：启动脚本提示无法连接数据库

**解决方案**：
- 确保 MySQL 服务正在运行：`brew services start mysql`
- 确保数据库已初始化：`mysql -u root < database/init.sql`
- 检查数据库连接配置：`backend/.env` 文件中的数据库参数
- 验证数据库是否存在：`mysql -u root -e "SHOW DATABASES;"`

### 4. 前端依赖缺失

**症状**：前端无法启动，提示 node_modules 不存在

**解决方案**：
```bash
cd frontend
npm install
```

### 5. 后端依赖缺失

**症状**：后端启动失败，提示缺少 Python 包

**解决方案**：
```bash
cd backend
pip install -e .
```

### 6. 日志文件查看

ChatBI 提供多层次的日志系统：

**后端日志**:
```bash
# 详细后端日志（推荐）
tail -f backend/backend/backend.log

# 启动脚本输出
tail -f backend.log
```

**前端日志**:
```bash
# 启动脚本输出
tail -f frontend.log

# 浏览器控制台（F12 > Console）
# localStorage 日志（F12 > Application > Local Storage）
```

**日志级别配置**:
在 `backend/.env` 中设置：
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### 7. 健康检查失败

**症状**：访问 `http://localhost:8000/health` 返回错误

**解决方案**：
- 检查后端日志中的错误信息
- 验证数据库连接是否正常
- 检查是否所有必需的依赖都已安装
- 重启后端服务

## 性能优化建议

### 1. 数据库优化

- **索引优化**：确保 `query_history`、`query_sessions` 和 `data_dictionary` 表上有适当的索引
- **连接池**：根据并发用户数调整 `DB_POOL_SIZE` 参数（建议 5-20）
- **查询缓存**：在 `cache_service.py` 中启用 Redis 缓存（如需）

### 2. 后端优化

- **Uvicorn 配置**：在生产环境中使用 `--workers` 参数启用多进程：
  ```bash
  uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- **日志级别**：生产环境建议使用 `INFO` 级别，避免过多调试日志
- **依赖管理**：定期更新依赖以获得安全补丁和性能改进

### 3. 前端优化

- **构建优化**：生产环境使用 `npm run build` 构建优化后的静态文件
- **图片优化**：使用 WebP 格式图片以减少加载时间
- **代码分割**：利用 Vue Router 的懒加载功能减少初始加载包大小

### 4. 系统资源管理

- **内存监控**：监控 Python 和 Node.js 进程的内存使用情况
- **CPU 使用率**：确保 Qwen 模型推理不会导致 CPU 过载
- **磁盘空间**：定期清理日志文件，避免占用过多磁盘空间

## Docker 部署（可选）

未来版本将提供 Docker Compose 配置，简化部署流程：

```yaml
# docker-compose.yml
version: '3.8'

services:
  chatbi-backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_USER=root
      - DB_PASSWORD=secret
      - DB_NAME=chatbi
    depends_on:
      - mysql

  chatbi-frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - chatbi-backend

  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: secret
    volumes:
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
```

## 联系我们

如有任何部署问题，请联系项目团队。