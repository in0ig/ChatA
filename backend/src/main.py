from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import sys

# 加载环境变量
load_dotenv()

# 导入日志配置
from src.utils import logger

# 确保日志模块正确加载
try:
    from src.utils import logger
except ImportError as e:
    print(f"Error importing logger: {e}", file=sys.stderr)
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 导入所有模型以确保它们被正确注册到Base.metadata
# 必须在导入路由之前执行，以确保SQLAlchemy能正确解析所有关系
from src.models import Base
from src.models.data_source_model import DataSource
from src.models.data_preparation_model import DataTable, TableField, Dictionary, DictionaryItem, DynamicDictionaryConfig, TableRelation
from src.models.knowledge_base_model import KnowledgeBase
from src.models.knowledge_item_model import KnowledgeItem
from src.models.database_models import PromptConfig, SessionContext, ConversationMessage, TokenUsageStats

# 导入数据库配置
from src.database import get_db
from src.database_engine import engine

# 创建应用实例
app = FastAPI(title="ChatBI Backend", description="Natural Language Query System")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from src.api.data_source_api import router as data_source_router
from src.api.datasources_api import router as datasources_router  # ChatBI 兼容路由
from src.api.query_api import router as query_router
from src.api.settings_api import router as settings_router
# from src.api.session_api import router as session_router  # 暂时禁用，需要修复database_service依赖
from src.api.history_api import router as history_router
from src.api.prompt_api import router as prompt_router
from src.api.context_api import router as context_router
from src.api.multi_turn_api import router as multi_turn_router
# from src.api.sql_error_recovery_api import router as sql_error_recovery_router  # 暂时禁用，需要修复database_service依赖
from src.api.knowledge_base import router as knowledge_base_router
from src.api.knowledge_item import router as knowledge_item_router
from src.api.data_table_api import router as data_table_router
from src.api.table_field import router as table_field_router
from src.api.excel_upload import router as excel_upload_router
from src.api.excel_parser_api import router as excel_parser_router
from src.api.excel_importer_api import router as excel_importer_router
from src.api.table_relation import router as table_relation_router
from src.api.dictionary import router as dictionary_router
from src.api.dynamic_dictionary import router as dynamic_dictionary_router
from src.api.dictionary_version import router as dictionary_version_router
from src.api.table_folder import router as table_folder_router
from src.api.field_mapping import router as field_mapping_router

# 注意：很多路由器已经在定义时包含了前缀，不需要重复添加
app.include_router(data_source_router)  # 已包含 /api/data-sources 前缀
app.include_router(datasources_router)  # 已包含 /api/datasources 前缀 (ChatBI 兼容路由)
app.include_router(query_router, prefix="/api/query")
app.include_router(settings_router, prefix="/api/settings")
# app.include_router(session_router, prefix="/api/sessions")  # 暂时禁用
app.include_router(history_router, prefix="/api/query")
app.include_router(prompt_router, prefix="/api/prompts")
app.include_router(context_router, prefix="/api")
app.include_router(multi_turn_router, prefix="/api/sessions")
# app.include_router(sql_error_recovery_router, prefix="/api")  # 暂时禁用
app.include_router(knowledge_base_router, prefix="/api/knowledge-bases")
app.include_router(knowledge_item_router, prefix="/api/knowledge-items")
app.include_router(data_table_router, prefix="/api/data-tables")
app.include_router(table_field_router)  # 已包含 /api 前缀
app.include_router(excel_upload_router)  # 已包含 /api/data-sources 前缀
app.include_router(excel_parser_router)  # 已包含 /api/excel 前缀
app.include_router(excel_importer_router)  # 已包含 /api/data-tables 前缀
app.include_router(table_relation_router)  # 已包含 /api/table-relations 前缀
app.include_router(dictionary_router)  # 已包含 /api/dictionaries 前缀
app.include_router(dynamic_dictionary_router)  # 已包含 /api/dynamic-dictionaries 前缀
app.include_router(dictionary_version_router, prefix="/api/dictionary-version")
app.include_router(table_folder_router)  # 已包含 /api/table-folders 前缀
app.include_router(field_mapping_router)  # 已包含 /api/field-mappings 前缀

