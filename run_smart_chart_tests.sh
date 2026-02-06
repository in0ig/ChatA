#!/bin/bash

# 任务 6.5.2 - 智能图表系统测试自动化脚本
# 
# 功能：
# 1. 检查测试环境（后端、前端、浏览器）
# 2. 运行后端端到端测试
# 3. 运行前端 Playwright 测试
# 4. 生成测试报告
# 5. 提供手动测试指引

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查服务是否运行
check_service() {
    local url=$1
    local name=$2
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
        print_success "$name 服务运行正常"
        return 0
    else
        print_error "$name 服务未运行或无法访问"
        return 1
    fi
}

# 主函数
main() {
    print_header "智能图表系统测试套件"
    
    echo "任务 6.5.2 - 智能图表系统端到端测试"
    echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # ==========================================
    # 1. 环境检查
    # ==========================================
    print_header "1. 环境检查"
    
    # 检查 Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python 已安装: $PYTHON_VERSION"
    else
        print_error "Python 未安装"
        exit 1
    fi
    
    # 检查 Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js 已安装: $NODE_VERSION"
    else
        print_error "Node.js 未安装"
        exit 1
    fi
    
    # 检查 npm
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        print_success "npm 已安装: v$NPM_VERSION"
    else
        print_error "npm 未安装"
        exit 1
    fi
    
    # 检查后端服务
    print_info "检查后端服务..."
    if check_service "http://localhost:8000/docs" "后端"; then
        BACKEND_RUNNING=true
    else
        BACKEND_RUNNING=false
        print_warning "请先启动后端服务: cd backend && uvicorn src.main:app --reload"
    fi
    
    # 检查前端服务
    print_info "检查前端服务..."
    if check_service "http://localhost:5173" "前端"; then
        FRONTEND_RUNNING=true
    else
        FRONTEND_RUNNING=false
        print_warning "请先启动前端服务: cd frontend && npm run dev"
    fi
    
    # 如果服务未运行，询问是否继续
    if [ "$BACKEND_RUNNING" = false ] || [ "$FRONTEND_RUNNING" = false ]; then
        echo ""
        print_warning "部分服务未运行，某些测试可能会失败"
        read -p "是否继续测试？(y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "测试已取消"
            exit 0
        fi
    fi
    
    # ==========================================
    # 2. 准备测试环境
    # ==========================================
    print_header "2. 准备测试环境"
    
    # 创建测试结果目录
    print_info "创建测试结果目录..."
    mkdir -p test-results
    mkdir -p backend/test-results
    mkdir -p frontend/test-results
    print_success "测试结果目录已创建"
    
    # ==========================================
    # 3. 运行后端测试
    # ==========================================
    if [ "$BACKEND_RUNNING" = true ]; then
        print_header "3. 运行后端端到端测试"
        
        print_info "切换到后端目录..."
        cd backend
        
        print_info "激活虚拟环境..."
        if [ -d ".venv" ]; then
            source .venv/bin/activate || source .venv/Scripts/activate 2>/dev/null || true
            print_success "虚拟环境已激活"
        else
            print_warning "虚拟环境不存在，使用系统 Python"
        fi
        
        print_info "运行后端测试..."
        if pytest tests/e2e/test_real_smart_chart_system.py -v -s --tb=short 2>&1 | tee test-results/backend-test-output.txt; then
            print_success "后端测试完成"
            BACKEND_TEST_PASSED=true
        else
            print_error "后端测试失败"
            BACKEND_TEST_PASSED=false
        fi
        
        cd ..
    else
        print_warning "跳过后端测试（服务未运行）"
        BACKEND_TEST_PASSED=false
    fi
    
    # ==========================================
    # 4. 运行前端测试
    # ==========================================
    if [ "$FRONTEND_RUNNING" = true ]; then
        print_header "4. 运行前端 Playwright 测试"
        
        print_info "切换到前端目录..."
        cd frontend
        
        # 检查 Playwright 是否安装
        if [ ! -d "node_modules/@playwright" ]; then
            print_warning "Playwright 未安装，正在安装..."
            npm install --save-dev @playwright/test
            npx playwright install
        fi
        
        print_info "运行前端测试..."
        if npx playwright test tests/e2e/smart-chart-system-real.spec.ts --reporter=html 2>&1 | tee test-results/frontend-test-output.txt; then
            print_success "前端测试完成"
            FRONTEND_TEST_PASSED=true
        else
            print_error "前端测试失败"
            FRONTEND_TEST_PASSED=false
        fi
        
        # 生成测试报告
        print_info "生成测试报告..."
        if [ -d "playwright-report" ]; then
            print_success "测试报告已生成: frontend/playwright-report/index.html"
        fi
        
        cd ..
    else
        print_warning "跳过前端测试（服务未运行）"
        FRONTEND_TEST_PASSED=false
    fi
    
    # ==========================================
    # 5. 测试总结
    # ==========================================
    print_header "5. 测试总结"
    
    echo "测试完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 后端测试结果
    if [ "$BACKEND_RUNNING" = true ]; then
        if [ "$BACKEND_TEST_PASSED" = true ]; then
            print_success "后端测试: 通过"
        else
            print_error "后端测试: 失败"
        fi
    else
        print_warning "后端测试: 未运行"
    fi
    
    # 前端测试结果
    if [ "$FRONTEND_RUNNING" = true ]; then
        if [ "$FRONTEND_TEST_PASSED" = true ]; then
            print_success "前端测试: 通过"
        else
            print_error "前端测试: 失败"
        fi
    else
        print_warning "前端测试: 未运行"
    fi
    
    echo ""
    print_info "测试结果位置:"
    echo "  - 后端测试: backend/test-results/"
    echo "  - 前端测试: frontend/test-results/"
    echo "  - 前端报告: frontend/playwright-report/index.html"
    echo "  - 截图: test-results/"
    
    # ==========================================
    # 6. 手动测试指引
    # ==========================================
    print_header "6. 手动测试指引"
    
    echo "自动化测试已完成，建议继续进行手动测试："
    echo ""
    echo "1. 打开测试指南:"
    echo "   cat TASK_6_5_2_SMART_CHART_SYSTEM_TEST_GUIDE.md"
    echo ""
    echo "2. 打开浏览器访问:"
    echo "   http://localhost:5173/chat"
    echo ""
    echo "3. 按照测试指南执行 8 个手动测试场景"
    echo ""
    echo "4. 截图保存到 test-results/ 目录"
    echo ""
    
    # 询问是否打开浏览器
    read -p "是否现在打开浏览器进行手动测试？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "正在打开浏览器..."
        
        # 根据操作系统打开浏览器
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            open "http://localhost:5173/chat"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            xdg-open "http://localhost:5173/chat" 2>/dev/null || sensible-browser "http://localhost:5173/chat" 2>/dev/null
        elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
            # Windows
            start "http://localhost:5173/chat"
        fi
        
        print_success "浏览器已打开"
    fi
    
    # ==========================================
    # 7. 查看测试报告
    # ==========================================
    echo ""
    read -p "是否查看 Playwright 测试报告？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "正在打开测试报告..."
        cd frontend
        npx playwright show-report
        cd ..
    fi
    
    # 最终状态
    echo ""
    if [ "$BACKEND_TEST_PASSED" = true ] && [ "$FRONTEND_TEST_PASSED" = true ]; then
        print_success "所有自动化测试通过！"
        exit 0
    else
        print_warning "部分测试失败或未运行，请查看详细日志"
        exit 1
    fi
}

# 运行主函数
main
