#!/usr/bin/env python3
"""
为已存在的字典创建字典项
"""

import requests
import json

# API 基础配置
API_BASE = "http://localhost:8000/api"

def get_dictionaries():
    """获取所有字典"""
    response = requests.get(f"{API_BASE}/dictionaries/")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 获取字典列表失败: {response.status_code} - {response.text}")
        return []

def create_dictionary_item(dictionary_id, item_key, item_value, description, sort_order=0, status=True):
    """创建字典项"""
    data = {
        "dictionary_id": dictionary_id,
        "item_key": item_key,
        "item_value": item_value,
        "description": description,
        "sort_order": sort_order,
        "status": status
    }
    
    response = requests.post(f"{API_BASE}/dictionaries/{dictionary_id}/items", json=data)
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"  ✅ 创建字典项成功: {item_key} -> {item_value}")
        return result
    else:
        print(f"  ❌ 创建字典项失败: {item_key} - {response.status_code} - {response.text}")
        return None

def main():
    print("🚀 开始为已存在的字典创建字典项...")
    print("=" * 50)
    
    # 获取所有字典
    dictionaries = get_dictionaries()
    if not dictionaries:
        print("❌ 没有找到字典，请先创建字典")
        return
    
    # 创建字典映射
    dict_map = {d['code']: d['id'] for d in dictionaries}
    print(f"📋 找到 {len(dictionaries)} 个字典:")
    for d in dictionaries:
        print(f"  - {d['name']} ({d['code']})")
    
    # 1. 数据源类型字典项
    if 'datasource_type' in dict_map:
        print("\n📊 创建数据源类型字典项...")
        dict_id = dict_map['datasource_type']
        datasource_types = [
            ("DATABASE", "数据库", "关系型数据库数据源", 1),
            ("FILE", "文件", "文件类型数据源", 2),
            ("API", "接口", "API接口数据源", 3),
            ("CLOUD", "云存储", "云存储数据源", 4)
        ]
        
        for key, value, desc, order in datasource_types:
            create_dictionary_item(dict_id, key, value, desc, order)
    
    # 2. 数据库类型字典项
    if 'database_type' in dict_map:
        print("\n🗄️ 创建数据库类型字典项...")
        dict_id = dict_map['database_type']
        db_types = [
            ("MySQL", "MySQL", "MySQL数据库", 1),
            ("PostgreSQL", "PostgreSQL", "PostgreSQL数据库", 2),
            ("Oracle", "Oracle", "Oracle数据库", 3),
            ("SQL Server", "SQL Server", "Microsoft SQL Server数据库", 4),
            ("SQLite", "SQLite", "SQLite数据库", 5)
        ]
        
        for key, value, desc, order in db_types:
            create_dictionary_item(dict_id, key, value, desc, order)
    
    # 3. 数据表状态字典项
    if 'table_status' in dict_map:
        print("\n📋 创建数据表状态字典项...")
        dict_id = dict_map['table_status']
        table_statuses = [
            ("ACTIVE", "活跃", "正常使用中的数据表", 1),
            ("INACTIVE", "非活跃", "暂停使用的数据表", 2),
            ("ARCHIVED", "已归档", "已归档的历史数据表", 3),
            ("DEPRECATED", "已废弃", "已废弃不再使用的数据表", 4)
        ]
        
        for key, value, desc, order in table_statuses:
            create_dictionary_item(dict_id, key, value, desc, order)
    
    # 4. 字段类型字典项
    if 'field_type' in dict_map:
        print("\n🔤 创建字段类型字典项...")
        dict_id = dict_map['field_type']
        field_types = [
            ("VARCHAR", "字符串", "可变长度字符串", 1),
            ("INT", "整数", "整数类型", 2),
            ("DECIMAL", "小数", "精确小数类型", 3),
            ("DATE", "日期", "日期类型", 4),
            ("DATETIME", "日期时间", "日期时间类型", 5),
            ("TEXT", "文本", "长文本类型", 6),
            ("BOOLEAN", "布尔", "布尔类型", 7)
        ]
        
        for key, value, desc, order in field_types:
            create_dictionary_item(dict_id, key, value, desc, order)
    
    # 5. 用户状态字典项
    if 'user_status' in dict_map:
        print("\n👤 创建用户状态字典项...")
        dict_id = dict_map['user_status']
        user_statuses = [
            ("ACTIVE", "活跃", "正常活跃用户", 1),
            ("INACTIVE", "非活跃", "长期未登录用户", 2),
            ("SUSPENDED", "暂停", "账户被暂停的用户", 3),
            ("DELETED", "已删除", "已删除的用户账户", 4)
        ]
        
        for key, value, desc, order in user_statuses:
            create_dictionary_item(dict_id, key, value, desc, order)
    
    # 6. 订单状态字典项
    if 'order_status' in dict_map:
        print("\n📦 创建订单状态字典项...")
        dict_id = dict_map['order_status']
        order_statuses = [
            ("PENDING", "待处理", "新创建的订单，等待处理", 1),
            ("CONFIRMED", "已确认", "订单已确认，准备发货", 2),
            ("SHIPPED", "已发货", "订单已发货，在途中", 3),
            ("DELIVERED", "已送达", "订单已成功送达", 4),
            ("CANCELLED", "已取消", "订单被取消", 5),
            ("REFUNDED", "已退款", "订单已退款", 6)
        ]
        
        for key, value, desc, order in order_statuses:
            create_dictionary_item(dict_id, key, value, desc, order)
    
    # 7. 数据同步状态字典项
    if 'sync_status' in dict_map:
        print("\n🔄 创建数据同步状态字典项...")
        dict_id = dict_map['sync_status']
        sync_statuses = [
            ("PENDING", "等待中", "同步任务等待执行", 1),
            ("RUNNING", "执行中", "同步任务正在执行", 2),
            ("SUCCESS", "成功", "同步任务执行成功", 3),
            ("FAILED", "失败", "同步任务执行失败", 4),
            ("CANCELLED", "已取消", "同步任务被取消", 5)
        ]
        
        for key, value, desc, order in sync_statuses:
            create_dictionary_item(dict_id, key, value, desc, order)
    
    print("\n" + "=" * 50)
    print("🎉 字典项创建完成！")
    print("\n🌐 现在可以访问前端页面查看字典数据：")
    print("   http://localhost:5173/#/data-prep/dictionaries")

if __name__ == "__main__":
    main()