# 添加调试信息：打印所有注册的路由
@app.on_event("startup")
def log_routes():
    """
    在应用启动时打印所有注册的路由，用于调试
    同时验证 API 路径的正确性
    """
    logger.info("Registered routes:")
    api_routes = []
    
    for route in app.routes:
        logger.info(f"{route.methods} {route.path}")
        
        # 收集 API 路径进行验证
        if hasattr(route, 'path') and '/api/' in route.path:
            api_routes.append(route.path)
    
    # 验证 API 路径格式
    logger.info("Validating API path formats...")
    for path in api_routes:
        # 检查重复前缀
        path_segments = path.split('/')
        if path_segments.count('api') > 1:
            logger.warning(f"⚠️  Duplicate 'api' prefix detected in path: {path}")
        
        # 检查资源命名（应该使用复数形式）
        if len(path_segments) >= 3:
            resource_segment = path_segments[2]
            # 检查知识库和知识项资源是否使用复数形式
            if resource_segment in ['knowledge-base', 'knowledge-item']:
                logger.warning(f"⚠️  Resource should be plural: {resource_segment} in {path}")
            elif resource_segment in ['knowledge-bases', 'knowledge-items']:
                logger.info(f"✅ Correct plural resource naming: {resource_segment}")
        
        # 检查路径格式（kebab-case）
        for segment in path_segments:
            if segment and '_' in segment:
                logger.warning(f"⚠️  Path segment should use kebab-case instead of snake_case: {segment} in {path}")
    
    logger.info(f"API path validation completed. Total API routes: {len(api_routes)}")

# 导入数据准备模块的文档配置
from src.api.docs import create_data_prep_openapi_schema

# 在app实例创建后立即设置依赖注入覆盖
# 根据路由
@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "ChatBI Backend is running"}

# 自定义 OpenAPI 文档
@app.on_event("startup")
def setup_openapi():
    """
    在应用启动时设置自定义 OpenAPI 文档
    """
    create_data_prep_openapi_schema(app)
    logger.info("Custom OpenAPI schema for data preparation module has been configured")

@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

# 数据库健康检查端点
@app.get("/health/db")
def database_health_check():
    """
    检查数据库连接状态
    返回详细的数据库健康信息
    """
    logger.info("Database health check endpoint accessed")
    try:
        # 使用SQLAlchemy引擎测试连接
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return {"status": "healthy", "database": "MySQL"}
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

# 创建一个独立的函数来处理应用启动时的初始化
async def startup_event_handler():
    """
    应用启动时的初始化处理
    创建所有表并注册路由
    """
    logger.info("Initializing database connection on startup...")
    
    # 在测试模式下不创建表，由测试代码负责表创建
    if os.getenv("TEST_MODE", "false").lower() != "true":
        # 生产模式下创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    else:
        logger.info("TEST_MODE is enabled, skipping table creation (handled by test suite)")
    
    # 打印所有注册的路由
    logger.info("Registered routes:")
    for route in app.routes:
        logger.info(f"{route.methods} {route.path}")

# 应用启动时初始化数据库连接
@app.on_event("startup")
async def startup_event():
    """
    应用启动时初始化数据库连接
    创建所有表
    """
    await startup_event_handler()

# 应用关闭时清理数据库连接
@app.on_event("shutdown")
def shutdown_event():
    """
    应用关闭时清理数据库连接
    """
    logger.info("Closing database connection on shutdown...")
    engine.dispose()

if __name__ == "__main__":
    # 获取模型配置
    model_type = os.getenv('MODEL_TYPE', 'local').lower()
    model_name = os.getenv('QWEN_MODEL_NAME', 'qwen-agent')
    
    # 记录启动配置
    logger.info(f"Starting ChatBI Backend server with MODEL_TYPE='{model_type}', QWEN_MODEL_NAME='{model_name}'")
    
    # 使用更健壮的启动配置
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        workers=1,
        timeout_keep_alive=30
    )