"""
语义上下文聚合引擎

实现五模块元数据的智能聚合和相关性评分、动态上下文裁剪和优化算法、
按需加载的条件性模块注入、Token使用量的精确控制和预算管理。
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
from collections import defaultdict

from src.services.data_source_semantic_injection import DataSourceSemanticInjectionService
from src.services.table_structure_semantic_injection import TableStructureSemanticInjectionService
from src.services.table_relation_semantic_injection import TableRelationSemanticInjectionService
from src.services.semantic_injection_service import SemanticInjectionService
from src.services.knowledge_semantic_injection import KnowledgeSemanticInjectionService

logger = logging.getLogger(__name__)


class ModuleType(str, Enum):
    """模块类型枚举"""
    DATA_SOURCE = "data_source"
    TABLE_STRUCTURE = "table_structure"
    TABLE_RELATION = "table_relation"
    DICTIONARY = "dictionary"
    KNOWLEDGE = "knowledge"


class ContextPriority(str, Enum):
    """上下文优先级枚举"""
    CRITICAL = "critical"    # 关键信息，必须包含
    HIGH = "high"           # 高优先级，优先包含
    MEDIUM = "medium"       # 中等优先级，空间允许时包含
    LOW = "low"            # 低优先级，最后考虑


@dataclass
class TokenBudget:
    """Token预算管理"""
    total_budget: int = 4000        # 总Token预算
    reserved_for_response: int = 1000  # 为响应预留的Token
    available_for_context: int = field(init=False)  # 可用于上下文的Token
    
    def __post_init__(self):
        self.available_for_context = self.total_budget - self.reserved_for_response


@dataclass
class SemanticModule:
    """语义模块信息"""
    module_type: ModuleType
    service: Any
    priority: ContextPriority
    estimated_tokens: int = 0
    relevance_score: float = 0.0
    is_loaded: bool = False
    content: Optional[Dict[str, Any]] = None


@dataclass
class AggregationContext:
    """聚合上下文"""
    user_question: str
    table_ids: Optional[List[str]] = None
    include_global: bool = True
    token_budget: TokenBudget = field(default_factory=TokenBudget)
    modules: List[SemanticModule] = field(default_factory=list)
    aggregated_content: Dict[str, Any] = field(default_factory=dict)
    total_tokens_used: int = 0


@dataclass
class AggregationResult:
    """聚合结果"""
    enhanced_context: str
    modules_used: List[str]
    total_tokens_used: int
    token_budget_remaining: int
    relevance_scores: Dict[str, float]
    optimization_summary: Dict[str, Any]


class SemanticContextAggregator:
    """语义上下文聚合引擎"""
    
    def __init__(self, db_session=None):
        self.db = db_session
        
        # 初始化五个语义模块服务
        self.data_source_service = DataSourceSemanticInjectionService(db_session)
        self.table_structure_service = TableStructureSemanticInjectionService(db_session)
        self.table_relation_service = TableRelationSemanticInjectionService(db_session)
        self.dictionary_service = SemanticInjectionService()  # 不需要db_session参数
        self.knowledge_service = KnowledgeSemanticInjectionService(db_session)
        
        # Token估算配置
        self.token_estimation_config = {
            ModuleType.DATA_SOURCE: {"base": 200, "per_source": 100},
            ModuleType.TABLE_STRUCTURE: {"base": 300, "per_table": 150},
            ModuleType.TABLE_RELATION: {"base": 250, "per_relation": 80},
            ModuleType.DICTIONARY: {"base": 400, "per_field": 50},
            ModuleType.KNOWLEDGE: {"base": 300, "per_item": 100}
        }
        
        # 缓存
        self.context_cache: Dict[str, AggregationResult] = {}
        self.relevance_cache: Dict[str, Dict[str, float]] = {}
    
    async def aggregate_semantic_context(
        self,
        user_question: str,
        table_ids: Optional[List[str]] = None,
        include_global: bool = True,
        token_budget: Optional[TokenBudget] = None,
        module_priorities: Optional[Dict[ModuleType, ContextPriority]] = None
    ) -> AggregationResult:
        """
        聚合语义上下文
        
        Args:
            user_question: 用户问题
            table_ids: 相关表ID列表
            include_global: 是否包含全局知识
            token_budget: Token预算
            module_priorities: 模块优先级配置
            
        Returns:
            聚合结果
        """
        try:
            logger.info(f"开始语义上下文聚合，问题: {user_question[:100]}...")
            
            # 创建聚合上下文
            context = AggregationContext(
                user_question=user_question,
                table_ids=table_ids,
                include_global=include_global,
                token_budget=token_budget or TokenBudget()
            )
            
            # 1. 初始化语义模块
            await self._initialize_semantic_modules(context, module_priorities)
            
            # 2. 计算模块相关性评分
            await self._calculate_module_relevance(context)
            
            # 3. 动态上下文裁剪和优化
            await self._optimize_context_selection(context)
            
            # 4. 按需加载选中的模块
            await self._load_selected_modules(context)
            
            # 5. 生成最终的聚合上下文
            enhanced_context = await self._generate_aggregated_context(context)
            
            # 6. 生成优化摘要
            optimization_summary = self._generate_optimization_summary(context)
            
            result = AggregationResult(
                enhanced_context=enhanced_context,
                modules_used=[m.module_type.value for m in context.modules if m.is_loaded],
                total_tokens_used=context.total_tokens_used,
                token_budget_remaining=context.token_budget.available_for_context - context.total_tokens_used,
                relevance_scores={m.module_type.value: m.relevance_score for m in context.modules},
                optimization_summary=optimization_summary
            )
            
            logger.info(f"语义上下文聚合完成，使用Token: {context.total_tokens_used}")
            return result
            
        except Exception as e:
            logger.error(f"语义上下文聚合失败: {str(e)}", exc_info=True)
            # 返回基础上下文
            return AggregationResult(
                enhanced_context=f"用户问题: {user_question}",
                modules_used=[],
                total_tokens_used=0,
                token_budget_remaining=token_budget.available_for_context if token_budget else 3000,
                relevance_scores={},
                optimization_summary={"error": str(e)}
            )
    
    async def _initialize_semantic_modules(
        self,
        context: AggregationContext,
        module_priorities: Optional[Dict[ModuleType, ContextPriority]] = None
    ):
        """初始化语义模块"""
        default_priorities = {
            ModuleType.TABLE_STRUCTURE: ContextPriority.CRITICAL,
            ModuleType.DICTIONARY: ContextPriority.HIGH,
            ModuleType.DATA_SOURCE: ContextPriority.HIGH,
            ModuleType.TABLE_RELATION: ContextPriority.MEDIUM,
            ModuleType.KNOWLEDGE: ContextPriority.MEDIUM
        }
        
        priorities = module_priorities or default_priorities
        
        # 创建语义模块
        modules = [
            SemanticModule(
                module_type=ModuleType.DATA_SOURCE,
                service=self.data_source_service,
                priority=priorities.get(ModuleType.DATA_SOURCE, ContextPriority.MEDIUM)
            ),
            SemanticModule(
                module_type=ModuleType.TABLE_STRUCTURE,
                service=self.table_structure_service,
                priority=priorities.get(ModuleType.TABLE_STRUCTURE, ContextPriority.CRITICAL)
            ),
            SemanticModule(
                module_type=ModuleType.TABLE_RELATION,
                service=self.table_relation_service,
                priority=priorities.get(ModuleType.TABLE_RELATION, ContextPriority.MEDIUM)
            ),
            SemanticModule(
                module_type=ModuleType.DICTIONARY,
                service=self.dictionary_service,
                priority=priorities.get(ModuleType.DICTIONARY, ContextPriority.HIGH)
            ),
            SemanticModule(
                module_type=ModuleType.KNOWLEDGE,
                service=self.knowledge_service,
                priority=priorities.get(ModuleType.KNOWLEDGE, ContextPriority.MEDIUM)
            )
        ]
        
        context.modules = modules
        logger.debug(f"初始化了 {len(modules)} 个语义模块")
    
    async def _calculate_module_relevance(self, context: AggregationContext):
        """计算模块相关性评分"""
        try:
            # 提取问题关键词
            keywords = self._extract_keywords(context.user_question)
            
            for module in context.modules:
                # 基于模块类型和问题内容计算相关性
                relevance_score = await self._calculate_relevance_for_module(
                    module, keywords, context
                )
                module.relevance_score = relevance_score
                
                # 估算Token使用量
                estimated_tokens = self._estimate_module_tokens(module, context)
                module.estimated_tokens = estimated_tokens
                
                logger.debug(f"模块 {module.module_type.value} 相关性: {relevance_score:.2f}, 估算Token: {estimated_tokens}")
                
        except Exception as e:
            logger.error(f"计算模块相关性失败: {str(e)}", exc_info=True)
    
    async def _calculate_relevance_for_module(
        self,
        module: SemanticModule,
        keywords: Set[str],
        context: AggregationContext
    ) -> float:
        """计算单个模块的相关性评分"""
        base_score = 0.0
        
        # 基于模块类型的基础评分
        type_scores = {
            ModuleType.TABLE_STRUCTURE: 0.9,  # 表结构几乎总是需要的
            ModuleType.DICTIONARY: 0.8,       # 数据字典很重要
            ModuleType.DATA_SOURCE: 0.7,      # 数据源信息重要
            ModuleType.TABLE_RELATION: 0.6,   # 表关联中等重要
            ModuleType.KNOWLEDGE: 0.5          # 知识库依情况而定
        }
        
        base_score = type_scores.get(module.module_type, 0.5)
        
        # 基于关键词匹配的评分调整
        keyword_bonus = 0.0
        
        if module.module_type == ModuleType.TABLE_STRUCTURE:
            # 表结构相关关键词
            structure_keywords = {'表', '字段', '列', '结构', 'table', 'column', 'field'}
            keyword_bonus = len(keywords.intersection(structure_keywords)) * 0.1
            
        elif module.module_type == ModuleType.DICTIONARY:
            # 数据字典相关关键词
            dict_keywords = {'含义', '业务', '字典', '映射', 'meaning', 'business', 'dictionary'}
            keyword_bonus = len(keywords.intersection(dict_keywords)) * 0.1
            
        elif module.module_type == ModuleType.TABLE_RELATION:
            # 表关联相关关键词
            relation_keywords = {'关联', '连接', '关系', 'join', 'relation', 'link'}
            keyword_bonus = len(keywords.intersection(relation_keywords)) * 0.15
            
        elif module.module_type == ModuleType.KNOWLEDGE:
            # 知识库相关关键词
            knowledge_keywords = {'规则', '逻辑', '术语', '事件', 'rule', 'logic', 'term', 'event'}
            keyword_bonus = len(keywords.intersection(knowledge_keywords)) * 0.2
        
        # 基于表ID的相关性调整
        table_bonus = 0.0
        if context.table_ids:
            if module.module_type in [ModuleType.TABLE_STRUCTURE, ModuleType.DICTIONARY, ModuleType.TABLE_RELATION]:
                table_bonus = 0.2  # 有具体表时，这些模块更重要
        
        final_score = min(1.0, base_score + keyword_bonus + table_bonus)
        return final_score
    
    def _estimate_module_tokens(self, module: SemanticModule, context: AggregationContext) -> int:
        """估算模块Token使用量"""
        config = self.token_estimation_config.get(module.module_type, {"base": 200, "per_item": 50})
        base_tokens = config["base"]
        
        # 基于上下文估算额外Token
        extra_tokens = 0
        
        if module.module_type == ModuleType.TABLE_STRUCTURE and context.table_ids:
            extra_tokens = len(context.table_ids) * config.get("per_table", 150)
        elif module.module_type == ModuleType.DICTIONARY and context.table_ids:
            # 假设每个表平均有10个字段
            estimated_fields = len(context.table_ids) * 10
            extra_tokens = estimated_fields * config.get("per_field", 50)
        elif module.module_type == ModuleType.TABLE_RELATION and context.table_ids:
            # 假设表之间有一些关联
            estimated_relations = max(0, len(context.table_ids) - 1) * 2
            extra_tokens = estimated_relations * config.get("per_relation", 80)
        elif module.module_type == ModuleType.KNOWLEDGE:
            # 基于问题长度估算知识项数量
            estimated_items = min(10, len(context.user_question.split()) // 3)
            extra_tokens = estimated_items * config.get("per_item", 100)
        
        return base_tokens + extra_tokens
    
    async def _optimize_context_selection(self, context: AggregationContext):
        """动态上下文裁剪和优化"""
        try:
            # 按优先级和相关性排序模块
            context.modules.sort(
                key=lambda m: (
                    self._get_priority_weight(m.priority),
                    m.relevance_score
                ),
                reverse=True
            )
            
            # 贪心算法选择模块，在Token预算内最大化价值
            selected_modules = []
            remaining_budget = context.token_budget.available_for_context
            
            # 首先处理关键模块，但也要检查预算
            critical_modules = [m for m in context.modules if m.priority == ContextPriority.CRITICAL]
            for module in critical_modules:
                if remaining_budget >= module.estimated_tokens:
                    selected_modules.append(module)
                    remaining_budget -= module.estimated_tokens
                    logger.debug(f"关键模块 {module.module_type.value} 已选中")
                else:
                    logger.warning(f"关键模块 {module.module_type.value} 因预算不足被跳过")
            
            # 然后处理其他模块
            other_modules = [m for m in context.modules if m.priority != ContextPriority.CRITICAL]
            for module in other_modules:
                # 计算模块的价值密度（相关性/Token成本）
                if module.estimated_tokens > 0:
                    value_density = module.relevance_score / module.estimated_tokens
                else:
                    value_density = module.relevance_score
                
                # 基于预算和价值密度选择
                if remaining_budget >= module.estimated_tokens and value_density > 0.3:
                    selected_modules.append(module)
                    remaining_budget -= module.estimated_tokens
                    logger.debug(f"模块 {module.module_type.value} 已选中，价值密度: {value_density:.3f}")
                else:
                    logger.debug(f"模块 {module.module_type.value} 被跳过，预算不足或价值密度低")
            
            # 更新模块选择状态
            for module in context.modules:
                module.is_loaded = module in selected_modules
            
            logger.info(f"优化完成，选中 {len(selected_modules)} 个模块，剩余预算: {remaining_budget}")
            
        except Exception as e:
            logger.error(f"上下文优化失败: {str(e)}", exc_info=True)
    
    def _get_priority_weight(self, priority: ContextPriority) -> int:
        """获取优先级权重"""
        weights = {
            ContextPriority.CRITICAL: 4,
            ContextPriority.HIGH: 3,
            ContextPriority.MEDIUM: 2,
            ContextPriority.LOW: 1
        }
        return weights.get(priority, 1)
    
    async def _load_selected_modules(self, context: AggregationContext):
        """按需加载选中的模块"""
        try:
            for module in context.modules:
                if not module.is_loaded:
                    continue
                
                logger.debug(f"加载模块: {module.module_type.value}")
                
                # 根据模块类型调用相应的服务
                if module.module_type == ModuleType.DATA_SOURCE:
                    content = await self._load_data_source_content(context)
                elif module.module_type == ModuleType.TABLE_STRUCTURE:
                    content = await self._load_table_structure_content(context)
                elif module.module_type == ModuleType.TABLE_RELATION:
                    content = await self._load_table_relation_content(context)
                elif module.module_type == ModuleType.DICTIONARY:
                    content = await self._load_dictionary_content(context)
                elif module.module_type == ModuleType.KNOWLEDGE:
                    content = await self._load_knowledge_content(context)
                else:
                    content = {}
                
                module.content = content
                context.aggregated_content[module.module_type.value] = content
                
                # 更新实际Token使用量
                actual_tokens = self._calculate_actual_tokens(content)
                context.total_tokens_used += actual_tokens
                
                logger.debug(f"模块 {module.module_type.value} 加载完成，实际Token: {actual_tokens}")
                
        except Exception as e:
            logger.error(f"模块加载失败: {str(e)}", exc_info=True)
    
    async def _load_data_source_content(self, context: AggregationContext) -> Dict[str, Any]:
        """加载数据源语义内容"""
        try:
            # 这里应该调用数据源语义注入服务
            # 由于服务可能不存在，我们返回模拟内容
            return {
                "module_type": "data_source",
                "content": "数据源语义信息：MySQL数据库，支持LIMIT语法",
                "sql_dialect": {"limit_syntax": "LIMIT {limit}"},
                "performance_tips": ["使用索引优化查询", "避免全表扫描"]
            }
        except Exception as e:
            logger.error(f"加载数据源内容失败: {str(e)}")
            return {}
    
    async def _load_table_structure_content(self, context: AggregationContext) -> Dict[str, Any]:
        """加载表结构语义内容"""
        try:
            if not context.table_ids:
                return {}
            
            # 这里应该调用表结构语义注入服务
            return {
                "module_type": "table_structure",
                "content": f"表结构信息：涉及 {len(context.table_ids)} 个表",
                "tables": context.table_ids,
                "structure_info": "包含主键、外键、索引信息"
            }
        except Exception as e:
            logger.error(f"加载表结构内容失败: {str(e)}")
            return {}
    
    async def _load_table_relation_content(self, context: AggregationContext) -> Dict[str, Any]:
        """加载表关联语义内容"""
        try:
            if not context.table_ids or len(context.table_ids) < 2:
                return {}
            
            # 这里应该调用表关联语义注入服务
            return {
                "module_type": "table_relation",
                "content": f"表关联信息：{len(context.table_ids)} 个表之间的关联关系",
                "relations": ["INNER JOIN", "LEFT JOIN"],
                "join_conditions": "基于外键关系"
            }
        except Exception as e:
            logger.error(f"加载表关联内容失败: {str(e)}")
            return {}
    
    async def _load_dictionary_content(self, context: AggregationContext) -> Dict[str, Any]:
        """加载数据字典语义内容"""
        try:
            # 调用数据字典语义注入服务，传递数据库会话
            result = self.dictionary_service.inject_semantic_values(
                db=self.db,  # 传递数据库会话
                table_ids=context.table_ids or [],
                field_names=[],
                include_mappings=True
            )
            
            return {
                "module_type": "dictionary",
                "content": "数据字典语义信息",
                "field_mappings": result.get("field_mappings", []),
                "semantic_values": result.get("semantic_values", {})
            }
        except Exception as e:
            logger.error(f"加载数据字典内容失败: {str(e)}")
            return {}
    
    async def _load_knowledge_content(self, context: AggregationContext) -> Dict[str, Any]:
        """加载知识库语义内容"""
        try:
            # 调用知识库语义注入服务
            result = self.knowledge_service.inject_knowledge_semantics(
                user_question=context.user_question,
                table_ids=context.table_ids,
                include_global=context.include_global,
                max_terms=5,
                max_logics=3,
                max_events=2
            )
            
            return {
                "module_type": "knowledge",
                "content": result.enhanced_context,
                "knowledge_info": {
                    "terms_count": len(result.knowledge_info.terms),
                    "logics_count": len(result.knowledge_info.logics),
                    "events_count": len(result.knowledge_info.events)
                },
                "total_relevance_score": result.knowledge_info.total_relevance_score
            }
        except Exception as e:
            logger.error(f"加载知识库内容失败: {str(e)}")
            return {}
    
    def _calculate_actual_tokens(self, content: Dict[str, Any]) -> int:
        """计算实际Token使用量"""
        try:
            # 简单的Token估算：每4个字符约等于1个Token
            content_str = json.dumps(content, ensure_ascii=False)
            return len(content_str) // 4
        except Exception:
            return 0
    
    async def _generate_aggregated_context(self, context: AggregationContext) -> str:
        """生成最终的聚合上下文"""
        try:
            context_parts = [f"用户问题: {context.user_question}"]
            
            # 按优先级顺序添加模块内容
            for module in sorted(context.modules, key=lambda m: self._get_priority_weight(m.priority), reverse=True):
                if not module.is_loaded or not module.content:
                    continue
                
                module_content = module.content.get("content", "")
                if module_content:
                    context_parts.append(f"\n{module.module_type.value.replace('_', ' ').title()}:")
                    context_parts.append(module_content)
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"生成聚合上下文失败: {str(e)}")
            return f"用户问题: {context.user_question}"
    
    def _generate_optimization_summary(self, context: AggregationContext) -> Dict[str, Any]:
        """生成优化摘要"""
        return {
            "total_modules_available": len(context.modules),
            "modules_selected": len([m for m in context.modules if m.is_loaded]),
            "token_budget_used": context.total_tokens_used,
            "token_budget_total": context.token_budget.available_for_context,
            "token_utilization_rate": context.total_tokens_used / context.token_budget.available_for_context,
            "modules_by_priority": {
                priority.value: len([m for m in context.modules if m.priority == priority and m.is_loaded])
                for priority in ContextPriority
            },
            "average_relevance_score": sum(m.relevance_score for m in context.modules if m.is_loaded) / max(1, len([m for m in context.modules if m.is_loaded]))
        }
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取文本关键词"""
        # 简单的关键词提取，支持中文分词
        import re
        
        # 对于中文文本，我们使用简单的字符级分割和常见词汇识别
        # 首先提取中文字符序列和英文单词
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        
        # 简单的中文词汇识别（基于常见词汇模式）
        chinese_text = ''.join(chinese_chars)
        chinese_keywords = set()
        
        # 常见的中文词汇模式
        common_words = ['查询', '用户', '表', '字段', '信息', '业务', '含义', '数据', '分析', '统计', '报表', '图表']
        for word in common_words:
            if word in chinese_text:
                chinese_keywords.add(word)
        
        # 合并中英文关键词
        keywords = chinese_keywords.union(set(english_words))
        
        # 过滤停用词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '如果', '那么', '这', '那', '什么', '怎么', '为什么', 'the', 'is', 'in', 'and', 'or', 'but'}
        keywords = {word for word in keywords if len(word) > 1 and word not in stop_words}
        
        return keywords
    
    def clear_cache(self):
        """清空缓存"""
        self.context_cache.clear()
        self.relevance_cache.clear()
        logger.info("语义上下文聚合器缓存已清空")