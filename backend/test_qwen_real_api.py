#!/usr/bin/env python3
"""
阿里云Qwen模型实际API调用测试
使用提供的API密钥和配置进行真实调用测试
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.ai_model_service import QwenCloudAdapter, ModelType
from src.config.ai_config import AIConfig

# 设置环境变量
os.environ["DASHSCOPE_API_KEY"] = "sk-399d0eb35c494883afdc3ca41e2ce214"
os.environ["ALIYUN_API_URL"] = "https://dashscope.aliyuncs.com/api/v1"
os.environ["DASHSCOPE_MODEL"] = "qwen-plus-2025-09-11"


async def test_qwen_basic_generation():
    """测试基本的SQL生成功能"""
    print("🔄 测试基本SQL生成...")
    
    config = {
        'api_key': os.environ["DASHSCOPE_API_KEY"],
        'base_url': os.environ["ALIYUN_API_URL"],
        'model_name': os.environ["DASHSCOPE_MODEL"],
        'max_tokens': 1000,
        'temperature': 0.1,
        'retry_count': 3,
        'retry_delay': 1.0
    }
    
    adapter = QwenCloudAdapter(config)
    
    try:
        # 测试简单的SQL生成
        prompt = """
请根据以下信息生成SQL查询：

用户问题：查询所有活跃用户的姓名和邮箱

表结构：
- 表名：users
- 字段：id (int), name (varchar), email (varchar), status (varchar), created_at (datetime)

请生成标准的MySQL查询语句。
"""
        
        response = await adapter.generate(prompt)
        
        print(f"✅ 生成成功!")
        print(f"📊 Token使用量: {response.tokens_used}")
        print(f"⏱️  响应时间: {response.response_time:.2f}秒")
        print(f"🤖 模型类型: {response.model_type.value}")
        print(f"📝 生成内容:\n{response.content}")
        
        # 尝试提取SQL
        if hasattr(adapter, 'extract_sql_from_response'):
            sql = adapter.extract_sql_from_response(response.content)
            if sql:
                print(f"🔍 提取的SQL: {sql}")
            else:
                print("⚠️  未能提取到SQL语句")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False
    finally:
        await adapter.close()


async def test_qwen_stream_generation():
    """测试流式生成功能"""
    print("\n🔄 测试流式SQL生成...")
    
    config = {
        'api_key': os.environ["DASHSCOPE_API_KEY"],
        'base_url': os.environ["ALIYUN_API_URL"],
        'model_name': os.environ["DASHSCOPE_MODEL"],
        'max_tokens': 1000,
        'temperature': 0.1,
        'retry_count': 3,
        'retry_delay': 1.0
    }
    
    adapter = QwenCloudAdapter(config)
    
    try:
        prompt = """
请根据以下信息生成SQL查询：

用户问题：统计每个部门的员工数量，按数量降序排列

表结构：
- 表名：employees
- 字段：id (int), name (varchar), department (varchar), salary (decimal), hire_date (date)

请生成标准的MySQL查询语句，并解释查询逻辑。
"""
        
        print("📡 开始流式生成...")
        content_buffer = ""
        
        async for chunk in adapter.generate_stream(prompt):
            print(chunk, end='', flush=True)
            content_buffer += chunk
        
        print(f"\n\n✅ 流式生成完成!")
        print(f"📄 总内容长度: {len(content_buffer)} 字符")
        
        # 尝试提取SQL
        if hasattr(adapter, 'extract_sql_from_response'):
            sql = adapter.extract_sql_from_response(content_buffer)
            if sql:
                print(f"🔍 提取的SQL: {sql}")
        
        return True
        
    except Exception as e:
        print(f"❌ 流式测试失败: {str(e)}")
        return False
    finally:
        await adapter.close()


async def test_qwen_complex_query():
    """测试复杂查询生成"""
    print("\n🔄 测试复杂SQL生成...")
    
    config = {
        'api_key': os.environ["DASHSCOPE_API_KEY"],
        'base_url': os.environ["ALIYUN_API_URL"],
        'model_name': os.environ["DASHSCOPE_MODEL"],
        'max_tokens': 2000,
        'temperature': 0.1,
        'retry_count': 3,
        'retry_delay': 1.0
    }
    
    adapter = QwenCloudAdapter(config)
    
    try:
        prompt = """
请根据以下信息生成SQL查询：

