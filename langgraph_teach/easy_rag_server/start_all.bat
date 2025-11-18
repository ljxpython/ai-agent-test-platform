@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   知识库管理系统 - 启动脚本
echo ==========================================
echo.

REM 检查是否在项目根目录
if not exist "pyproject.toml" (
    echo ❌ 错误: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python,请先安装Python 3.13+
    pause
    exit /b 1
)

REM 检查Node.js环境
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Node.js,请先安装Node.js 20+
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 询问是否安装依赖
set /p install_deps="是否需要安装依赖? (y/n): "

if /i "%install_deps%"=="y" (
    echo.
    echo 📦 安装后端依赖...
    call uv sync

    echo.
    echo 📦 安装前端依赖...
    cd retrieval_grant_web
    call npm install
    cd ..

    echo.
    echo ✅ 依赖安装完成
)

echo.
echo ==========================================
echo   启动服务
echo ==========================================
echo.

REM 启动后端服务
echo 🚀 启动后端服务 (端口: 8001)...
cd src\agentic_rag_server
start "知识库后端服务" cmd /k "python start_server.py"
cd ..\..

echo    API文档: http://localhost:8001/docs
echo    健康检查: http://localhost:8001/api/health

REM 等待后端启动
echo.
echo ⏳ 等待后端服务启动...
timeout /t 5 /nobreak >nul

echo.
echo 🚀 启动前端服务 (端口: 8000)...
echo.
cd retrieval_grant_web
call npm run start:dev

pause
