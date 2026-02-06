"""
表结构语义注入服务

实现完整表结构元数据的结构化注入，包含表名、字段名、数据类型、约束、注释的语义描述，
添加主键、外键、索引信息的关联语义，创建表结构的业务含义增强机制。
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    """数据类型枚举"""
    INTEGER = "integer"
    STRING = "string"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    TEXT = "text"
    JSON = "json"


class ConstraintType(str, Enum):
    """约束类型枚举"""
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    NOT_NULL = "not_null"
    CHECK = "check"


@dataclass
class FieldInfo:
    """字段信息"""
    name: str
    data_type: DataType
    is_nullable: bool
    default_value: Optional[str]
    comment: Optional[str]
    constraints: List[ConstraintType]
    business_meaning: Optional[str] = None


@dataclass
class TableStructureInfo:
    """表结构信息"""
    table_name: str
    fields: List[FieldInfo]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, str]]
    indexes: List[Dict[str, Any]]
    comment: Optional[str]
    business_meaning: Optional[str] = None


class TableStructureSemanticInjectionService:
    """表结构语义注入服务"""
    
    def __init__(self, db_session=None):
        self.db = db_session
        
        # 数据类型语义映射
        self.data_type_semantics = {
            DataType.INTEGER: "整数类型，适用于计数、ID等",
            DataType.STRING: "字符串类型，适用于名称、描述等",
            DataType.DECIMAL: "小数类型，适用于金额、比率等",
            DataType.DATE: "日期类型，适用于生日、创建日期等",
            DataType.DATETIME: "日期时间类型，适用于时间戳等",
            DataType.BOOLEAN: "布尔类型，适用于状态标识等",
            DataType.TEXT: "长文本类型，适用于详细描述等",
            DataType.JSON: "JSON类型，适用于结构化数据存储"
        }
        
        # 字段名模式识别
        self.field_patterns = {
            "id": "标识符字段，通常为主键",
            "name": "名称字段，存储实体名称",
            "code": "编码字段，存储业务编码",
            "status": "状态字段，标识实体状态",
            "type": "类型字段，标识实体类型",
            "created_at": "创建时间字段",
            "updated_at": "更新时间字段",
            "deleted_at": "删除时间字段",
            "created_by": "创建人字段",
            "updated_by": "更新人字段",
            "amount": "金额字段",
            "price": "价格字段",
            "quantity": "数量字段",
            "description": "描述字段",
            "remark": "备注字段"
        }
    
    def inject_table_structure_semantics(
        self,
        table_ids: Optional[List[str]] = None,
        table_names: Optional[List[str]] = None
    ) -> List[TableStructureInfo]:
        """
        注入表结构语义信息
        
        Args:
            table_ids: 表ID列表
            table_names: 表名列表
            
        Returns:
            表结构信息列表
        """
        try:
            tables_info = []
            
            if table_ids:
                for table_id in table_ids:
                    table_info = self._get_table_structure_by_id(table_id)
                    if table_info:
                        # 增强业务含义
                        enhanced_info = self._enhance_business_meaning(table_info)
                        tables_info.append(enhanced_info)
            
            elif table_names:
                for table_name in table_names:
                    table_info = self._get_table_structure_by_name(table_name)
                    if table_info:
                        # 增强业务含义
                        enhanced_info = self._enhance_business_meaning(table_info)
                        tables_info.append(enhanced_info)
            
            return tables_info
            
        except Exception as e:
            logger.error(f"表结构语义注入失败: {str(e)}", exc_info=True)
            return []
    
    def _get_table_structure_by_id(self, table_id: str) -> Optional[TableStructureInfo]:
        """根据表ID获取表结构信息"""
        try:
            # 这里应该查询数据库获取表结构
            # 暂时返回模拟数据
            return TableStructureInfo(
                table_name=f"table_{table_id}",
                fields=[
                    FieldInfo(
                        name="id",
                        data_type=DataType.INTEGER,
                        is_nullable=False,
                        default_value=None,
                        comment="主键ID",
                        constraints=[ConstraintType.PRIMARY_KEY, ConstraintType.NOT_NULL]
                    ),
                    FieldInfo(
                        name="name",
                        data_type=DataType.STRING,
                        is_nullable=False,
                        default_value=None,
                        comment="名称",
                        constraints=[ConstraintType.NOT_NULL]
                    )
                ],
                primary_keys=["id"],
                foreign_keys=[],
                indexes=[{"name": "idx_name", "fields": ["name"], "unique": False}],
                comment=f"表{table_id}的注释"
            )
        except Exception as e:
            logger.error(f"获取表结构失败: {str(e)}")
            return None
    
    def _get_table_structure_by_name(self, table_name: str) -> Optional[TableStructureInfo]:
        """根据表名获取表结构信息"""
        try:
            # 这里应该查询数据库获取表结构
            # 暂时返回模拟数据
            return TableStructureInfo(
                table_name=table_name,
                fields=[
                    FieldInfo(
                        name="id",
                        data_type=DataType.INTEGER,
                        is_nullable=False,
                        default_value=None,
                        comment="主键ID",
                        constraints=[ConstraintType.PRIMARY_KEY, ConstraintType.NOT_NULL]
                    )
                ],
                primary_keys=["id"],
                foreign_keys=[],
                indexes=[],
                comment=f"表{table_name}的注释"
            )
        except Exception as e:
            logger.error(f"获取表结构失败: {str(e)}")
            return None
    
    def _enhance_business_meaning(self, table_info: TableStructureInfo) -> TableStructureInfo:
        """增强表结构的业务含义"""
        try:
            # 推断表的业务含义
            table_info.business_meaning = self._infer_table_business_meaning(table_info.table_name)
            
            # 推断字段的业务含义
            for field in table_info.fields:
                field.business_meaning = self._infer_field_business_meaning(field)
            
            return table_info
            
        except Exception as e:
            logger.error(f"增强业务含义失败: {str(e)}")
            return table_info
    
    def _infer_table_business_meaning(self, table_name: str) -> str:
        """推断表的业务含义"""
        table_name_lower = table_name.lower()
        
        if "user" in table_name_lower:
            return "用户信息表，存储用户基本信息"
        elif "order" in table_name_lower:
            return "订单信息表，存储订单相关数据"
        elif "product" in table_name_lower:
            return "产品信息表，存储产品基本信息"
        elif "customer" in table_name_lower:
            return "客户信息表，存储客户相关数据"
        elif "log" in table_name_lower:
            return "日志表，记录系统操作日志"
        else:
            return f"业务数据表：{table_name}"
    
    def _infer_field_business_meaning(self, field: FieldInfo) -> str:
        """推断字段的业务含义"""
        field_name_lower = field.name.lower()
        
        # 基于字段名模式匹配
        for pattern, meaning in self.field_patterns.items():
            if pattern in field_name_lower:
                return meaning
        
        # 基于数据类型推断
        type_meaning = self.data_type_semantics.get(field.data_type, "")
        
        # 基于约束推断
        constraint_meanings = []
        if ConstraintType.PRIMARY_KEY in field.constraints:
            constraint_meanings.append("主键字段")
        if ConstraintType.FOREIGN_KEY in field.constraints:
            constraint_meanings.append("外键字段")
        if ConstraintType.UNIQUE in field.constraints:
            constraint_meanings.append("唯一约束字段")
        
        meanings = [type_meaning] + constraint_meanings
        return "，".join(filter(None, meanings)) or f"字段：{field.name}"
    
    def generate_semantic_context(self, tables_info: List[TableStructureInfo]) -> str:
        """生成表结构语义上下文"""
        if not tables_info:
            return "无表结构信息"
        
        context_parts = []
        
        for table_info in tables_info:
            table_context = [
                f"表名: {table_info.table_name}",
                f"业务含义: {table_info.business_meaning or '未知'}",
                f"字段数量: {len(table_info.fields)}",
                f"主键: {', '.join(table_info.primary_keys)}",
                f"外键数量: {len(table_info.foreign_keys)}",
                f"索引数量: {len(table_info.indexes)}"
            ]
            
            # 添加字段详情
            field_details = []
            for field in table_info.fields:
                field_detail = f"{field.name}({field.data_type.value})"
                if not field.is_nullable:
                    field_detail += " NOT NULL"
                if field.business_meaning:
                    field_detail += f" - {field.business_meaning}"
                field_details.append(field_detail)
            
            table_context.append(f"字段: {'; '.join(field_details)}")
            context_parts.append("\n".join(table_context))
        
        return "\n\n".join(context_parts)
    
    def analyze_table_relationships(self, tables_info: List[TableStructureInfo]) -> Dict[str, Any]:
        """分析表之间的关系"""
        relationships = {
            "foreign_key_relations": [],
            "potential_joins": [],
            "table_hierarchy": {}
        }
        
        try:
            # 分析外键关系
            for table_info in tables_info:
                for fk in table_info.foreign_keys:
                    relationships["foreign_key_relations"].append({
                        "from_table": table_info.table_name,
                        "from_field": fk.get("field"),
                        "to_table": fk.get("referenced_table"),
                        "to_field": fk.get("referenced_field")
                    })
            
            # 分析潜在的JOIN关系
            table_names = [t.table_name for t in tables_info]
            for i, table1 in enumerate(tables_info):
                for j, table2 in enumerate(tables_info):
                    if i >= j:
                        continue
                    
                    # 查找同名字段（可能的关联字段）
                    common_fields = self._find_common_fields(table1, table2)
                    if common_fields:
                        relationships["potential_joins"].append({
                            "table1": table1.table_name,
                            "table2": table2.table_name,
                            "common_fields": common_fields
                        })
            
            return relationships
            
        except Exception as e:
            logger.error(f"分析表关系失败: {str(e)}")
            return relationships
    
    def _find_common_fields(self, table1: TableStructureInfo, table2: TableStructureInfo) -> List[str]:
        """查找两个表的共同字段"""
        fields1 = {f.name for f in table1.fields}
        fields2 = {f.name for f in table2.fields}
        return list(fields1.intersection(fields2))