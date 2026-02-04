"""
表发现服务
实现从数据源数据库中发现表结构和同步表结构的功能
"""
import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy import create_engine, text, inspect, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from src.models.data_source_model import DataSource
from src.models.data_preparation_model import DataTable, TableField
from src.services.data_table_service import DataTableService
from src.utils.encryption import decrypt_password
from datetime import datetime

# 创建日志记录器
logger = logging.getLogger(__name__)

class TableDiscoveryService:
    """
    表发现服务类
    提供从数据源数据库中发现表结构和同步表结构的功能
    """
    
    def __init__(self):
        self.data_table_service = DataTableService()
    
    def create_connection_string(self, data_source: DataSource) -> str:
        """
        根据数据源配置创建数据库连接字符串
        
        Args:
            data_source: 数据源对象
            
        Returns:
            str: 数据库连接字符串
        """
        logger.info(f"Creating connection string for {data_source.name}: host={data_source.host}, port={data_source.port}, db={data_source.database_name}, user={data_source.username}")
        
        # 解密密码
        password = decrypt_password(data_source.password) if data_source.password else ""
        
        if data_source.db_type.upper() == 'MYSQL':
            return f"mysql+pymysql://{data_source.username}:{password}@{data_source.host}:{data_source.port}/{data_source.database_name}"
        elif data_source.db_type.upper() == 'SQLSERVER':
            if data_source.auth_type == 'WINDOWS_AUTH':
                return f"mssql+pyodbc://{data_source.host}:{data_source.port}/{data_source.database_name}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
            else:
                return f"mssql+pyodbc://{data_source.username}:{password}@{data_source.host}:{data_source.port}/{data_source.database_name}?driver=ODBC+Driver+17+for+SQL+Server"
        elif data_source.db_type.upper() == 'POSTGRESQL':
            return f"postgresql://{data_source.username}:{password}@{data_source.host}:{data_source.port}/{data_source.database_name}"
        else:
            raise ValueError(f"不支持的数据库类型: {data_source.db_type}")
    
    def discover_tables(self, data_source: DataSource) -> List[Dict]:
        """
        从数据源中发现所有表
        
        Args:
            data_source: 数据源对象
            
        Returns:
            List[Dict]: 表信息列表，每个元素包含表名、注释等信息
        """
        logger.info(f"Discovering tables from data source: {data_source.name} ({data_source.db_type})")
        
        try:
            # 创建数据库连接
            connection_string = self.create_connection_string(data_source)
            engine = create_engine(connection_string)
            
            # 使用SQLAlchemy的inspect功能获取表信息
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            tables = []
            for table_name in table_names:
                try:
                    # 获取表注释
                    table_comment = None
                    if data_source.db_type.upper() == 'MYSQL':
                        with engine.connect() as conn:
                            result = conn.execute(text(f"""
                                SELECT TABLE_COMMENT 
                                FROM INFORMATION_SCHEMA.TABLES 
                                WHERE TABLE_SCHEMA = '{data_source.database_name}' 
                                AND TABLE_NAME = '{table_name}'
                            """))
                            row = result.fetchone()
                            if row:
                                table_comment = row[0] if row[0] else None
                    
                    # 获取表行数（估算）
                    row_count = 0
                    try:
                        with engine.connect() as conn:
                            result = conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                            row_count = result.scalar()
                    except Exception as e:
                        logger.warning(f"Failed to get row count for table {table_name}: {str(e)}")
                    
                    tables.append({
                        'table_name': table_name,
                        'comment': table_comment,
                        'row_count': row_count,
                        'schema': data_source.database_name
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get details for table {table_name}: {str(e)}")
                    # 仍然添加基本信息
                    tables.append({
                        'table_name': table_name,
                        'comment': None,
                        'row_count': 0,
                        'schema': data_source.database_name
                    })
            
            logger.info(f"Discovered {len(tables)} tables from data source {data_source.name}")
            return tables
            
        except Exception as e:
            logger.error(f"Failed to discover tables from data source {data_source.name}: {str(e)}")
            raise
        finally:
            if 'engine' in locals():
                engine.dispose()
    
    def get_table_structure(self, data_source: DataSource, table_name: str) -> Dict:
        """
        获取指定表的结构信息
        
        Args:
            data_source: 数据源对象
            table_name: 表名
            
        Returns:
            Dict: 表结构信息，包含字段列表
        """
        logger.info(f"Getting table structure for {table_name} from data source {data_source.name}")
        
        try:
            # 创建数据库连接
            connection_string = self.create_connection_string(data_source)
            engine = create_engine(connection_string)
            
            # 使用SQLAlchemy的inspect功能获取表结构
            inspector = inspect(engine)
            columns = inspector.get_columns(table_name)
            primary_keys = inspector.get_pk_constraint(table_name)['constrained_columns']
            
            # 转换字段信息
            fields = []
            for i, column in enumerate(columns):
                field_info = {
                    'name': column['name'],
                    'data_type': str(column['type']),
                    'is_nullable': column['nullable'],
                    'is_primary_key': column['name'] in primary_keys,
                    'default_value': column.get('default'),
                    'comment': column.get('comment'),
                    'sort_order': i + 1
                }
                fields.append(field_info)
            
            # 获取表注释和行数
            table_comment = None
            row_count = 0
            
            if data_source.db_type.upper() == 'MYSQL':
                with engine.connect() as conn:
                    # 获取表注释
                    result = conn.execute(text(f"""
                        SELECT TABLE_COMMENT 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = '{data_source.database_name}' 
                        AND TABLE_NAME = '{table_name}'
                    """))
                    row = result.fetchone()
                    if row:
                        table_comment = row[0] if row[0] else None
                    
                    # 获取行数
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                        row_count = result.scalar()
                    except Exception as e:
                        logger.warning(f"Failed to get row count for table {table_name}: {str(e)}")
            
            table_structure = {
                'table_name': table_name,
                'comment': table_comment,
                'row_count': row_count,
                'field_count': len(fields),
                'fields': fields
            }
            
            logger.info(f"Retrieved structure for table {table_name}: {len(fields)} fields, {row_count} rows")
            return table_structure
            
        except Exception as e:
            logger.error(f"Failed to get table structure for {table_name}: {str(e)}")
            raise
        finally:
            if 'engine' in locals():
                engine.dispose()
    
    def sync_table_structure(self, db: Session, data_source: DataSource, table_name: str) -> DataTable:
        """
        同步表结构到本地数据库
        
        Args:
            db: 数据库会话
            data_source: 数据源对象
            table_name: 表名
            
        Returns:
            DataTable: 同步后的数据表对象
        """
        logger.info(f"Syncing table structure for {table_name} from data source {data_source.name}")
        
        try:
            # 获取表结构
            table_structure = self.get_table_structure(data_source, table_name)
            
            # 检查表是否已存在
            existing_table = self.data_table_service.get_table_by_name_and_source(
                db, table_name, str(data_source.id)
            )
            
            if existing_table:
                # 更新现有表
                logger.info(f"Updating existing table {table_name}")
                
                # 更新表信息
                existing_table.description = table_structure['comment']
                existing_table.row_count = table_structure['row_count']
                existing_table.field_count = table_structure['field_count']
                existing_table.updated_at = datetime.now()
                existing_table.last_sync_time = datetime.now()
                
                # 更新字段信息
                self.data_table_service.update_table_columns(
                    db, str(existing_table.id), table_structure['fields']
                )
                
                db.commit()
                db.refresh(existing_table)
                
                logger.info(f"Table {table_name} updated successfully")
                return existing_table
            else:
                # 创建新表
                logger.info(f"Creating new table {table_name}")
                
                now = datetime.now()
                new_table = DataTable(
                    data_source_id=str(data_source.id),
                    table_name=table_name,
                    display_name=table_name,
                    description=table_structure['comment'],
                    data_mode='DIRECT_QUERY',
                    row_count=table_structure['row_count'],
                    field_count=table_structure['field_count'],
                    status=True,
                    created_by='system',
                    created_at=now,
                    updated_at=now,
                    last_sync_time=now
                )
                
                db.add(new_table)
                db.flush()  # 获取ID但不提交
                
                # 创建字段信息
                self.data_table_service.create_table_columns(
                    db, str(new_table.id), table_structure['fields']
                )
                
                db.commit()
                db.refresh(new_table)
                
                logger.info(f"Table {table_name} created successfully")
                return new_table
                
        except Exception as e:
            logger.error(f"Failed to sync table structure for {table_name}: {str(e)}")
            db.rollback()
            raise
    
    def batch_sync_tables(self, db: Session, data_source: DataSource, table_names: List[str]) -> List[DataTable]:
        """
        批量同步多个表的结构
        
        Args:
            db: 数据库会话
            data_source: 数据源对象
            table_names: 表名列表
            
        Returns:
            List[DataTable]: 同步后的数据表对象列表
        """
        logger.info(f"Batch syncing {len(table_names)} tables from data source {data_source.name}")
        
        synced_tables = []
        failed_tables = []
        
        for table_name in table_names:
            try:
                synced_table = self.sync_table_structure(db, data_source, table_name)
                synced_tables.append(synced_table)
                logger.info(f"Successfully synced table: {table_name}")
            except Exception as e:
                logger.error(f"Failed to sync table {table_name}: {str(e)}")
                failed_tables.append(table_name)
        
        logger.info(f"Batch sync completed: {len(synced_tables)} succeeded, {len(failed_tables)} failed")
        
        if failed_tables:
            logger.warning(f"Failed tables: {', '.join(failed_tables)}")
        
        return synced_tables
    
    def test_connection(self, data_source: DataSource) -> Tuple[bool, str]:
        """
        测试数据源连接
        
        Args:
            data_source: 数据源对象
            
        Returns:
            Tuple[bool, str]: (连接是否成功, 消息)
        """
        logger.info(f"Testing connection to data source: {data_source.name}")
        
        try:
            connection_string = self.create_connection_string(data_source)
            engine = create_engine(connection_string)
            
            # 尝试连接并执行简单查询
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info(f"Connection test successful for data source: {data_source.name}")
            return True, "连接成功"
            
        except Exception as e:
            error_msg = f"连接失败: {str(e)}"
            logger.error(f"Connection test failed for data source {data_source.name}: {error_msg}")
            return False, error_msg
        finally:
            if 'engine' in locals():
                engine.dispose()