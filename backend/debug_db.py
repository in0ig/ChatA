#!/usr/bin/env python3
"""
调试数据库连接问题
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.models.base import Base
from src.models.data_preparation_model import DataTable, TableField
from src.models.data_source_model import DataSource

# 使用SQLite内存数据库进行测试，使用StaticPool确保连接共享
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True  # 启用SQL日志
)

print("创建数据库引擎...")
print(f"引擎: {engine}")

# 创建所有表
print("创建所有表...")
Base.metadata.create_all(bind=engine)

# 验证表是否被创建
print("验证表是否被创建...")
with engine.connect() as connection:
    result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = result.fetchall()
    print(f"数据库中的表: {[table[0] for table in tables]}")

# 创建会话并测试查询
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("测试查询...")
try:
    count = db.query(DataTable).count()
    print(f"DataTable 表中的记录数: {count}")
except Exception as e:
    print(f"查询失败: {e}")

db.close()