from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import uuid
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.services.sql_error_recovery_service import SQLErrorRecoveryService
from src.services.database_service import database_service

# 创建API路由器
router = APIRouter(prefix="/api/sql-error-recovery", tags=["sql-error-recovery"])

# 初始化服务
sql_error_recovery_service = SQLErrorRecoveryService()

# 请求模型
class ExecuteRequest(BaseModel):
    session_id: str
    user_question: str
    sql: str
    data_source_id: str

class HistoryResponse(BaseModel):
    sql: str
    generated_sql: str
    chart_type: str
    result_data: Dict[str, Any]
    created_at: str

@router.post("/execute")
async def execute_with_retry(request: ExecuteRequest) -> Dict[str, Any]:
    """
    执行SQL并处理错误（支持自动重试）
    
    Args:
        session_id: 会话ID
        user_question: 用户原始问题
        sql: 要执行的SQL语句
        data_source_id: 数据源ID
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    try:
        # 验证必需参数
        if not request.session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        if not request.user_question:
            raise HTTPException(status_code=400, detail="user_question is required")
        if not request.sql:
            raise HTTPException(status_code=400, detail="sql is required")
        if not request.data_source_id:
            raise HTTPException(status_code=400, detail="data_source_id is required")
        
        # 调用服务执行SQL
        result = sql_error_recovery_service.execute_with_retry(
            session_id=request.session_id,
            user_question=request.user_question,
            sql=request.sql,
            data_source_id=request.data_source_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute SQL with retry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/history")
async def get_retry_history(session_id: str) -> List[HistoryResponse]:
    """
    获取指定会话的重试历史
    
    Args:
        session_id: 会话ID
        
    Returns:
        List[HistoryResponse]: 重试历史列表
    """
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # 调用服务获取重试历史
        history = sql_error_recovery_service.get_retry_history(session_id)
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to get retry history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 导出路由器
__all__ = ["router"]
