"""
对话流程编排引擎 - 左右互搏核心
实现"云端生成SQL → 本地执行 → 本地分析"的完整流水线
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from src.services.context_manager import ContextManager
from src.services.ai_model_service import AIModelService
from src.services.semantic_context_aggregator import SemanticContextAggregator
from src.services.websocket_stream_service import get_websocket_stream_service, StreamMessageType
from src.services.sql_security_validator import SQLSecurityService
from src.database import get_db
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class ChatStage(Enum):
    """对话阶段枚举"""
    INTENT_RECOGNITION = "intent_recognition"  # 意图识别
    TABLE_SELECTION = "table_selection"        # 智能选表
    INTENT_CLARIFICATION = "intent_clarification"  # 意图澄清
    SQL_GENERATION = "sql_generation"          # SQL生成
    SQL_EXECUTION = "sql_execution"            # SQL执行
    DATA_ANALYSIS = "data_analysis"            # 数据分析
    RESULT_PRESENTATION = "result_presentation"  # 结果展示
    ERROR_HANDLING = "error_handling"          # 错误处理
    COMPLETED = "completed"                    # 完成


class ChatIntent(Enum):
    """对话意图枚举"""
    SMART_QUERY = "smart_query"      # 智能问数
    REPORT_GENERATION = "report_generation"  # 生成报告
    DATA_FOLLOWUP = "data_followup"  # 数据追问
    CLARIFICATION = "clarification"  # 澄清确认
    UNKNOWN = "unknown"              # 未知意图


class ChatContext:
    """对话上下文"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_stage = ChatStage.INTENT_RECOGNITION
        self.intent = ChatIntent.UNKNOWN
        self.selected_tables: List[str] = []
        self.generated_sql: Optional[str] = None
        self.query_result: Optional[Dict[str, Any]] = None
        self.previous_data: List[Dict[str, Any]] = []
        self.error_count = 0
        self.retry_count = 0
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_stage(self, stage: ChatStage):
        """更新对话阶段"""
        self.current_stage = stage
        self.updated_at = datetime.now()
        logger.info(f"会话 {self.session_id} 进入阶段: {stage.value}")
    
    def add_error(self, error: str):
        """添加错误记录"""
        self.error_count += 1
        if 'errors' not in self.metadata:
            self.metadata['errors'] = []
        self.metadata['errors'].append({
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'stage': self.current_stage.value
        })
    
    def add_previous_data(self, data: Dict[str, Any]):
        """添加历史数据用于对比分析"""
        self.previous_data.append({
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'sql': self.generated_sql
        })
        # 保持最近5次查询结果
        if len(self.previous_data) > 5:
            self.previous_data = self.previous_data[-5:]


