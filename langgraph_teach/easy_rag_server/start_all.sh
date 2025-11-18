#!/bin/bash

# 知识库管理系统 - 一键启动脚本

echo "=========================================="
echo "  知识库管理系统 - 启动脚本"
echo "=========================================="
echo ""

# 检查是否在项目根目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到Python,请先安装Python 3.13+"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js,请先安装Node.js 20+"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 询问是否安装依赖
read -p "是否需要安装依赖? (y/n): " install_deps

if [ "$install_deps" = "y" ] || [ "$install_deps" = "Y" ]; then
    echo ""
    echo "📦 安装后端依赖..."
    uv sync

    echo ""
    echo "📦 安装前端依赖..."
    cd retrieval_grant_web
    npm install
    cd ..

    echo ""
    echo "✅ 依赖安装完成"
fi

echo ""
echo "=========================================="
echo "  启动服务"
echo "=========================================="
echo ""

# 启动后端服务(后台运行)
echo "🚀 启动后端服务 (端口: 8001)..."
cd src/agentic_rag_server
python start_server.py > ../../backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

echo "   后端PID: $BACKEND_PID"
echo "   日志文件: backend.log"
echo "   API文档: http://localhost:8001/docs"

# 等待后端启动
echo ""
echo "⏳ 等待后端服务启动..."
sleep 5

# 检查后端是否启动成功
if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "⚠️  后端服务可能未完全启动,请检查 backend.log"
fi

# 启动前端服务(前台运行)
echo ""
echo "🚀 启动前端服务 (端口: 8000)..."
echo ""
cd retrieval_grant_web
npm run start:dev

# 清理函数
cleanup() {
    echo ""
    echo "=========================================="
    echo "  停止服务"
    echo "=========================================="
    echo ""
    echo "🛑 停止后端服务..."
    kill $BACKEND_PID 2>/dev/null
    echo "✅ 服务已停止"
    exit 0
}

# 捕获Ctrl+C信号
trap cleanup INT TERM

# 等待前端进程
wait
