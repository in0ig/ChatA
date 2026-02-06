#!/bin/bash

# 对话界面功能测试 - 完整测试套件
# 使用真实数据库、真实AI调用、真实流式响应

set -e

echo "========================================"
echo "🚀 对话界面功能测试套件"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local service_name=$1
    local url=$2
    
    echo -n "检查 $service_name... "
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 运行中${NC}"
        return 0
    else
        echo -e "${RED}❌ 未运行${NC}"
        return 1
    fi
}

# 1. 环境检查
echo "📋 步骤 1: 环境检查"
echo "----------------------------------------"

check_service "后端服务" "http://localhost:8000/health" || {
    echo -e "${RED}错误: 后端服务未启动${NC}"
    echo "请运行: cd backend && uvicorn src.main:app --reload"
    exit 1
}

check_service "前端服务" "http://localhost:5173" || {
    echo -e "${RED}错误: 前端服务未启动${NC}"
    echo "请运行: cd frontend && npm run dev"
    exit 1
}

echo ""

# 2. 数据库检查
echo "📋 步骤 2: 数据库检查"
echo "----------------------------------------"

cd backend
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from src.database import get_db
from src.models.data_source_model import DataSource

try:
    db = next(get_db())
    count = db.query(DataSource).count()
    print(f"✅ 数据库连接正常")
    print(f"   数据源数量: {count}")
    db.close()
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}数据库检查失败${NC}"
    exit 1
fi

cd ..
echo ""

# 3. AI 模型配置检查
echo "📋 步骤 3: AI 模型配置检查"
echo "----------------------------------------"

if [ -f "backend/.env" ]; then
    echo "✅ .env 文件存在"
    
    if grep -q "QWEN_API_KEY" backend/.env; then
        echo "✅ Qwen API Key 已配置"
    else
        echo -e "${YELLOW}⚠️  Qwen API Key 未配置${NC}"
    fi
    
    if grep -q "OPENAI_API_KEY" backend/.env; then
        echo "✅ OpenAI API Key 已配置"
    else
        echo -e "${YELLOW}⚠️  OpenAI API Key 未配置${NC}"
    fi
else
    echo -e "${RED}❌ .env 文件不存在${NC}"
    exit 1
fi

echo ""

# 4. 创建测试结果目录
echo "📋 步骤 4: 准备测试环境"
echo "----------------------------------------"

mkdir -p test-results
mkdir -p backend/test-results
mkdir -p frontend/test-results

echo "✅ 测试结果目录已创建"
echo ""

# 5. 运行后端测试
echo "📋 步骤 5: 运行后端端到端测试"
echo "========================================"
echo ""

cd backend

if [ -f "tests/e2e/test_real_dialogue_interface.py" ]; then
    echo "🧪 执行后端测试..."
    python -m pytest tests/e2e/test_real_dialogue_interface.py -v -s --tb=short || {
        echo -e "${RED}❌ 后端测试失败${NC}"
        cd ..
        exit 1
    }
    echo -e "${GREEN}✅ 后端测试通过${NC}"
else
    echo -e "${YELLOW}⚠️  后端测试文件不存在，跳过${NC}"
fi

cd ..
echo ""

# 6. 运行前端测试
echo "📋 步骤 6: 运行前端端到端测试"
echo "========================================"
echo ""

cd frontend

# 检查 Playwright 是否安装
if ! command -v npx &> /dev/null; then
    echo -e "${RED}❌ npx 未安装${NC}"
    cd ..
    exit 1
fi

# 安装 Playwright（如果需要）
if [ ! -d "node_modules/@playwright" ]; then
    echo "📦 安装 Playwright..."
    npx playwright install
fi

if [ -f "tests/e2e/dialogue-interface-real.spec.ts" ]; then
    echo "🧪 执行前端测试..."
    npx playwright test tests/e2e/dialogue-interface-real.spec.ts --reporter=list || {
        echo -e "${YELLOW}⚠️  前端测试有失败，请查看报告${NC}"
    }
    
    # 生成测试报告
    if [ -d "playwright-report" ]; then
        echo ""
        echo "📊 测试报告已生成: frontend/playwright-report/index.html"
        echo "   查看报告: npx playwright show-report"
    fi
else
    echo -e "${YELLOW}⚠️  前端测试文件不存在，跳过${NC}"
fi

cd ..
echo ""

# 7. 生成测试总结
echo "========================================"
echo "📊 测试总结"
echo "========================================"
echo ""

# 统计测试结果
BACKEND_TESTS=$(find backend/test-results -name "*.xml" 2>/dev/null | wc -l)
FRONTEND_TESTS=$(find frontend/test-results -name "*.json" 2>/dev/null | wc -l)

echo "后端测试: $BACKEND_TESTS 个测试文件"
echo "前端测试: $FRONTEND_TESTS 个测试文件"
echo ""

# 检查截图
SCREENSHOTS=$(find test-results -name "*.png" 2>/dev/null | wc -l)
echo "测试截图: $SCREENSHOTS 张"
echo ""

echo "测试结果位置:"
echo "  - 后端: backend/test-results/"
echo "  - 前端: frontend/test-results/"
echo "  - 截图: test-results/"
echo ""

# 8. 打开测试指南
echo "========================================"
echo "📖 测试指南"
echo "========================================"
echo ""
echo "详细测试指南: TASK_6_5_1_DIALOGUE_INTERFACE_TEST_GUIDE.md"
echo ""
echo "手动测试场景:"
echo "  1. 基础对话流程"
echo "  2. 流式消息显示"
echo "  3. 图表自动生成"
echo "  4. 多轮对话"
echo "  5. 表格图表切换"
echo "  6. 错误处理"
echo "  7. 数据追问"
echo "  8. 复杂查询"
echo ""

# 9. 提示下一步
echo "========================================"
echo "✅ 自动化测试完成！"
echo "========================================"
echo ""
echo "下一步:"
echo "  1. 查看测试报告"
echo "  2. 执行手动测试场景"
echo "  3. 填写测试报告"
echo "  4. 记录发现的问题"
echo ""
echo "开始手动测试:"
echo "  1. 打开浏览器: http://localhost:5173/chat"
echo "  2. 参考测试指南执行测试场景"
echo "  3. 截图保存到 test-results/"
echo ""

# 询问是否打开浏览器
read -p "是否打开浏览器开始手动测试? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 根据操作系统打开浏览器
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "http://localhost:5173/chat"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "http://localhost:5173/chat"
    else
        echo "请手动打开: http://localhost:5173/chat"
    fi
fi

echo ""
echo "🎉 测试套件执行完成！"
