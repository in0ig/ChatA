#!/usr/bin/env python3
"""
调试阿里云Qwen API调用
"""

import asyncio
import httpx
import json

# API配置
API_KEY = "sk-399d0eb35c494883afdc3ca41e2ce214"
BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
MODEL_NAME = "qwen-plus-2025-09-11"


async def test_simple_call():
    """测试简单的API调用"""
    print("🔄 测试简单API调用...")
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': MODEL_NAME,
        'input': {
            'messages': [
                {'role': 'user', 'content': '你好，请生成一个简单的SQL查询语句'}
            ]
        },
        'parameters': {
            'max_tokens': 500,
            'temperature': 0.1,
            'result_format': 'message'
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"📡 发送请求到: {BASE_URL}/services/aigc/text-generation/generation")
            print(f"🔑 使用API密钥: {API_KEY[:10]}...")
            print(f"🤖 模型: {MODEL_NAME}")
            print(f"📦 请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = await client.post(
                f'{BASE_URL}/services/aigc/text-generation/generation',
                headers=headers,
                json=payload
            )
            
            print(f"📊 响应状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 响应成功:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # 提取内容
                if 'output' in result and 'choices' in result['output']:
                    content = result['output']['choices'][0]['message']['content']
                    print(f"📝 生成内容: {content}")
                
            else:
                print(f"❌ 请求失败:")
                print(f"错误内容: {response.text}")
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}")


async def test_stream_call():
    """测试流式API调用"""
    print("\n🔄 测试流式API调用...")
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': MODEL_NAME,
        'input': {
            'messages': [
                {'role': 'user', 'content': '请生成一个查询用户信息的SQL语句'}
            ]
        },
        'parameters': {
            'max_tokens': 500,
            'temperature': 0.1,
            'incremental_output': True
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("📡 开始流式请求...")
            
            async with client.stream(
                'POST',
                f'{BASE_URL}/services/aigc/text-generation/generation',
                headers=headers,
                json=payload
            ) as response:
                
                print(f"📊 流式响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print("📡 接收流式数据:")
                    async for line in response.aiter_lines():
                        if line.strip():
                            print(f"📄 收到行: {line}")
                            
                            # 尝试解析JSON
                            try:
                                if line.startswith('data: '):
                                    data = json.loads(line[6:])
                                else:
                                    data = json.loads(line)
                                
                                print(f"📦 解析数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                                
                                if 'output' in data and 'choices' in data['output']:
                                    choices = data['output']['choices']
                                    if choices and 'message' in choices[0]:
                                        content = choices[0]['message']['content']
                                        print(f"📝 内容: {content}")
                                        
                            except json.JSONDecodeError as e:
                                print(f"⚠️  JSON解析失败: {e}")
                else:
                    print(f"❌ 流式请求失败: {response.status_code}")
                    print(f"错误内容: {await response.aread()}")
                    
        except Exception as e:
            print(f"❌ 流式请求异常: {str(e)}")


async def main():
    """主函数"""
    print("🚀 开始调试阿里云Qwen API")
    print("=" * 50)
    
    await test_simple_call()
    await test_stream_call()
    
    print("\n" + "=" * 50)
    print("🏁 调试完成")


if __name__ == "__main__":
    asyncio.run(main())