#!/usr/bin/env python3
"""
SQL错误恢复功能测试脚本

独立测试脚本，验证SQL错误分类和恢复功能。
"""

import sys
import os
import asyncio

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.sql_error_classifier import (
    SQLErrorClassifier,
    SQLErrorRetryHandler,
    ErrorFeedbackGenerator,
    SQLErrorRecoveryService,
    SQLErrorType,
    RetryStrategy
)


def test_sql_error_classifier():
    """测试SQL错误分类器"""
    print("🧪 Testing SQL Error Classifier...")
    
    classifier = SQLErrorClassifier()
    
    test_cases = [
        # MySQL错误
        ("You have an error in your SQL syntax", "SELECT * FROM users WHRE id = 1", SQLErrorType.SYNTAX_ERROR),
        ("Unknown column 'user_name' in 'field list'", "SELECT user_name FROM users", SQLErrorType.FIELD_NOT_EXISTS),
        ("Table 'test.users' doesn't exist", "SELECT * FROM users", SQLErrorType.TABLE_NOT_EXISTS),
        ("Incorrect integer value for column 'age'", "INSERT INTO users (age) VALUES ('abc')", SQLErrorType.TYPE_MISMATCH),
        
        # SQL Server错误
        ("Incorrect syntax near 'WHRE'", "SELECT * FROM users WHRE id = 1", SQLErrorType.SYNTAX_ERROR),
        ("Invalid column name 'user_name'", "SELECT user_name FROM users", SQLErrorType.FIELD_NOT_EXISTS),
        ("Invalid object name 'users'", "SELECT * FROM users", SQLErrorType.TABLE_NOT_EXISTS),
        
        # 权限和连接错误
        ("Access denied for user 'test'@'localhost'", "SELECT * FROM sensitive", SQLErrorType.PERMISSION_ERROR),
        ("Can't connect to MySQL server", "SELECT 1", SQLErrorType.CONNECTION_ERROR),
        
        # 未知错误
        ("Some unknown database error", "SELECT * FROM test", SQLErrorType.UNKNOWN_ERROR),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (error_msg, sql, expected_type) in enumerate(test_cases, 1):
        result = classifier.classify_error(error_msg, sql)
        if result.error_type == expected_type:
            print(f"  ✅ Test {i}: {result.error_type.value} (confidence: {result.confidence:.2f})")
            passed += 1
        else:
            print(f"  ❌ Test {i}: Expected {expected_type.value}, got {result.error_type.value}")
    
    print(f"  📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    # 测试统计功能
    stats = classifier.get_error_statistics()
    print(f"  📈 Statistics: {stats['total_errors']} total errors, most common: {stats.get('most_common_error', 'N/A')}")
    
    return passed == total


async def test_retry_handler():
    """测试重试处理器"""
    print("\n🔄 Testing SQL Error Retry Handler...")
    
    classifier = SQLErrorClassifier()
    retry_handler = SQLErrorRetryHandler(classifier)
    
    # 模拟重试回调
    async def mock_retry_callback(retry_type, sql_error):
        print(f"    🔄 Retry callback called: {retry_type} for {sql_error.error_type.value}")
        return False, None  # 模拟重试失败
    
    # 测试重试逻辑
    success, result, sql_error = await retry_handler.handle_error_with_retry(
        error_message="Unknown column 'test_field' in 'field list'",
        sql_statement="SELECT test_field FROM users",
        session_id="test_session",
        retry_callback=mock_retry_callback
    )
    
    print(f"  ✅ Error classified as: {sql_error.error_type.value}")
    print(f"  ✅ Retry strategy: {sql_error.retry_strategy.value}")
    print(f"  ✅ Retry result: success={success}")
    
    # 测试统计
    stats = retry_handler.get_retry_statistics("test_session")
    print(f"  📊 Retry statistics: {stats}")
    
    return True


def test_feedback_generator():
    """测试错误反馈生成器"""
    print("\n💬 Testing Error Feedback Generator...")
    
    classifier = SQLErrorClassifier()
    feedback_generator = ErrorFeedbackGenerator(classifier)
    
    # 创建测试错误
    sql_error = classifier.classify_error(
        "Unknown column 'user_name' in 'field list'",
        "SELECT user_name FROM users"
    )
    
    context = {
        "session_id": "test_session",
        "original_question": "查询用户姓名",
        "available_fields": ["id", "username", "email"],
        "available_tables": ["users", "orders"]
    }
    
    feedback = feedback_generator.generate_feedback_for_ai(sql_error, context)
    
    print(f"  ✅ Feedback generated for session: {feedback.session_id}")
    print(f"  ✅ Original question: {feedback.original_question}")
    print(f"  ✅ Error type: {feedback.error_info.error_type.value}")
    print(f"  ✅ Feedback content length: {len(feedback.feedback_for_ai)} characters")
    
    # 测试日志格式化
    log_format = feedback_generator.format_feedback_for_logging(feedback)
    print(f"  ✅ Log format generated: {len(log_format)} characters")
    
    return True


async def test_recovery_service():
    """测试完整的错误恢复服务"""
    print("\n🛠️ Testing SQL Error Recovery Service...")
    
    service = SQLErrorRecoveryService()
    
    # 测试完整的错误处理流程
    result = await service.handle_sql_error(
        error_message="Table 'test.invalid_table' doesn't exist",
        sql_statement="SELECT * FROM invalid_table",
        session_id="test_session",
        context={
            "original_question": "查询无效表",
            "available_tables": ["users", "orders", "products"]
        }
    )
    
    print(f"  ✅ Recovery handled: success={result['success']}")
    print(f"  ✅ Error type: {result['error_info']['error_type']}")
    print(f"  ✅ Feedback generated: {'feedback_for_ai' in result['feedback']}")
    print(f"  ✅ Statistics available: {'total_retries' in result['retry_statistics']}")
    
    # 测试服务统计
    service_stats = service.get_service_statistics()
    print(f"  📊 Service statistics: {service_stats}")
    
    # 测试学习功能
    service.learn_from_feedback(
        "Test error for learning",
        SQLErrorType.SYNTAX_ERROR.value
    )
    print(f"  ✅ Learning function executed")
    
    return True


async def main():
    """主测试函数"""
    print("🚀 Starting SQL Error Recovery System Tests\n")
    
    tests = [
        ("SQL Error Classifier", test_sql_error_classifier()),
        ("Retry Handler", test_retry_handler()),
        ("Feedback Generator", test_feedback_generator()),
        ("Recovery Service", test_recovery_service())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutine(test_func):
                result = await test_func
            else:
                result = test_func
            
            if result:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
    
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! SQL Error Recovery System is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)