"""
SQL安全校验和字段验证服务

实现SQL解析器进行语法和安全验证，验证所有引用的表和字段在数据库中存在，
添加危险操作检测和SQL注入防护，创建查询复杂度分析和资源限制。
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
from sqlparse import parse, sql
from sqlparse.tokens import Keyword, Name, Punctuation
import sqlparse

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """安全级别枚举"""
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


class SQLOperation(Enum):
    """SQL操作类型"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    TRUNCATE = "TRUNCATE"
    UNKNOWN = "UNKNOWN"


@dataclass
class SecurityViolation:
    """安全违规记录"""
    level: SecurityLevel
    type: str
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class TableReference:
    """表引用信息"""
    table_name: str
    alias: Optional[str] = None
    schema: Optional[str] = None


@dataclass
class FieldReference:
    """字段引用信息"""
    field_name: str
    table_name: Optional[str] = None
    table_alias: Optional[str] = None


@dataclass
class QueryComplexity:
    """查询复杂度分析"""
    table_count: int
    join_count: int
    subquery_count: int
    function_count: int
    condition_count: int
    complexity_score: float
    estimated_cost: str


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    security_level: SecurityLevel
    operation: SQLOperation
    violations: List[SecurityViolation]
    table_references: List[TableReference]
    field_references: List[FieldReference]
    complexity: QueryComplexity
    sanitized_sql: Optional[str] = None


