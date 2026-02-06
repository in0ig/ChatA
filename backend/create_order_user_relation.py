"""创建订单表和用户表的关联关系"""
from src.database import get_db
from sqlalchemy import text
from datetime import datetime
import uuid

db = next(get_db())

try:
    # 1. 查找订单表和用户表
    result = db.execute(text("""
        SELECT id, table_name, data_source_id 
        FROM data_tables 
        WHERE table_name IN ('orders', 'users')
    """))
    tables = result.fetchall()
    
    print(f"找到 {len(tables)} 个表:")
    for table in tables:
        print(f"  - ID: {table[0]}, 表名: {table[1]}, 数据源ID: {table[2]}")
    
    # 找到订单表和用户表
    orders_table = None
    users_table = None
    for table in tables:
        if table[1] == 'orders':
            orders_table = table
        elif table[1] == 'users':
            users_table = table
    
    if not orders_table or not users_table:
        print("\n错误: 未找到订单表或用户表")
        exit(1)
    
    print(f"\n订单表 ID: {orders_table[0]}")
    print(f"用户表 ID: {users_table[0]}")
    
    # 2. 查找订单表的 user_id 字段
    result = db.execute(text("""
        SELECT id, field_name, data_type 
        FROM table_fields 
        WHERE table_id = :table_id AND field_name = 'user_id'
    """), {"table_id": orders_table[0]})
    orders_user_id_field = result.fetchone()
    
    if not orders_user_id_field:
        print("\n错误: 订单表中未找到 user_id 字段")
        exit(1)
    
    print(f"\n订单表 user_id 字段 ID: {orders_user_id_field[0]}, 类型: {orders_user_id_field[2]}")
    
    # 3. 查找用户表的 id 字段
    result = db.execute(text("""
        SELECT id, field_name, data_type 
        FROM table_fields 
        WHERE table_id = :table_id AND field_name = 'id'
    """), {"table_id": users_table[0]})
    users_id_field = result.fetchone()
    
    if not users_id_field:
        print("\n错误: 用户表中未找到 id 字段")
        exit(1)
    
    print(f"用户表 id 字段 ID: {users_id_field[0]}, 类型: {users_id_field[2]}")
    
    # 4. 检查是否已存在关联
    result = db.execute(text("""
        SELECT id, relation_name 
        FROM table_relations 
        WHERE primary_table_id = :primary_table_id 
        AND foreign_table_id = :foreign_table_id
    """), {
        "primary_table_id": orders_table[0],
        "foreign_table_id": users_table[0]
    })
    existing_relation = result.fetchone()
    
    if existing_relation:
        print(f"\n关联已存在: ID={existing_relation[0]}, 名称={existing_relation[1]}")
    else:
        # 5. 创建关联关系
        relation_id = str(uuid.uuid4())
        now = datetime.now()
        
        db.execute(text("""
            INSERT INTO table_relations (
                id, relation_name, 
                primary_table_id, primary_field_id,
                foreign_table_id, foreign_field_id,
                join_type, description, status,
                created_by, created_at, updated_at
            ) VALUES (
                :id, :relation_name,
                :primary_table_id, :primary_field_id,
                :foreign_table_id, :foreign_field_id,
                :join_type, :description, :status,
                :created_by, :created_at, :updated_at
            )
        """), {
            "id": relation_id,
            "relation_name": "订单-用户关联",
            "primary_table_id": orders_table[0],
            "primary_field_id": orders_user_id_field[0],
            "foreign_table_id": users_table[0],
            "foreign_field_id": users_id_field[0],
            "join_type": "LEFT",
            "description": "订单表通过 user_id 关联到用户表的 id",
            "status": True,
            "created_by": "system",
            "created_at": now,
            "updated_at": now
        })
        
        db.commit()
        print(f"\n✅ 成功创建关联关系!")
        print(f"关联 ID: {relation_id}")
        print(f"关联名称: 订单-用户关联")
        print(f"主表: orders (user_id)")
        print(f"从表: users (id)")
        print(f"连接类型: LEFT JOIN")
    
    # 6. 显示所有关联关系
    result = db.execute(text("""
        SELECT 
            tr.id, tr.relation_name, tr.join_type,
            dt1.table_name as primary_table,
            tf1.field_name as primary_field,
            dt2.table_name as foreign_table,
            tf2.field_name as foreign_field
        FROM table_relations tr
        JOIN data_tables dt1 ON tr.primary_table_id = dt1.id
        JOIN table_fields tf1 ON tr.primary_field_id = tf1.id
        JOIN data_tables dt2 ON tr.foreign_table_id = dt2.id
        JOIN table_fields tf2 ON tr.foreign_field_id = tf2.id
    """))
    
    relations = result.fetchall()
    print(f"\n当前所有关联关系 ({len(relations)} 个):")
    for rel in relations:
        print(f"  - {rel[1]}: {rel[3]}.{rel[4]} -> {rel[5]}.{rel[6]} ({rel[2]} JOIN)")

except Exception as e:
    print(f"\n错误: {str(e)}")
    db.rollback()
finally:
    db.close()