class ChatOrchestrator:
    """对话流程编排引擎"""
    
    def __init__(self):
        self.context_manager = ContextManager()
        # 使用默认配置初始化AI服务，在测试中会被mock
        default_config = {
            "qwen_cloud": {"api_key": "test", "base_url": "test"},
            "openai_local": {"api_key": "test", "base_url": "test"}
        }
        self.ai_service = AIModelService(default_config)
        self.semantic_aggregator = SemanticContextAggregator()
        self.websocket_service = get_websocket_stream_service()
        self.sql_security = SQLSecurityService()
        self.active_contexts: Dict[str, ChatContext] = {}
        self.max_retry_count = 3
        self.max_error_count = 5
    
    async def start_chat(self, session_id: str, user_question: str, data_source_id: Optional[int] = None) -> Dict[str, Any]:
        """
        开始对话流程
        
        Args:
            session_id: 会话ID
            user_question: 用户问题
            data_source_id: 数据源ID（可选）
            
        Returns:
            对话结果
        """
        try:
            # 创建或获取对话上下文
            context = self.get_or_create_context(session_id)
            
            # 发送开始消息
            await self.websocket_service.send_status_message(
                session_id, "开始处理您的问题...", 0.1
            )
            
            # 执行完整对话流程
            result = await self._execute_chat_pipeline(context, user_question, data_source_id)
            
            return result
            
        except Exception as e:
            logger.error(f"对话流程执行失败: {str(e)}")
            await self.websocket_service.send_error_message(
                session_id, f"对话处理失败: {str(e)}", "CHAT_ORCHESTRATOR_ERROR"
            )
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def continue_chat(self, session_id: str, user_response: str) -> Dict[str, Any]:
        """
        继续对话（处理用户回复）
        
        Args:
            session_id: 会话ID
            user_response: 用户回复
            
        Returns:
            对话结果
        """
        try:
            context = self.active_contexts.get(session_id)
            if not context:
                return {
                    "success": False,
                    "error": "会话不存在或已过期",
                    "session_id": session_id
                }
            
            # 根据当前阶段处理用户回复
            if context.current_stage == ChatStage.INTENT_CLARIFICATION:
                return await self._handle_clarification_response(context, user_response)
            elif context.current_stage == ChatStage.ERROR_HANDLING:
                return await self._handle_error_recovery(context, user_response)
            else:
                # 作为新的追问处理
                return await self._handle_followup_question(context, user_response)
                
        except Exception as e:
            logger.error(f"继续对话失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def get_or_create_context(self, session_id: str) -> ChatContext:
        """获取或创建对话上下文"""
        if session_id not in self.active_contexts:
            self.active_contexts[session_id] = ChatContext(session_id)
        return self.active_contexts[session_id]
    
    async def _execute_chat_pipeline(self, context: ChatContext, user_question: str, data_source_id: Optional[int]) -> Dict[str, Any]:
        """执行完整对话流水线"""
        
        try:
            # 阶段1: 意图识别
            context.update_stage(ChatStage.INTENT_RECOGNITION)
            await self.websocket_service.send_thinking_message(
                context.session_id, "正在识别您的问题意图...", {"stage": "intent_recognition", "progress": 0.2}
            )
            
            intent_result = await self._recognize_intent(context, user_question)
            if not intent_result["success"]:
                return await self._handle_pipeline_error(context, "意图识别失败", intent_result.get("error"))
            
            context.intent = ChatIntent(intent_result["intent"])
            
            # 阶段2: 智能选表
            context.update_stage(ChatStage.TABLE_SELECTION)
            await self.websocket_service.send_thinking_message(
                context.session_id, "正在分析相关数据表...", {"stage": "table_selection", "progress": 0.4}
            )
            
            table_result = await self._select_tables(context, user_question, data_source_id)
            if not table_result["success"]:
                return await self._handle_pipeline_error(context, "智能选表失败", table_result.get("error"))
            
            context.selected_tables = table_result["tables"]
            
            # 阶段3: 意图澄清（如果需要）
            if table_result.get("needs_clarification", False):
                return await self._request_clarification(context, table_result["clarification_question"])
            
            # 阶段4: SQL生成
            context.update_stage(ChatStage.SQL_GENERATION)
            await self.websocket_service.send_thinking_message(
                context.session_id, "正在生成SQL查询...", {"stage": "sql_generation", "progress": 0.6}
            )
            
            sql_result = await self._generate_sql(context, user_question, data_source_id)
            if not sql_result["success"]:
                return await self._handle_pipeline_error(context, "SQL生成失败", sql_result.get("error"))
            
            context.generated_sql = sql_result["sql"]
            
            # 阶段5: SQL执行
            context.update_stage(ChatStage.SQL_EXECUTION)
            await self.websocket_service.send_thinking_message(
                context.session_id, "正在执行查询...", {"stage": "sql_execution", "progress": 0.8}
            )
            
            execution_result = await self._execute_sql(context, data_source_id)
            if not execution_result["success"]:
                return await self._handle_pipeline_error(context, "SQL执行失败", execution_result.get("error"))
            
            context.query_result = execution_result["result"]
            
            # 阶段6: 数据分析（本地模型）
            context.update_stage(ChatStage.DATA_ANALYSIS)
            await self.websocket_service.send_thinking_message(
                context.session_id, "正在分析查询结果...", {"stage": "data_analysis", "progress": 0.9}
            )
            
            analysis_result = await self._analyze_data(context, user_question)
            if not analysis_result["success"]:
                return await self._handle_pipeline_error(context, "数据分析失败", analysis_result.get("error"))
            
            # 阶段7: 结果展示
            context.update_stage(ChatStage.RESULT_PRESENTATION)
            await self._present_results(context, analysis_result)
            
            # 保存历史数据
            context.add_previous_data(context.query_result)
            
            context.update_stage(ChatStage.COMPLETED)
            
            return {
                "success": True,
                "session_id": context.session_id,
                "intent": context.intent.value,
                "tables": context.selected_tables,
                "sql": context.generated_sql,
                "result": context.query_result,
                "analysis": analysis_result["analysis"],
                "stage": context.current_stage.value
            }
            
        except Exception as e:
            logger.error(f"对话流水线执行失败: {str(e)}")
            return await self._handle_pipeline_error(context, "流水线执行失败", str(e))
    
    async def _recognize_intent(self, context: ChatContext, user_question: str) -> Dict[str, Any]:
        """意图识别"""
        try:
            # 构建意图识别的prompt
            prompt = f"""
            请分析用户问题的意图类型：
            
            用户问题: {user_question}
            
            意图类型:
            1. smart_query - 智能问数（查询具体数据）
            2. report_generation - 生成报告（生成分析报告）
            3. data_followup - 数据追问（对已有结果追问）
            4. clarification - 澄清确认（需要更多信息）
            
            请返回JSON格式: {{"intent": "意图类型", "confidence": 0.95, "reason": "判断理由"}}
            """
            
            # 调用云端模型进行意图识别
            response = await self.ai_service.call_cloud_model(
                prompt, 
                session_id=context.session_id,
                model_type="qwen"
            )
            
            if response["success"]:
                try:
                    result = json.loads(response["content"])
                    return {
                        "success": True,
                        "intent": result["intent"],
                        "confidence": result.get("confidence", 0.8),
                        "reason": result.get("reason", "")
                    }
                except json.JSONDecodeError:
                    # 如果JSON解析失败，使用简单规则
                    return self._fallback_intent_recognition(user_question)
            else:
                return self._fallback_intent_recognition(user_question)
                
        except Exception as e:
            logger.error(f"意图识别失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _fallback_intent_recognition(self, user_question: str) -> Dict[str, Any]:
        """意图识别降级策略"""
        question_lower = user_question.lower()
        
        # 简单关键词匹配
        if any(word in question_lower for word in ["查询", "多少", "统计", "数量", "金额"]):
            return {"success": True, "intent": "smart_query", "confidence": 0.7}
        elif any(word in question_lower for word in ["报告", "分析", "总结", "汇总"]):
            return {"success": True, "intent": "report_generation", "confidence": 0.7}
        elif any(word in question_lower for word in ["为什么", "原因", "详细", "进一步"]):
            return {"success": True, "intent": "data_followup", "confidence": 0.7}
        else:
            return {"success": True, "intent": "smart_query", "confidence": 0.5}
    
    async def _select_tables(self, context: ChatContext, user_question: str, data_source_id: Optional[int]) -> Dict[str, Any]:
        """智能选表"""
        try:
            # 获取语义上下文
            semantic_context = await self.semantic_aggregator.aggregate_context(
                user_question=user_question,
                data_source_id=data_source_id,
                max_tokens=2000
            )
            
            if not semantic_context["success"]:
                return {
                    "success": False,
                    "error": "获取语义上下文失败"
                }
            
            # 构建选表prompt
            prompt = f"""
            基于用户问题和数据库信息，请选择相关的数据表：
            
            用户问题: {user_question}
            
            可用数据表信息:
            {semantic_context['context']['table_structure']}
            
            数据字典信息:
            {semantic_context['context'].get('dictionary', '')}
            
            请返回JSON格式:
            {{
                "tables": ["table1", "table2"],
                "reason": "选择理由",
                "needs_clarification": false,
                "clarification_question": ""
            }}
            """
            
            # 调用云端模型进行选表
            response = await self.ai_service.call_cloud_model(
                prompt,
                session_id=context.session_id,
                model_type="qwen"
            )
            
            if response["success"]:
                try:
                    result = json.loads(response["content"])
                    return {
                        "success": True,
                        "tables": result["tables"],
                        "reason": result.get("reason", ""),
                        "needs_clarification": result.get("needs_clarification", False),
                        "clarification_question": result.get("clarification_question", "")
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "选表结果解析失败"
                    }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "选表失败")
                }
                
        except Exception as e:
            logger.error(f"智能选表失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_sql(self, context: ChatContext, user_question: str, data_source_id: Optional[int]) -> Dict[str, Any]:
        """生成SQL"""
        try:
            # 获取完整语义上下文
            semantic_context = await self.semantic_aggregator.aggregate_context(
                user_question=user_question,
                data_source_id=data_source_id,
                table_names=context.selected_tables,
                max_tokens=3000
            )
            
            if not semantic_context["success"]:
                return {
                    "success": False,
                    "error": "获取语义上下文失败"
                }
            
            # 构建SQL生成prompt
            prompt = f"""
            基于用户问题和数据库信息，请生成SQL查询：
            
            用户问题: {user_question}
            意图类型: {context.intent.value}
            选择的表: {', '.join(context.selected_tables)}
            
            数据库信息:
            {semantic_context['context']}
            
            请生成准确的SQL查询，只返回SQL语句，不要包含其他内容。
            """
            
            # 调用云端模型生成SQL
            response = await self.ai_service.call_cloud_model(
                prompt,
                session_id=context.session_id,
                model_type="qwen"
            )
            
            if response["success"]:
                sql = self._extract_sql_from_response(response["content"])
                
                # SQL安全验证
                validation_result = await self.sql_security.validate_sql_comprehensive(
                    sql, data_source_id or 1
                )
                
                if validation_result["is_safe"]:
                    return {
                        "success": True,
                        "sql": sql
                    }
                else:
                    return {
                        "success": False,
                        "error": f"SQL安全验证失败: {validation_result['message']}"
                    }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "SQL生成失败")
                }
                
        except Exception as e:
            logger.error(f"SQL生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_sql_from_response(self, response: str) -> str:
        """从AI响应中提取SQL"""
        import re
        
        # 尝试提取```sql```包围的SQL
        sql_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(sql_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 尝试提取```包围的内容
        code_pattern = r"```\s*(.*?)\s*```"
        match = re.search(code_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 如果没有代码块，返回整个响应
        return response.strip()
    
    async def _execute_sql(self, context: ChatContext, data_source_id: Optional[int]) -> Dict[str, Any]:
        """执行SQL"""
        try:
            # 这里应该调用数据源服务执行SQL
            # 暂时返回模拟结果
            mock_result = {
                "columns": ["id", "name", "amount"],
                "rows": [
                    [1, "产品A", 1000],
                    [2, "产品B", 2000],
                    [3, "产品C", 1500]
                ],
                "total_rows": 3,
                "execution_time": 0.05
            }
            
            return {
                "success": True,
                "result": mock_result
            }
            
        except Exception as e:
            logger.error(f"SQL执行失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_data(self, context: ChatContext, user_question: str) -> Dict[str, Any]:
        """数据分析（本地模型）"""
        try:
            # 构建数据分析prompt
            analysis_prompt = f"""
            请分析以下查询结果，回答用户问题：
            
            用户问题: {user_question}
            
            查询结果:
            列名: {context.query_result['columns']}
            数据行数: {context.query_result['total_rows']}
            数据内容: {context.query_result['rows'][:10]}  # 只显示前10行
            
            历史数据对比:
            {self._format_previous_data(context.previous_data)}
            
            请提供详细的数据分析和洞察。
            """
            
            # 调用本地模型进行分析
            response = await self.ai_service.call_local_model(
                analysis_prompt,
                session_id=context.session_id
            )
            
            if response["success"]:
                return {
                    "success": True,
                    "analysis": response["content"]
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "数据分析失败")
                }
                
        except Exception as e:
            logger.error(f"数据分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_previous_data(self, previous_data: List[Dict[str, Any]]) -> str:
        """格式化历史数据用于对比"""
        if not previous_data:
            return "无历史数据"
        
        formatted = []
        for i, data in enumerate(previous_data[-3:]):  # 最近3次
            formatted.append(f"历史查询{i+1}: {data['timestamp'][:19]} - 行数: {data['data'].get('total_rows', 0)}")
        
        return "\n".join(formatted)
    
    async def _present_results(self, context: ChatContext, analysis_result: Dict[str, Any]):
        """展示结果"""
        try:
            # 发送SQL结果
            await self.websocket_service.send_result_message(
                context.session_id,
                f"查询完成，共找到 {context.query_result['total_rows']} 条记录",
                {
                    "sql": context.generated_sql,
                    "result": context.query_result,
                    "execution_time": context.query_result.get("execution_time", 0)
                }
            )
            
            # 发送数据分析
            await self.websocket_service.send_result_message(
                context.session_id,
                analysis_result["analysis"],
                {"type": "analysis"}
            )
            
            # 如果数据适合图表展示，发送图表数据
            if self._should_generate_chart(context.query_result):
                chart_data = self._generate_chart_data(context.query_result)
                await self.websocket_service.send_chart_message(
                    context.session_id,
                    chart_data
                )
            
            await self.websocket_service.send_status_message(
                context.session_id, "分析完成", 1.0
            )
            
        except Exception as e:
            logger.error(f"结果展示失败: {str(e)}")
    
    def _should_generate_chart(self, query_result: Dict[str, Any]) -> bool:
        """判断是否应该生成图表"""
        if not query_result or not query_result.get("rows"):
            return False
        
        # 如果有数值列且行数适中，生成图表
        return (
            len(query_result["rows"]) > 1 and 
            len(query_result["rows"]) <= 100 and
            len(query_result["columns"]) >= 2
        )
    
    def _generate_chart_data(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成图表数据"""
        columns = query_result["columns"]
        rows = query_result["rows"]
        
        # 简单的图表数据生成逻辑
        if len(columns) >= 2:
            return {
                "type": "bar",
                "data": [
                    {"x": str(row[0]), "y": float(row[1]) if isinstance(row[1], (int, float)) else 0}
                    for row in rows[:20]  # 最多20个数据点
                ],
                "xAxis": columns[0],
                "yAxis": columns[1]
            }
        
        return {"type": "table", "data": {"columns": columns, "rows": rows}}
    
    async def _handle_pipeline_error(self, context: ChatContext, stage: str, error: str) -> Dict[str, Any]:
        """处理流水线错误"""
        context.add_error(f"{stage}: {error}")
        context.update_stage(ChatStage.ERROR_HANDLING)
        
        await self.websocket_service.send_error_message(
            context.session_id,
            f"{stage}: {error}",
            "PIPELINE_ERROR"
        )
        
        # 如果错误次数过多，终止对话
        if context.error_count >= self.max_error_count:
            await self.websocket_service.send_error_message(
                context.session_id,
                "错误次数过多，对话已终止",
                "MAX_ERRORS_EXCEEDED"
            )
            return {
                "success": False,
                "error": "错误次数过多",
                "session_id": context.session_id,
                "terminated": True
            }
        
        return {
            "success": False,
            "error": error,
            "session_id": context.session_id,
            "stage": stage,
            "retry_available": context.retry_count < self.max_retry_count
        }
    
    async def _request_clarification(self, context: ChatContext, clarification_question: str) -> Dict[str, Any]:
        """请求意图澄清"""
        context.update_stage(ChatStage.INTENT_CLARIFICATION)
        
        await self.websocket_service.send_result_message(
            context.session_id,
            f"需要澄清: {clarification_question}",
            {
                "type": "clarification",
                "question": clarification_question,
                "selected_tables": context.selected_tables
            }
        )
        
        return {
            "success": True,
            "needs_clarification": True,
            "clarification_question": clarification_question,
            "session_id": context.session_id
        }
    
    async def _handle_clarification_response(self, context: ChatContext, user_response: str) -> Dict[str, Any]:
        """处理澄清回复"""
        # 继续执行流水线
        return await self._execute_chat_pipeline(context, user_response, None)
    
    async def _handle_error_recovery(self, context: ChatContext, user_response: str) -> Dict[str, Any]:
        """处理错误恢复"""
        if user_response.lower() in ["重试", "retry", "再试一次"]:
            context.retry_count += 1
            if context.retry_count <= self.max_retry_count:
                # 重置到上一个成功的阶段
                context.update_stage(ChatStage.INTENT_RECOGNITION)
                return await self._execute_chat_pipeline(context, user_response, None)
            else:
                return {
                    "success": False,
                    "error": "重试次数已达上限",
                    "session_id": context.session_id
                }
        else:
            # 作为新问题处理
            context.update_stage(ChatStage.INTENT_RECOGNITION)
            return await self._execute_chat_pipeline(context, user_response, None)
    
    async def _handle_followup_question(self, context: ChatContext, user_question: str) -> Dict[str, Any]:
        """处理追问"""
        try:
            # 使用本地模型处理追问
            followup_prompt = f"""
            基于之前的查询结果，回答用户的追问：
            
            用户追问: {user_question}
            
            之前的查询结果:
            {context.query_result}
            
            历史数据:
            {self._format_previous_data(context.previous_data)}
            
            请基于已有数据回答用户问题。
            """
            
            await self.websocket_service.send_thinking_message(
                context.session_id, "正在分析您的追问...", {"stage": "followup", "progress": 0.5}
            )
            
            response = await self.ai_service.call_local_model(
                followup_prompt,
                session_id=context.session_id
            )
            
            if response["success"]:
                await self.websocket_service.send_result_message(
                    context.session_id,
                    response["content"],
                    {"type": "followup_answer"}
                )
                
                return {
                    "success": True,
                    "answer": response["content"],
                    "session_id": context.session_id,
                    "type": "followup"
                }
            else:
                return {
                    "success": False,
                    "error": "追问处理失败",
                    "session_id": context.session_id
                }
                
        except Exception as e:
            logger.error(f"追问处理失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": context.session_id
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        context = self.active_contexts.get(session_id)
        if not context:
            return {
                "session_id": session_id,
                "exists": False
            }
        
        return {
            "session_id": session_id,
            "exists": True,
            "current_stage": context.current_stage.value,
            "intent": context.intent.value,
            "selected_tables": context.selected_tables,
            "error_count": context.error_count,
            "retry_count": context.retry_count,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "has_result": context.query_result is not None,
            "previous_data_count": len(context.previous_data)
        }
    
    def cleanup_session(self, session_id: str) -> bool:
        """清理会话"""
        if session_id in self.active_contexts:
            del self.active_contexts[session_id]
            logger.info(f"会话 {session_id} 已清理")
            return True
        return False
    
    def get_all_sessions_status(self) -> Dict[str, Any]:
        """获取所有会话状态"""
        return {
            "total_sessions": len(self.active_contexts),
            "sessions": {
                session_id: {
                    "current_stage": context.current_stage.value,
                    "intent": context.intent.value,
                    "error_count": context.error_count,
                    "updated_at": context.updated_at.isoformat()
                }
                for session_id, context in self.active_contexts.items()
            }
        }


# 全局实例
_chat_orchestrator = None

def get_chat_orchestrator() -> ChatOrchestrator:
    """获取对话编排器实例"""
    global _chat_orchestrator
    if _chat_orchestrator is None:
        _chat_orchestrator = ChatOrchestrator()
    return _chat_orchestrator