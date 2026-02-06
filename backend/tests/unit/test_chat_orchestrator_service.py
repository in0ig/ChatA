"""
对话流程编排引擎服务单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.chat_orchestrator import (
    ChatOrchestrator,
    ChatContext,
    ChatStage,
    ChatIntent,
    get_chat_orchestrator
)


@pytest.fixture
def chat_orchestrator():
    """创建对话编排器实例"""
    return ChatOrchestrator()


@pytest.fixture
def mock_context():
    """创建模拟对话上下文"""
    context = ChatContext("test_session_1")
    context.intent = ChatIntent.SMART_QUERY
    context.selected_tables = ["products", "sales"]
    context.generated_sql = "SELECT * FROM products"
    context.query_result = {
        "columns": ["id", "name", "price"],
        "rows": [[1, "Product A", 100], [2, "Product B", 200]],
        "total_rows": 2,
        "execution_time": 0.05
    }
    return context


class TestChatContext:
    """对话上下文测试"""
    
    def test_chat_context_creation(self):
        """测试创建对话上下文"""
        session_id = "test_session"
        context = ChatContext(session_id)
        
        assert context.session_id == session_id
        assert context.current_stage == ChatStage.INTENT_RECOGNITION
        assert context.intent == ChatIntent.UNKNOWN
        assert context.selected_tables == []
        assert context.generated_sql is None
        assert context.query_result is None
        assert context.previous_data == []
        assert context.error_count == 0
        assert context.retry_count == 0
        assert isinstance(context.metadata, dict)
        assert context.created_at is not None
        assert context.updated_at is not None
    
    def test_update_stage(self):
        """测试更新对话阶段"""
        context = ChatContext("test_session")
        original_time = context.updated_at
        
        context.update_stage(ChatStage.TABLE_SELECTION)
        
        assert context.current_stage == ChatStage.TABLE_SELECTION
        assert context.updated_at > original_time
    
    def test_add_error(self):
        """测试添加错误记录"""
        context = ChatContext("test_session")
        
        context.add_error("测试错误")
        
        assert context.error_count == 1
        assert "errors" in context.metadata
        assert len(context.metadata["errors"]) == 1
        
        error = context.metadata["errors"][0]
        assert error["error"] == "测试错误"
        assert error["stage"] == ChatStage.INTENT_RECOGNITION.value
        assert "timestamp" in error
    
    def test_add_previous_data(self):
        """测试添加历史数据"""
        context = ChatContext("test_session")
        context.generated_sql = "SELECT * FROM test"
        
        test_data = {"columns": ["id"], "rows": [[1]], "total_rows": 1}
        context.add_previous_data(test_data)
        
        assert len(context.previous_data) == 1
        assert context.previous_data[0]["data"] == test_data
        assert context.previous_data[0]["sql"] == "SELECT * FROM test"
        assert "timestamp" in context.previous_data[0]
    
    def test_add_previous_data_limit(self):
        """测试历史数据数量限制"""
        context = ChatContext("test_session")
        
        # 添加6条历史数据
        for i in range(6):
            context.add_previous_data({"test": i})
        
        # 应该只保留最近5条
        assert len(context.previous_data) == 5
        assert context.previous_data[0]["data"]["test"] == 1  # 最早的被删除
        assert context.previous_data[-1]["data"]["test"] == 5  # 最新的保留


class TestChatOrchestrator:
    """对话编排器测试"""
    
    @pytest.mark.asyncio
    async def test_get_or_create_context(self, chat_orchestrator):
        """测试获取或创建对话上下文"""
        session_id = "test_session"
        
        # 第一次调用，创建新上下文
        context1 = chat_orchestrator.get_or_create_context(session_id)
        assert context1.session_id == session_id
        assert session_id in chat_orchestrator.active_contexts
        
        # 第二次调用，返回已存在的上下文
        context2 = chat_orchestrator.get_or_create_context(session_id)
        assert context1 is context2
    
    @pytest.mark.asyncio
    @patch('src.services.chat_orchestrator.get_websocket_stream_service')
    @patch.object(ChatOrchestrator, '_execute_chat_pipeline')
    async def test_start_chat_success(self, mock_pipeline, mock_websocket, chat_orchestrator):
        """测试成功开始对话"""
        # 模拟依赖
        mock_websocket_service = AsyncMock()
        mock_websocket_service.send_status_message = AsyncMock(return_value=True)
        mock_websocket.return_value = mock_websocket_service
        
        # 替换实例中的websocket服务
        chat_orchestrator.websocket_service = mock_websocket_service
        
        mock_pipeline.return_value = {
            "success": True,
            "session_id": "test_session",
            "intent": "smart_query",
            "tables": ["products"],
            "sql": "SELECT * FROM products",
            "result": {"columns": ["id"], "rows": [[1]]},
            "analysis": "分析结果",
            "stage": "completed"
        }
        
        # 执行测试
        result = await chat_orchestrator.start_chat("test_session", "查询产品信息")
        
        # 验证结果
        assert result["success"] is True
        assert result["session_id"] == "test_session"
        assert result["intent"] == "smart_query"
        
        # 验证WebSocket调用
        mock_websocket_service.send_status_message.assert_called_once()
        
        # 验证流水线调用
        mock_pipeline.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.chat_orchestrator.get_websocket_stream_service')
    async def test_start_chat_failure(self, mock_websocket, chat_orchestrator):
        """测试开始对话失败"""
        # 模拟WebSocket服务
        mock_websocket_service = AsyncMock()
        mock_websocket_service.send_status_message = AsyncMock(return_value=True)
        mock_websocket_service.send_error_message = AsyncMock(return_value=True)
        mock_websocket.return_value = mock_websocket_service
        
        # 替换实例中的websocket服务
        chat_orchestrator.websocket_service = mock_websocket_service
        
        # 模拟流水线执行失败
        with patch.object(chat_orchestrator, '_execute_chat_pipeline', side_effect=Exception("测试错误")):
            result = await chat_orchestrator.start_chat("test_session", "查询产品信息")
        
        # 验证结果
        assert result["success"] is False
        assert "测试错误" in result["error"]
        assert result["session_id"] == "test_session"
        
        # 验证错误消息发送
        mock_websocket_service.send_error_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_continue_chat_no_session(self, chat_orchestrator):
        """测试继续不存在的对话"""
        result = await chat_orchestrator.continue_chat("nonexistent_session", "用户回复")
        
        assert result["success"] is False
        assert "会话不存在或已过期" in result["error"]
        assert result["session_id"] == "nonexistent_session"
    
    @pytest.mark.asyncio
    @patch.object(ChatOrchestrator, '_handle_clarification_response')
    async def test_continue_chat_clarification(self, mock_handle, chat_orchestrator):
        """测试继续对话 - 澄清阶段"""
        # 创建处于澄清阶段的上下文
        context = chat_orchestrator.get_or_create_context("test_session")
        context.update_stage(ChatStage.INTENT_CLARIFICATION)
        
        mock_handle.return_value = {"success": True, "result": "澄清处理结果"}
        
        result = await chat_orchestrator.continue_chat("test_session", "是的，请继续")
        
        assert result["success"] is True
        mock_handle.assert_called_once_with(context, "是的，请继续")
    
    @pytest.mark.asyncio
    @patch.object(ChatOrchestrator, '_handle_error_recovery')
    async def test_continue_chat_error_handling(self, mock_handle, chat_orchestrator):
        """测试继续对话 - 错误处理阶段"""
        # 创建处于错误处理阶段的上下文
        context = chat_orchestrator.get_or_create_context("test_session")
        context.update_stage(ChatStage.ERROR_HANDLING)
        
        mock_handle.return_value = {"success": True, "result": "错误恢复结果"}
        
        result = await chat_orchestrator.continue_chat("test_session", "重试")
        
        assert result["success"] is True
        mock_handle.assert_called_once_with(context, "重试")
    
    @pytest.mark.asyncio
    @patch.object(ChatOrchestrator, '_handle_followup_question')
    async def test_continue_chat_followup(self, mock_handle, chat_orchestrator):
        """测试继续对话 - 追问"""
        # 创建已完成的上下文
        context = chat_orchestrator.get_or_create_context("test_session")
        context.update_stage(ChatStage.COMPLETED)
        
        mock_handle.return_value = {"success": True, "answer": "追问答案"}
        
        result = await chat_orchestrator.continue_chat("test_session", "为什么是这个结果？")
        
        assert result["success"] is True
        mock_handle.assert_called_once_with(context, "为什么是这个结果？")
    
    @pytest.mark.asyncio
    @patch.object(ChatOrchestrator, '_recognize_intent')
    @patch('src.services.chat_orchestrator.get_websocket_stream_service')
    async def test_execute_chat_pipeline_intent_failure(self, mock_websocket, mock_intent, chat_orchestrator):
        """测试执行对话流水线 - 意图识别失败"""
        # 模拟依赖
        mock_websocket_service = AsyncMock()
        mock_websocket_service.send_thinking_message = AsyncMock(return_value=True)
        mock_websocket_service.send_error_message = AsyncMock(return_value=True)
        mock_websocket.return_value = mock_websocket_service
        
        # 替换实例中的websocket服务
        chat_orchestrator.websocket_service = mock_websocket_service
        
        mock_intent.return_value = {"success": False, "error": "意图识别失败"}
        
        context = chat_orchestrator.get_or_create_context("test_session")
        
        # 执行测试
        result = await chat_orchestrator._execute_chat_pipeline(context, "测试问题", None)
        
        # 验证结果
        assert result["success"] is False
        assert "意图识别失败" in result["error"]
        
        # 验证错误处理
        mock_websocket_service.send_error_message.assert_called()
    
    @pytest.mark.asyncio
    @patch.object(ChatOrchestrator, '_recognize_intent')
    @patch.object(ChatOrchestrator, '_select_tables')
    @patch('src.services.chat_orchestrator.get_websocket_stream_service')
    async def test_execute_chat_pipeline_table_selection_failure(self, mock_websocket, mock_tables, mock_intent, chat_orchestrator):
        """测试执行对话流水线 - 选表失败"""
        # 模拟依赖
        mock_websocket_service = AsyncMock()
        mock_websocket.return_value = mock_websocket_service
        
        mock_intent.return_value = {"success": True, "intent": "smart_query"}
        mock_tables.return_value = {"success": False, "error": "选表失败"}
        
        context = chat_orchestrator.get_or_create_context("test_session")
        
        # 执行测试
        result = await chat_orchestrator._execute_chat_pipeline(context, "测试问题", None)
        
        # 验证结果
        assert result["success"] is False
        assert "选表失败" in result["error"]
    
    @pytest.mark.asyncio
    @patch.object(ChatOrchestrator, '_recognize_intent')
    @patch.object(ChatOrchestrator, '_select_tables')
    @patch.object(ChatOrchestrator, '_request_clarification')
    @patch('src.services.chat_orchestrator.get_websocket_stream_service')
    async def test_execute_chat_pipeline_needs_clarification(self, mock_websocket, mock_clarify, mock_tables, mock_intent, chat_orchestrator):
        """测试执行对话流水线 - 需要澄清"""
        # 模拟依赖
        mock_websocket_service = AsyncMock()
        mock_websocket.return_value = mock_websocket_service
        
        mock_intent.return_value = {"success": True, "intent": "smart_query"}
        mock_tables.return_value = {
            "success": True,
            "tables": ["products"],
            "needs_clarification": True,
            "clarification_question": "请确认查询范围"
        }
        mock_clarify.return_value = {"success": True, "needs_clarification": True}
        
        context = chat_orchestrator.get_or_create_context("test_session")
        
        # 执行测试
        result = await chat_orchestrator._execute_chat_pipeline(context, "测试问题", None)
        
        # 验证结果
        assert result["success"] is True
        assert result["needs_clarification"] is True
        
        # 验证澄清请求
        mock_clarify.assert_called_once()
    
    def test_fallback_intent_recognition(self, chat_orchestrator):
        """测试意图识别降级策略"""
        # 测试查询意图
        result = chat_orchestrator._fallback_intent_recognition("查询销售数量")
        assert result["success"] is True
        assert result["intent"] == "smart_query"
        
        # 测试报告意图
        result = chat_orchestrator._fallback_intent_recognition("生成销售报告")
        assert result["success"] is True
        assert result["intent"] == "report_generation"
        
        # 测试追问意图
        result = chat_orchestrator._fallback_intent_recognition("为什么会这样？")
        assert result["success"] is True
        assert result["intent"] == "data_followup"
        
        # 测试未知意图
        result = chat_orchestrator._fallback_intent_recognition("随机文本")
        assert result["success"] is True
        assert result["intent"] == "smart_query"  # 默认为查询
        assert result["confidence"] == 0.5
    
    def test_extract_sql_from_response(self, chat_orchestrator):
        """测试从AI响应中提取SQL"""
        # 测试标准SQL代码块
        response1 = "```sql\nSELECT * FROM products\n```"
        sql1 = chat_orchestrator._extract_sql_from_response(response1)
        assert sql1 == "SELECT * FROM products"
        
        # 测试普通代码块
        response2 = "```\nSELECT * FROM users\n```"
        sql2 = chat_orchestrator._extract_sql_from_response(response2)
        assert sql2 == "SELECT * FROM users"
        
        # 测试无代码块
        response3 = "SELECT * FROM orders"
        sql3 = chat_orchestrator._extract_sql_from_response(response3)
        assert sql3 == "SELECT * FROM orders"
    
    def test_should_generate_chart(self, chat_orchestrator):
        """测试是否应该生成图表"""
        # 测试适合生成图表的数据
        good_result = {
            "columns": ["name", "value"],
            "rows": [["A", 10], ["B", 20], ["C", 30]],
            "total_rows": 3
        }
        assert chat_orchestrator._should_generate_chart(good_result) is True
        
        # 测试数据过少
        small_result = {
            "columns": ["name", "value"],
            "rows": [["A", 10]],
            "total_rows": 1
        }
        assert chat_orchestrator._should_generate_chart(small_result) is False
        
        # 测试数据过多
        large_result = {
            "columns": ["name", "value"],
            "rows": [["A", 10]] * 101,
            "total_rows": 101
        }
        assert chat_orchestrator._should_generate_chart(large_result) is False
        
        # 测试列数不足
        few_columns = {
            "columns": ["name"],
            "rows": [["A"], ["B"], ["C"]],
            "total_rows": 3
        }
        assert chat_orchestrator._should_generate_chart(few_columns) is False
    
    def test_generate_chart_data(self, chat_orchestrator):
        """测试生成图表数据"""
        query_result = {
            "columns": ["product", "sales"],
            "rows": [["A", 100], ["B", 200], ["C", 150]],
            "total_rows": 3
        }
        
        chart_data = chat_orchestrator._generate_chart_data(query_result)
        
        assert chart_data["type"] == "bar"
        assert chart_data["xAxis"] == "product"
        assert chart_data["yAxis"] == "sales"
        assert len(chart_data["data"]) == 3
        assert chart_data["data"][0] == {"x": "A", "y": 100.0}
        assert chart_data["data"][1] == {"x": "B", "y": 200.0}
        assert chart_data["data"][2] == {"x": "C", "y": 150.0}
    
    def test_format_previous_data(self, chat_orchestrator):
        """测试格式化历史数据"""
        # 测试无历史数据
        result1 = chat_orchestrator._format_previous_data([])
        assert result1 == "无历史数据"
        
        # 测试有历史数据
        previous_data = [
            {
                "timestamp": "2024-01-01T10:00:00.000Z",
                "data": {"total_rows": 10}
            },
            {
                "timestamp": "2024-01-01T11:00:00.000Z",
                "data": {"total_rows": 20}
            }
        ]
        
        result2 = chat_orchestrator._format_previous_data(previous_data)
        assert "历史查询1: 2024-01-01T10:00:00 - 行数: 10" in result2
        assert "历史查询2: 2024-01-01T11:00:00 - 行数: 20" in result2
    
    def test_get_session_status(self, chat_orchestrator):
        """测试获取会话状态"""
        # 测试不存在的会话
        status1 = chat_orchestrator.get_session_status("nonexistent")
        assert status1["session_id"] == "nonexistent"
        assert status1["exists"] is False
        
        # 测试存在的会话
        context = chat_orchestrator.get_or_create_context("test_session")
        context.intent = ChatIntent.SMART_QUERY
        context.selected_tables = ["products"]
        context.query_result = {"test": "data"}
        context.add_previous_data({"test": "previous"})
        
        status2 = chat_orchestrator.get_session_status("test_session")
        assert status2["session_id"] == "test_session"
        assert status2["exists"] is True
        assert status2["current_stage"] == ChatStage.INTENT_RECOGNITION.value
        assert status2["intent"] == ChatIntent.SMART_QUERY.value
        assert status2["selected_tables"] == ["products"]
        assert status2["has_result"] is True
        assert status2["previous_data_count"] == 1
    
    def test_cleanup_session(self, chat_orchestrator):
        """测试清理会话"""
        # 创建会话
        chat_orchestrator.get_or_create_context("test_session")
        assert "test_session" in chat_orchestrator.active_contexts
        
        # 清理会话
        result = chat_orchestrator.cleanup_session("test_session")
        assert result is True
        assert "test_session" not in chat_orchestrator.active_contexts
        
        # 清理不存在的会话
        result2 = chat_orchestrator.cleanup_session("nonexistent")
        assert result2 is False
    
    def test_get_all_sessions_status(self, chat_orchestrator):
        """测试获取所有会话状态"""
        # 创建几个会话
        chat_orchestrator.get_or_create_context("session1")
        chat_orchestrator.get_or_create_context("session2")
        
        status = chat_orchestrator.get_all_sessions_status()
        
        assert status["total_sessions"] == 2
        assert "sessions" in status
        assert "session1" in status["sessions"]
        assert "session2" in status["sessions"]
        
        # 验证会话详情
        session1_info = status["sessions"]["session1"]
        assert session1_info["current_stage"] == ChatStage.INTENT_RECOGNITION.value
        assert session1_info["intent"] == ChatIntent.UNKNOWN.value
        assert session1_info["error_count"] == 0


class TestChatOrchestratorSingleton:
    """对话编排器单例测试"""
    
    def test_get_chat_orchestrator_singleton(self):
        """测试获取对话编排器单例"""
        orchestrator1 = get_chat_orchestrator()
        orchestrator2 = get_chat_orchestrator()
        
        assert orchestrator1 is orchestrator2
        assert isinstance(orchestrator1, ChatOrchestrator)


class TestChatOrchestratorIntegration:
    """对话编排器集成测试"""
    
    @pytest.mark.asyncio
    @patch('src.services.chat_orchestrator.get_websocket_stream_service')
    @patch.object(ChatOrchestrator, '_recognize_intent')
    @patch.object(ChatOrchestrator, '_select_tables')
    @patch.object(ChatOrchestrator, '_generate_sql')
    @patch.object(ChatOrchestrator, '_execute_sql')
    @patch.object(ChatOrchestrator, '_analyze_data')
    @patch.object(ChatOrchestrator, '_present_results')
    async def test_complete_chat_pipeline(self, mock_present, mock_analyze, mock_execute, 
                                        mock_generate, mock_select, mock_intent, 
                                        mock_websocket, chat_orchestrator):
        """测试完整对话流水线"""
        # 模拟所有依赖
        mock_websocket_service = AsyncMock()
        mock_websocket_service.send_status_message = AsyncMock(return_value=True)
        mock_websocket_service.send_thinking_message = AsyncMock(return_value=True)
        mock_websocket.return_value = mock_websocket_service
        
        # 替换实例中的websocket服务
        chat_orchestrator.websocket_service = mock_websocket_service
        
        mock_intent.return_value = {"success": True, "intent": "smart_query"}
        mock_select.return_value = {"success": True, "tables": ["products"], "needs_clarification": False}
        mock_generate.return_value = {"success": True, "sql": "SELECT * FROM products"}
        mock_execute.return_value = {"success": True, "result": {"columns": ["id"], "rows": [[1]]}}
        mock_analyze.return_value = {"success": True, "analysis": "分析结果"}
        mock_present.return_value = None
        
        # 执行完整流水线
        result = await chat_orchestrator.start_chat("test_session", "查询产品信息")
        
        # 验证结果
        assert result["success"] is True
        assert result["intent"] == "smart_query"
        assert result["tables"] == ["products"]
        assert result["sql"] == "SELECT * FROM products"
        assert result["analysis"] == "分析结果"
        assert result["stage"] == "completed"
        
        # 验证所有步骤都被调用
        mock_intent.assert_called_once()
        mock_select.assert_called_once()
        mock_generate.assert_called_once()
        mock_execute.assert_called_once()
        mock_analyze.assert_called_once()
        mock_present.assert_called_once()
        
        # 验证WebSocket消息发送
        assert mock_websocket_service.send_thinking_message.call_count >= 4  # 至少4个思考阶段
        mock_websocket_service.send_status_message.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.services.chat_orchestrator.get_websocket_stream_service')
    async def test_error_handling_max_errors(self, mock_websocket, chat_orchestrator):
        """测试错误处理 - 达到最大错误次数"""
        mock_websocket_service = AsyncMock()
        mock_websocket_service.send_error_message = AsyncMock(return_value=True)
        mock_websocket.return_value = mock_websocket_service
        
        # 替换实例中的websocket服务
        chat_orchestrator.websocket_service = mock_websocket_service
        
        context = chat_orchestrator.get_or_create_context("test_session")
        
        # 模拟达到最大错误次数
        for i in range(chat_orchestrator.max_error_count):
            context.add_error(f"错误 {i+1}")
        
        result = await chat_orchestrator._handle_pipeline_error(context, "测试阶段", "测试错误")
        
        assert result["success"] is False
        assert result["terminated"] is True
        assert "错误次数过多" in result["error"]
        
        # 验证发送了终止消息
        assert mock_websocket_service.send_error_message.call_count == 2  # 阶段错误 + 终止错误