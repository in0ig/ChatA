import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import tiktoken
import requests
import json

from src.models.database_models import SessionContext, ConversationMessage, TokenUsageStats, ContextType, ModelType
from src.utils import get_db_session as get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextManager:
    """
    管理会话上下文的类，提供获取、总结和计算token的功能
    """
    
    def __init__(self):
        # 初始化tiktoken编码器
        try:
            self.local_encoder = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Failed to initialize tiktoken encoder: {str(e)}")
            self.local_encoder = None
    
    def get_session_context(self, session_id: str, context_type: ContextType) -> Optional[Dict]:
        """
        获取指定会话和上下文类型的上下文信息
        
        Args:
            session_id: 会话ID
            context_type: 上下文类型 (local_model 或 aliyun_model)
            
        Returns:
            包含messages、token_count、summary的字典，如果不存在则返回None
        """
        try:
            db: Session = next(get_db())
            context = db.query(SessionContext).filter(
                SessionContext.session_id == session_id,
                SessionContext.context_type == context_type
            ).first()
            
            if not context:
                logger.info(f"No context found for session {session_id} with type {context_type}")
                return None
            
            return {
                "messages": context.messages,
                "token_count": context.token_count,
                "summary": context.summary,
                "last_summary_at": context.last_summary_at
            }
            
        except Exception as e:
            logger.error(f"Error getting session context for {session_id}: {str(e)}")
            raise
    
    def get_session_messages(self, session_id: str, limit: int = 100) -> List[Dict]:
        """
        获取指定会话的消息列表
        
        Args:
            session_id: 会话ID
            limit: 最大消息数量，默认100
            
        Returns:
            消息列表，每个消息包含role、content、token_count等信息
        """
        try:
            db: Session = next(get_db())
            messages = db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session_id
            ).order_by(ConversationMessage.turn.asc()).limit(limit).all()
            
            return [
                {
                    "id": msg.id,
                    "turn": msg.turn,
                    "role": msg.role.value,
                    "content": msg.content,
                    "token_count": msg.token_count,
                    "model_used": msg.model_used.value if msg.model_used else "none",
                    "intent": msg.intent,
                    "query_id": msg.query_id,
                    "analysis_id": msg.analysis_id,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
            
        except Exception as e:
            logger.error(f"Error getting session messages for {session_id}: {str(e)}")
            raise
    
    def get_token_usage(self, session_id: str) -> Dict:
        """
        获取指定会话的token使用统计
        
        Args:
            session_id: 会话ID
            
        Returns:
            包含模型类型、输入/输出/总token数的统计信息
        """
        try:
            db: Session = next(get_db())
            token_stats = db.query(TokenUsageStats).filter(
                TokenUsageStats.session_id == session_id
            ).order_by(TokenUsageStats.turn.asc()).all()
            
            if not token_stats:
                return {
                    "session_id": session_id,
                    "total_turns": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_tokens": 0,
                    "model_usage": {}
                }
            
            # 按模型类型汇总
            model_usage = {}
            total_input = 0
            total_output = 0
            total_tokens = 0
            
            for stat in token_stats:
                model_type = stat.model_type.value
                if model_type not in model_usage:
                    model_usage[model_type] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "turns": 0
                    }
                
                model_usage[model_type]["input_tokens"] += stat.input_tokens
                model_usage[model_type]["output_tokens"] += stat.output_tokens
                model_usage[model_type]["total_tokens"] += stat.total_tokens
                model_usage[model_type]["turns"] += 1
                
                total_input += stat.input_tokens
                total_output += stat.output_tokens
                total_tokens += stat.total_tokens
            
            return {
                "session_id": session_id,
                "total_turns": len(token_stats),
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_tokens,
                "model_usage": model_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting token usage for {session_id}: {str(e)}")
            raise
    
    def summarize_context(self, session_id: str, context_type: ContextType, messages: List[Dict]) -> str:
        """
        总结会话上下文
        
        Args:
            session_id: 会话ID
            context_type: 上下文类型
            messages: 消息列表，包含role和content
            
        Returns:
            总结文本
        """
        try:
            # 构建用于总结的文本
            summary_text = ""
            for msg in messages:
                if msg.get("role") == "user":
                    summary_text += f"用户: {msg.get('content', '')}\n"
                elif msg.get("role") == "assistant":
                    summary_text += f"助手: {msg.get('content', '')}\n"
            
            # 简单的摘要实现：提取关键信息
            # 在实际应用中，这里应该调用大模型进行智能摘要
            # 这里使用一个简单的规则为基础
            
            if not summary_text.strip():
                return ""
            
            # 提取对话轮数
            user_messages = sum(1 for msg in messages if msg.get("role") == "user")
            assistant_messages = sum(1 for msg in messages if msg.get("role") == "assistant")
            
            # 提取主题关键词（简单实现）
            keywords = []
            for msg in messages:
                content = msg.get("content", "")
                if "数据" in content or "统计" in content or "分析" in content:
                    keywords.append("数据分析")
                elif "图表" in content or "可视化" in content:
                    keywords.append("图表可视化")
                elif "上月" in content or "本周" in content or "去年" in content:
                    keywords.append("时间范围")
            
            # 生成摘要
            summary = f"会话包含{user_messages}条用户查询和{assistant_messages}条助手回复。"
            if keywords:
                summary += f" 主题包括：{', '.join(set(keywords))}。"
            
            # 保存到数据库
            db: Session = next(get_db())
            context = db.query(SessionContext).filter(
                SessionContext.session_id == session_id,
                SessionContext.context_type == context_type
            ).first()
            
            if not context:
                context = SessionContext(
                    session_id=session_id,
                    context_type=context_type,
                    messages=messages,
                    token_count=self.calculate_token_count(summary_text, ModelType.local),
                    summary=summary,
                    last_summary_at=datetime.now()
                )
                db.add(context)
            else:
                context.messages = messages
                context.token_count = self.calculate_token_count(summary_text, ModelType.local)
                context.summary = summary
                context.last_summary_at = datetime.now()
                
            db.commit()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing context for {session_id}: {str(e)}")
            raise
    
    def calculate_token_count(self, text: str, model_type: ModelType) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 要计算的文本
            model_type: 模型类型 (local 或 aliyun)
            
        Returns:
            token数量
        """
        try:
            if not text:
                return 0
            
            if model_type == ModelType.local:
                if self.local_encoder is None:
                    # Fallback: estimate based on characters
                    return len(text) // 4
                return len(self.local_encoder.encode(text))
            
            elif model_type == ModelType.aliyun:
                # 阿里云模型token计数API调用
                # 这里需要根据实际的阿里云API实现
                # 由于没有实际API，使用一个估算值
                # 实际实现中应该调用阿里云的token计数服务
                return len(text) // 3  # 估算值
            
            else:
                return len(text) // 4
                
        except Exception as e:
            logger.error(f"Error calculating token count for text: {str(e)}")
            # Fallback: estimate based on characters
            return len(text) // 4
        
    def update_token_usage(self, session_id: str, model_type: ModelType, turn: int, input_tokens: int, output_tokens: int):
        """
        更新token使用统计
        
        Args:
            session_id: 会话ID
            model_type: 模型类型
            turn: 对话轮次
            input_tokens: 输入token数量
            output_tokens: 输出token数量
        """
        try:
            db: Session = next(get_db())
            
            # 创建新的token使用记录
            token_stat = TokenUsageStats(
                session_id=session_id,
                model_type=model_type,
                turn=turn,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens
            )
            
            db.add(token_stat)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating token usage for {session_id}: {str(e)}")
            raise

# 创建全局实例
context_manager = ContextManager()