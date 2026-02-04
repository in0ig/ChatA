#!/usr/bin/env python3
"""
测试依赖覆盖是否工作的简单脚本
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 创建测试数据库 - 使用共享缓存的内存数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:?cache=shared"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        print(f"override_get_db called! Database engine: {db.bind}")
        yield db
    finally:
        db.close()

# 导入app并设置依赖覆盖
from src.main import app
from src.database import get_db
from src.models.base import Base

print("Before override:")
print(f"get_db function: {get_db}")
print(f"app.dependency_overrides: {app.dependency_overrides}")

app.dependency_overrides[get_db] = override_get_db

print("\nAfter override:")
print(f"app.dependency_overrides: {app.dependency_overrides}")

# 创建所有表
print("\nCreating tables...")
Base.metadata.create_all(bind=engine)

# 验证表是否创建成功
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
    tables = result.fetchall()
    print(f"Tables in test database: {[table[0] for table in tables]}")

print("Tables created successfully!")

# 创建测试客户端
client = TestClient(app)

# 测试API调用
print("\nTesting API call...")
response = client.get("/api/data-tables")
print(f"Response status: {response.status_code}")
if response.status_code == 200:
    print("Success! Dependency override is working!")
    data = response.json()
    print(f"Response data: {data}")
else:
    print(f"Response content: {response.text}")