用户问题：查询2023年每个月的销售额，以及与上个月相比的增长率

表结构：
- 表名：orders
- 字段：id (int), customer_id (int), order_date (date), total_amount (decimal), status (varchar)

- 表名：customers  
- 字段：id (int), name (varchar), email (varchar), city (varchar)

数据字典：
- status字段含义：'pending'(待处理), 'completed'(已完成), 'cancelled'(已取消)
- 只统计已完成的订单

业务规则：
- 增长率计算公式：(当月销售额 - 上月销售额) / 上月销售额 * 100
- 结果按月份排序

请生成标准的MySQL查询语句。
"""
        
        response = await adapter.generate(prompt)
        
        print(f"✅ 复杂查询生成成功!")
        print(f"📊 Token使用量: {response.tokens_used}")
        print(f"⏱️  响应时间: {response.response_time:.2f}秒")
        print(f"📝 生成内容:\n{response.content}")
        
        # 尝试提取SQL
        if hasattr(adapter, 'extract_sql_from_response'):
            sql = adapter.extract_sql_from_response(response.content)
            if sql:
                print(f"🔍 提取的SQL:\n{sql}")
        
        return True
        
    except Exception as e:
        print(f"❌ 复杂查询测试失败: {str(e)}")
        return False
    finally:
        await adapter.close()


async def test_token_usage_monitoring():
    """测试Token使用量监控"""
    print("\n🔄 测试Token使用量监控...")
    
    config = {
        'api_key': os.environ["DASHSCOPE_API_KEY"],
        'base_url': os.environ["ALIYUN_API_URL"],
        'model_name': os.environ["DASHSCOPE_MODEL"],
        'max_tokens': 500,
        'temperature': 0.1,
        'retry_count': 3,
        'retry_delay': 1.0
    }
    
    adapter = QwenCloudAdapter(config)
    
    try:
        # 初始统计
        initial_stats = adapter.get_token_usage_stats()
        print(f"📊 初始统计: {initial_stats}")
        
        # 进行几次调用
        for i in range(3):
            prompt = f"生成一个简单的SELECT查询语句，查询第{i+1}个用户的信息。"
            response = await adapter.generate(prompt)
            print(f"🔄 第{i+1}次调用完成，使用Token: {response.tokens_used}")
        
        # 最终统计
        final_stats = adapter.get_token_usage_stats()
        print(f"📊 最终统计: {final_stats}")
        
        # 验证统计数据
        assert final_stats['total_requests'] == initial_stats['total_requests'] + 3
        assert final_stats['total_tokens'] > initial_stats['total_tokens']
        assert final_stats['total_cost'] > initial_stats['total_cost']
        
        print("✅ Token使用量监控测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ Token监控测试失败: {str(e)}")
        return False
    finally:
        await adapter.close()


async def test_error_handling():
    """测试错误处理"""
    print("\n🔄 测试错误处理...")
    
    # 使用错误的API密钥
    config = {
        'api_key': 'invalid_api_key',
        'base_url': os.environ["ALIYUN_API_URL"],
        'model_name': os.environ["DASHSCOPE_MODEL"],
        'max_tokens': 500,
        'temperature': 0.1,
        'retry_count': 1,  # 减少重试次数以加快测试
        'retry_delay': 0.5
    }
    
    adapter = QwenCloudAdapter(config)
    
    try:
        prompt = "生成一个简单的SQL查询"
        response = await adapter.generate(prompt)
        print("❌ 应该抛出错误，但没有抛出")
        return False
        
    except Exception as e:
        print(f"✅ 正确捕获错误: {str(e)}")
        return True
    finally:
        await adapter.close()


async def main():
    """主测试函数"""
    print("🚀 开始阿里云Qwen模型API测试")
    print(f"🔑 API密钥: {os.environ['DASHSCOPE_API_KEY'][:10]}...")
    print(f"🌐 API地址: {os.environ['ALIYUN_API_URL']}")
    print(f"🤖 模型名称: {os.environ['DASHSCOPE_MODEL']}")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("基本SQL生成", test_qwen_basic_generation),
        ("流式SQL生成", test_qwen_stream_generation),
        ("复杂SQL生成", test_qwen_complex_query),
        ("Token使用量监控", test_token_usage_monitoring),
        ("错误处理", test_error_handling),
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📋 测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！阿里云Qwen模型集成成功！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)