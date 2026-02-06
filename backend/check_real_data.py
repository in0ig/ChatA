"""检查数据库中的真实数据"""
from src.database import get_db
from sqlalchemy import text

db = next(get_db())

# 检查数据源
result = db.execute(text('SELECT COUNT(*) as count FROM data_sources'))
ds_count = result.fetchone()[0]
print(f'数据源数量: {ds_count}')

if ds_count > 0:
    result = db.execute(text('SELECT id, name, db_type FROM data_sources LIMIT 3'))
    print('\n数据源列表:')
    for row in result:
        print(f'  - ID: {row[0]}, 名称: {row[1]}, 类型: {row[2]}')

# 检查数据表
result = db.execute(text('SELECT COUNT(*) as count FROM data_tables'))
dt_count = result.fetchone()[0]
print(f'\n数据表数量: {dt_count}')

if dt_count > 0:
    result = db.execute(text('SELECT id, table_name, data_source_id FROM data_tables LIMIT 5'))
    print('\n数据表列表:')
    for row in result:
        print(f'  - ID: {row[0]}, 表名: {row[1]}, 数据源ID: {row[2]}')

db.close()
