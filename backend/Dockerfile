# ChatBI 后端服务 Dockerfile
# 多阶段构建以优化镜像大小

# ==================== 构建阶段 ====================
# 使用官方 Python 3.12 镜像作为构建基础
FROM python:3.12-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖（用于编译Python包）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmysqlclient-dev \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml uv.lock /app/

# 使用 uv 安装依赖（比 pip 更快更轻量）
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev

# 复制源代码
COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY .env.example /app/.env.example

# ==================== 最终镜像阶段 ====================
# 使用更小的 Python 镜像作为最终基础
FROM python:3.12-slim

# 创建非root用户
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# 设置工作目录
WORKDIR /app

# 复制构建阶段的依赖
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# 复制源代码
COPY --from=builder /app/src /app/src
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/.env.example /app/.env.example

# 创建日志和上传目录
RUN mkdir -p /var/log/chatbi /var/www/chatbi/uploads && \
    chown -R appuser:appuser /var/log/chatbi /var/www/chatbi/uploads

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 复制启动脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 启动命令
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==================== 优化建议 ====================
# 1. 生产环境部署时，移除 --reload 参数
# 2. 可以使用 gunicorn 替代 uvicorn 以获得更好的性能
# 3. 考虑使用多进程模式以充分利用多核CPU
# 4. 生产环境建议使用 nginx 作为反向代理
# 5. 使用健康检查端点监控服务状态
