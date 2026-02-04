from fastapi import APIRouter, HTTPException, Path, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel
from src.services.context_manager import context_manager
from src.models.database_models import ContextType, ModelType
from src.utils import get_db_session as get_db

# 创建API路由器
router = APIRouter(tags=["Session Context"])

# 请求模型
class ContextRequest(BaseModel):
    context_type: ContextType
    messages: Optional[List[Dict]] = None

class SummaryResponse(BaseModel):
    summary: str

class MessageResponse(BaseModel):
    messages: List[Dict]

class TokenUsageResponse(BaseModel):
    session_id: str
    total_turns: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    model_usage: Dict

# GET /api/sessions/{id}/context - 获取会话上下文
@router.get("/sessions/{session_id}/context", response_model=Dict)
def get_session_context(
    session_id: str = Path(..., description="会话ID"),
    context_type: ContextType = ContextType.local_model
):
    """
    获取指定会话和上下文类型的上下文信息
    
    Args:
        session_id: 会话ID
        context_type: 上下文类型 (local_model 或 aliyun_model)
        
    Returns:
        包含messages、token_count、summary的字典
    """
    try:
        context = context_manager.get_session_context(session_id, context_type)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session context: {str(e)}")

# POST /api/sessions/{id}/context/summarize - 总结会话上下文
@router.post("/sessions/{session_id}/context/summarize", response_model=SummaryResponse)
def summarize_session_context(
    session_id: str = Path(..., description="会话ID"),
    request: ContextRequest = None
):
    """
    总结指定会话的上下文
    
    Args:
        session_id: 会话ID
        context_type: 上下文类型
        messages: 消息列表（如果未提供，则从数据库获取）
        
    Returns:
        总结文本
    """
    try:
        # 如果没有提供messages，则从数据库获取
        if not request or not request.messages:
            messages = context_manager.get_session_messages(session_id, limit=100)
        else:
            messages = request.messages
        
        if not messages:
            raise HTTPException(status_code=404, detail="No messages found for summarization")
        
        summary = context_manager.summarize_context(session_id, request.context_type, messages)
        
        return SummaryResponse(summary=summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize context: {str(e)}")

# GET /api/sessions/{id}/messages - 获取会话消息
@router.get("/sessions/{session_id}/messages", response_model=MessageResponse)
def get_session_messages(
    session_id: str = Path(..., description="会话ID"),
    limit: int = 100
):
    """
    获取指定会话的消息列表
    
    Args:
        session_id: 会话ID
        limit: 最大消息数量，默认100
        
    Returns:
        消息列表
    """
    try:
        messages = context_manager.get_session_messages(session_id, limit)
        return MessageResponse(messages=messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session messages: {str(e)}")

# GET /api/sessions/{id}/token-usage - 获取Token使用统计
@router.get("/sessions/{session_id}/token-usage", response_model=TokenUsageResponse)
def get_token_usage(
    session_id: str = Path(..., description="会话ID")
):
    """
    获取指定会话的token使用统计
    
    Args:
        session_id: 会话ID
        
    Returns:
        token使用统计信息
    """
    try:
        token_usage = context_manager.get_token_usage(session_id)
        return TokenUsageResponse(**token_usage)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get token usage: {str(e)}")