class SQLSecurityValidator:
    """SQL安全校验器"""
    
    def __init__(self):
        self.dangerous_keywords = {
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE',
            'EXEC', 'EXECUTE', 'SP_', 'XP_', 'OPENROWSET', 'OPENDATASOURCE',
            'BULK', 'SHUTDOWN', 'BACKUP', 'RESTORE'
        }
        
        self.injection_patterns = [
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",  # OR 1=1, AND 1=1
            r"(\b(OR|AND)\s+['\"].*['\"])",    # OR 'x'='x'
            r"(;\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER))",  # 语句注入
            r"(UNION\s+SELECT)",               # UNION注入
            r"(--|\#|/\*)",                   # 注释注入
            r"(\bCHAR\s*\()",                 # CHAR函数注入
            r"(\bCONCAT\s*\()",               # CONCAT函数注入
            r"(\bSUBSTRING\s*\()",            # SUBSTRING函数注入
        ]
        
        self.max_complexity_score = 100.0
        self.max_table_count = 10
        self.max_join_count = 8
        self.max_subquery_count = 5
        
    def validate_sql(self, sql_query: str, available_tables: Dict[str, List[str]] = None) -> ValidationResult:
        """
        验证SQL查询的安全性和有效性
        
        Args:
            sql_query: SQL查询语句
            available_tables: 可用表及其字段 {table_name: [field_names]}
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            # 解析SQL
            parsed = parse(sql_query)[0]
            
            # 基础验证
            violations = []
            operation = self._detect_operation(parsed)
            
            # 安全检查
            violations.extend(self._check_dangerous_operations(parsed, operation))
            violations.extend(self._check_sql_injection(sql_query))
            
            # 解析表和字段引用
            table_references = self._extract_table_references(parsed)
            field_references = self._extract_field_references(parsed)
            
            # 存在性验证
            if available_tables:
                violations.extend(self._validate_table_existence(table_references, available_tables))
                violations.extend(self._validate_field_existence(field_references, table_references, available_tables))
            
            # 复杂度分析
            complexity = self._analyze_complexity(parsed)
            violations.extend(self._check_complexity_limits(complexity))
            
            # 确定安全级别
            security_level = self._determine_security_level(violations)
            
            # 生成清理后的SQL（如果需要）
            sanitized_sql = self._sanitize_sql(sql_query) if security_level in [SecurityLevel.WARNING, SecurityLevel.SAFE] else None
            
            return ValidationResult(
                is_valid=security_level != SecurityLevel.BLOCKED,
                security_level=security_level,
                operation=operation,
                violations=violations,
                table_references=table_references,
                field_references=field_references,
                complexity=complexity,
                sanitized_sql=sanitized_sql
            )
            
        except Exception as e:
            logger.error(f"SQL验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                security_level=SecurityLevel.BLOCKED,
                operation=SQLOperation.UNKNOWN,
                violations=[SecurityViolation(
                    level=SecurityLevel.BLOCKED,
                    type="PARSE_ERROR",
                    message=f"SQL解析失败: {str(e)}"
                )],
                table_references=[],
                field_references=[],
                complexity=QueryComplexity(0, 0, 0, 0, 0, 0.0, "UNKNOWN")
            )
    
    def _detect_operation(self, parsed: sql.Statement) -> SQLOperation:
        """检测SQL操作类型"""
        try:
            # 获取第一个有意义的关键字token
            for token in parsed.flatten():
                if token.ttype is Keyword and token.value.upper().strip() in [op.value for op in SQLOperation]:
                    return SQLOperation(token.value.upper().strip())
            
            # 如果没有找到，尝试从字符串中提取
            sql_text = str(parsed).strip().upper()
            for op in SQLOperation:
                if sql_text.startswith(op.value):
                    return op
                    
            return SQLOperation.UNKNOWN
        except Exception as e:
            logger.debug(f"操作检测失败: {e}")
            return SQLOperation.UNKNOWN
    
    def _check_dangerous_operations(self, parsed: sql.Statement, operation: SQLOperation) -> List[SecurityViolation]:
        """检查危险操作"""
        violations = []
        
        # 检查操作类型
        if operation in [SQLOperation.DROP, SQLOperation.DELETE, SQLOperation.TRUNCATE]:
            violations.append(SecurityViolation(
                level=SecurityLevel.BLOCKED,
                type="DANGEROUS_OPERATION",
                message=f"危险操作被禁止: {operation.value}",
                suggestion="仅允许SELECT查询操作"
            ))
        
        elif operation in [SQLOperation.INSERT, SQLOperation.UPDATE, SQLOperation.ALTER, SQLOperation.CREATE]:
            violations.append(SecurityViolation(
                level=SecurityLevel.DANGEROUS,
                type="WRITE_OPERATION",
                message=f"写操作需要特殊权限: {operation.value}",
                suggestion="确认是否有执行写操作的权限"
            ))
        
        # 检查危险关键词
        sql_text = str(parsed).upper()
        for keyword in self.dangerous_keywords:
            if keyword in sql_text:
                violations.append(SecurityViolation(
                    level=SecurityLevel.WARNING,
                    type="DANGEROUS_KEYWORD",
                    message=f"检测到潜在危险关键词: {keyword}",
                    suggestion="请确认该关键词的使用是否安全"
                ))
        
        return violations
    
    def _check_sql_injection(self, sql_query: str) -> List[SecurityViolation]:
        """检查SQL注入"""
        violations = []
        
        for pattern in self.injection_patterns:
            matches = re.finditer(pattern, sql_query, re.IGNORECASE)
            for match in matches:
                violations.append(SecurityViolation(
                    level=SecurityLevel.BLOCKED,
                    type="SQL_INJECTION",
                    message=f"检测到SQL注入模式: {match.group()}",
                    location=f"位置 {match.start()}-{match.end()}",
                    suggestion="请使用参数化查询避免SQL注入"
                ))
        
        return violations
    
    def _extract_table_references(self, parsed: sql.Statement) -> List[TableReference]:
        """提取表引用"""
        tables = []
        
        # 简化的表名提取逻辑 - 从SQL文本中提取
        sql_text = str(parsed).upper()
        
        # 查找FROM子句
        from_match = re.search(r'\bFROM\s+(\w+)', sql_text)
        if from_match:
            table_name = from_match.group(1).lower()
            tables.append(TableReference(table_name=table_name))
        
        # 查找JOIN子句
        join_matches = re.findall(r'\bJOIN\s+(\w+)', sql_text)
        for match in join_matches:
            table_name = match.lower()
            tables.append(TableReference(table_name=table_name))
        
        return tables
    
    def _extract_field_references(self, parsed: sql.Statement) -> List[FieldReference]:
        """提取字段引用"""
        fields = []
        sql_text = str(parsed)
        
        # 简化的字段提取逻辑 - 从SELECT子句中提取
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_text, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_part = select_match.group(1)
            
            # 处理SELECT *
            if '*' in select_part:
                fields.append(FieldReference(field_name='*'))
            else:
                # 分割字段名
                field_parts = [f.strip() for f in select_part.split(',')]
                for field_part in field_parts:
                    # 移除别名 (AS xxx)
                    field_part = re.sub(r'\s+AS\s+\w+', '', field_part, flags=re.IGNORECASE)
                    
                    # 检查是否有表前缀
                    if '.' in field_part:
                        table_part, field_name = field_part.rsplit('.', 1)
                        fields.append(FieldReference(
                            field_name=field_name.strip(),
                            table_name=table_part.strip()
                        ))
                    else:
                        fields.append(FieldReference(field_name=field_part.strip()))
        
        return fields
    
    def _validate_table_existence(self, table_refs: List[TableReference], available_tables: Dict[str, List[str]]) -> List[SecurityViolation]:
        """验证表存在性"""
        violations = []
        
        for table_ref in table_refs:
            if table_ref.table_name not in available_tables:
                violations.append(SecurityViolation(
                    level=SecurityLevel.BLOCKED,
                    type="TABLE_NOT_FOUND",
                    message=f"表不存在: {table_ref.table_name}",
                    suggestion=f"可用表: {', '.join(available_tables.keys())}"
                ))
        
        return violations
    
    def _validate_field_existence(self, field_refs: List[FieldReference], table_refs: List[TableReference], available_tables: Dict[str, List[str]]) -> List[SecurityViolation]:
        """验证字段存在性"""
        violations = []
        
        # 创建表名映射（包括别名）
        table_mapping = {}
        for table_ref in table_refs:
            table_mapping[table_ref.table_name] = table_ref.table_name
            if table_ref.alias:
                table_mapping[table_ref.alias] = table_ref.table_name
        
        for field_ref in field_refs:
            if field_ref.field_name == '*':  # 跳过通配符
                continue
                
            # 确定字段所属的表
            target_table = None
            if field_ref.table_name:
                target_table = table_mapping.get(field_ref.table_name)
            
            if target_table and target_table in available_tables:
                if field_ref.field_name not in available_tables[target_table]:
                    violations.append(SecurityViolation(
                        level=SecurityLevel.BLOCKED,
                        type="FIELD_NOT_FOUND",
                        message=f"字段不存在: {target_table}.{field_ref.field_name}",
                        suggestion=f"表 {target_table} 可用字段: {', '.join(available_tables[target_table])}"
                    ))
            elif not field_ref.table_name:
                # 字段没有指定表，检查所有表
                found = False
                for table_name, fields in available_tables.items():
                    if field_ref.field_name in fields:
                        found = True
                        break
                
                if not found:
                    violations.append(SecurityViolation(
                        level=SecurityLevel.BLOCKED,
                        type="FIELD_NOT_FOUND",
                        message=f"字段在任何表中都不存在: {field_ref.field_name}",
                        suggestion="请指定表名或检查字段名是否正确"
                    ))
        
        return violations
    
    def _analyze_complexity(self, parsed: sql.Statement) -> QueryComplexity:
        """分析查询复杂度"""
        table_count = 0
        join_count = 0
        subquery_count = 0
        function_count = 0
        condition_count = 0
        
        sql_text = str(parsed).upper()
        
        # 统计表数量（简化）
        table_count = sql_text.count('FROM') + sql_text.count('JOIN')
        
        # 统计JOIN数量
        join_count = (sql_text.count('JOIN') + 
                     sql_text.count('LEFT JOIN') + 
                     sql_text.count('RIGHT JOIN') + 
                     sql_text.count('INNER JOIN') + 
                     sql_text.count('OUTER JOIN'))
        
        # 统计子查询数量
        subquery_count = sql_text.count('(SELECT')
        
        # 统计函数数量
        function_count = (sql_text.count('COUNT(') + 
                         sql_text.count('SUM(') + 
                         sql_text.count('AVG(') + 
                         sql_text.count('MAX(') + 
                         sql_text.count('MIN('))
        
        # 统计条件数量
        condition_count = sql_text.count('WHERE') + sql_text.count('AND') + sql_text.count('OR')
        
        # 计算复杂度分数
        complexity_score = (
            table_count * 5 +
            join_count * 10 +
            subquery_count * 15 +
            function_count * 3 +
            condition_count * 2
        )
        
        # 估算成本
        if complexity_score < 20:
            estimated_cost = "LOW"
        elif complexity_score < 50:
            estimated_cost = "MEDIUM"
        elif complexity_score < 100:
            estimated_cost = "HIGH"
        else:
            estimated_cost = "VERY_HIGH"
        
        return QueryComplexity(
            table_count=table_count,
            join_count=join_count,
            subquery_count=subquery_count,
            function_count=function_count,
            condition_count=condition_count,
            complexity_score=complexity_score,
            estimated_cost=estimated_cost
        )
    
    def _check_complexity_limits(self, complexity: QueryComplexity) -> List[SecurityViolation]:
        """检查复杂度限制"""
        violations = []
        
        if complexity.table_count > self.max_table_count:
            violations.append(SecurityViolation(
                level=SecurityLevel.BLOCKED,
                type="COMPLEXITY_LIMIT",
                message=f"查询涉及表数量过多: {complexity.table_count} > {self.max_table_count}",
                suggestion="请简化查询或分解为多个查询"
            ))
        
        if complexity.join_count > self.max_join_count:
            violations.append(SecurityViolation(
                level=SecurityLevel.WARNING,
                type="COMPLEXITY_LIMIT",
                message=f"JOIN数量过多: {complexity.join_count} > {self.max_join_count}",
                suggestion="过多的JOIN可能影响性能"
            ))
        
        if complexity.subquery_count > self.max_subquery_count:
            violations.append(SecurityViolation(
                level=SecurityLevel.WARNING,
                type="COMPLEXITY_LIMIT",
                message=f"子查询数量过多: {complexity.subquery_count} > {self.max_subquery_count}",
                suggestion="考虑使用JOIN替代子查询"
            ))
        
        if complexity.complexity_score > self.max_complexity_score:
            violations.append(SecurityViolation(
                level=SecurityLevel.BLOCKED,
                type="COMPLEXITY_LIMIT",
                message=f"查询复杂度过高: {complexity.complexity_score} > {self.max_complexity_score}",
                suggestion="请简化查询逻辑"
            ))
        
        return violations
    
    def _determine_security_level(self, violations: List[SecurityViolation]) -> SecurityLevel:
        """确定安全级别"""
        if any(v.level == SecurityLevel.BLOCKED for v in violations):
            return SecurityLevel.BLOCKED
        elif any(v.level == SecurityLevel.DANGEROUS for v in violations):
            return SecurityLevel.DANGEROUS
        elif any(v.level == SecurityLevel.WARNING for v in violations):
            return SecurityLevel.WARNING
        else:
            return SecurityLevel.SAFE
    
    def _sanitize_sql(self, sql_query: str) -> str:
        """清理SQL查询"""
        # 移除注释
        sanitized = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
        sanitized = re.sub(r'/\*.*?\*/', '', sanitized, flags=re.DOTALL)
        
        # 标准化空白字符
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized


class SQLSecurityService:
    """SQL安全服务"""
    
    def __init__(self):
        self.validator = SQLSecurityValidator()
        self.validation_cache = {}  # 简单的内存缓存
    
    async def validate_and_secure_sql(self, sql_query: str, data_source_id: int = None) -> ValidationResult:
        """
        验证并保护SQL查询
        
        Args:
            sql_query: SQL查询语句
            data_source_id: 数据源ID，用于获取可用表和字段
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            # 检查缓存
            cache_key = f"{hash(sql_query)}_{data_source_id}"
            if cache_key in self.validation_cache:
                logger.info("使用缓存的SQL验证结果")
                return self.validation_cache[cache_key]
            
            # 获取可用表和字段（这里需要集成数据表服务）
            available_tables = await self._get_available_tables(data_source_id) if data_source_id else None
            
            # 执行验证
            result = self.validator.validate_sql(sql_query, available_tables)
            
            # 缓存结果
            self.validation_cache[cache_key] = result
            
            # 记录验证日志
            logger.info(f"SQL验证完成: 安全级别={result.security_level.value}, 违规数量={len(result.violations)}")
            
            return result
            
        except Exception as e:
            logger.error(f"SQL安全验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                security_level=SecurityLevel.BLOCKED,
                operation=SQLOperation.UNKNOWN,
                violations=[SecurityViolation(
                    level=SecurityLevel.BLOCKED,
                    type="VALIDATION_ERROR",
                    message=f"验证过程出错: {str(e)}"
                )],
                table_references=[],
                field_references=[],
                complexity=QueryComplexity(0, 0, 0, 0, 0, 0.0, "UNKNOWN")
            )
    
    async def _get_available_tables(self, data_source_id: int) -> Dict[str, List[str]]:
        """
        获取数据源的可用表和字段
        
        Args:
            data_source_id: 数据源ID
            
        Returns:
            Dict[str, List[str]]: 表名到字段列表的映射
        """
        # TODO: 集成数据表服务获取真实的表和字段信息
        # 这里返回模拟数据
        return {
            "users": ["id", "name", "email", "created_at"],
            "orders": ["id", "user_id", "amount", "status", "created_at"],
            "products": ["id", "name", "price", "category_id"]
        }
    
    def get_security_report(self, result: ValidationResult) -> Dict[str, Any]:
        """
        生成安全报告
        
        Args:
            result: 验证结果
            
        Returns:
            Dict[str, Any]: 安全报告
        """
        return {
            "summary": {
                "is_valid": result.is_valid,
                "security_level": result.security_level.value,
                "operation": result.operation.value,
                "violation_count": len(result.violations)
            },
            "violations": [
                {
                    "level": v.level.value,
                    "type": v.type,
                    "message": v.message,
                    "location": v.location,
                    "suggestion": v.suggestion
                }
                for v in result.violations
            ],
            "references": {
                "tables": [
                    {
                        "name": t.table_name,
                        "alias": t.alias,
                        "schema": t.schema
                    }
                    for t in result.table_references
                ],
                "fields": [
                    {
                        "name": f.field_name,
                        "table": f.table_name,
                        "table_alias": f.table_alias
                    }
                    for f in result.field_references
                ]
            },
            "complexity": {
                "score": result.complexity.complexity_score,
                "estimated_cost": result.complexity.estimated_cost,
                "table_count": result.complexity.table_count,
                "join_count": result.complexity.join_count,
                "subquery_count": result.complexity.subquery_count,
                "function_count": result.complexity.function_count,
                "condition_count": result.complexity.condition_count
            },
            "sanitized_sql": result.sanitized_sql
        }