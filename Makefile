# AI Chat 项目管理 Makefile
.PHONY: help install install-backend install-frontend start-backend start-frontend start stop-backend stop-frontend stop clean logs

# 默认目标
help:
	@echo "🚀 AI Chat 项目管理命令"
	@echo ""
	@echo "📦 环境管理:"
	@echo "  make install          - 安装所有依赖"
	@echo "  make install-backend  - 安装后端依赖"
	@echo "  make install-frontend - 安装前端依赖"
	@echo ""
	@echo "🌐 服务管理:"
	@echo "  make start           - 启动所有服务"
	@echo "  make start-backend   - 启动后端服务 (nohup)"
	@echo "  make start-frontend  - 启动前端服务"
	@echo ""
	@echo "🛑 停止服务:"
	@echo "  make stop            - 停止所有服务"
	@echo "  make stop-backend    - 停止后端服务"
	@echo "  make stop-frontend   - 停止前端服务"
	@echo ""
	@echo "🗄️ 数据库管理:"
	@echo "  make init-db         - 初始化数据库"
	@echo "  make migrate         - 运行数据库迁移"
	@echo "  make makemigrations  - 创建新的迁移文件"
	@echo "  make reset-db        - 重置数据库"
	@echo ""
	@echo "🔄 数据库切换:"
	@echo "  make switch-to-sqlite     - 切换到SQLite数据库"
	@echo "  make switch-to-mysql      - 切换到MySQL数据库"
	@echo "  make db-status            - 查看当前数据库配置"
	@echo "  make test-db              - 测试数据库连接"
	@echo ""
	@echo "🛠️ MySQL管理:"
	@echo "  make setup-mysql          - 设置MySQL数据库"
	@echo "  make check-mysql          - 检查MySQL连接"
	@echo "  make migrate-sqlite-to-mysql - 从SQLite迁移到MySQL"
	@echo ""
	@echo "🔧 其他:"
	@echo "  make status          - 查看服务状态"
	@echo "  make logs            - 查看后端日志"
	@echo "  make clean           - 清理临时文件"
	@echo "  make force-clean     - 强制清理所有进程"
	@echo "  make force-clean-backend  - 强制清理后端进程"
	@echo "  make force-clean-frontend - 强制清理前端进程"
	@echo "  make clean-ports     - 清理端口占用"
	@echo "  make show-processes  - 显示所有相关进程"
	@echo "  make test-config     - 测试配置"
	@echo ""
	@echo "📚 Poetry 管理:"
	@echo "  make poetry-shell    - 进入 Poetry 虚拟环境"
	@echo "  make poetry-show     - 显示依赖信息"
	@echo "  make poetry-update   - 更新依赖"

# 安装所有依赖
install: install-backend install-frontend
	@echo "✅ 所有依赖安装完成"

# 安装后端依赖
install-backend:
	@echo "📦 安装后端依赖..."
	@if ! command -v poetry &> /dev/null; then \
		echo "❌ Poetry 未安装，请先安装 Poetry"; \
		echo "💡 安装命令: curl -sSL https://install.python-poetry.org | python3 -"; \
		exit 1; \
	fi
	@if [ -f "pyproject.toml" ]; then \
		poetry install --no-root; \
		echo "✅ 后端依赖安装完成"; \
	else \
		echo "❌ 找不到 pyproject.toml"; \
		exit 1; \
	fi

# 安装前端依赖
install-frontend:
	@echo "📦 安装前端依赖..."
	@if [ -d "frontend" ]; then \
		cd frontend && npm install; \
		echo "✅ 前端依赖安装完成"; \
	else \
		echo "❌ 找不到 frontend 目录"; \
		exit 1; \
	fi

# 启动所有服务
start: start-backend start-frontend
	@echo "🎉 所有服务启动完成"
	@echo "🌐 前端地址: http://localhost:3000"
	@echo "🔧 后端地址: http://localhost:8000"
	@echo "📚 API 文档: http://localhost:8000/docs"

# 启动后端服务 (使用 nohup)
start-backend:
	@echo "🚀 启动后端服务..."
	@if [ -f "backend.pid" ]; then \
		echo "⚠️  后端服务已在运行 (PID: $$(cat backend.pid))"; \
	else \
		nohup poetry run python main.py > backend.log 2>&1 & echo $$! > backend.pid; \
		sleep 2; \
		if [ -f "backend.pid" ] && kill -0 $$(cat backend.pid) 2>/dev/null; then \
			echo "✅ 后端服务启动成功 (PID: $$(cat backend.pid))"; \
		else \
			echo "❌ 后端服务启动失败"; \
			rm -f backend.pid; \
			exit 1; \
		fi \
	fi

# 启动前端服务
start-frontend:
	@echo "🎨 启动前端服务..."
	@if [ -f "frontend.pid" ] && kill -0 $$(cat frontend.pid) 2>/dev/null; then \
		echo "⚠️  前端服务已在运行 (PID: $$(cat frontend.pid))"; \
	else \
		rm -f frontend.pid; \
		cd frontend && nohup npm run dev > ../frontend.log 2>&1 & \
		FRONTEND_PID=$$!; \
		echo $$FRONTEND_PID > ../frontend.pid; \
		echo "🚀 前端服务启动中 (PID: $$FRONTEND_PID)..."; \
		sleep 5; \
		if kill -0 $$FRONTEND_PID 2>/dev/null; then \
			echo "✅ 前端服务启动成功 (PID: $$FRONTEND_PID)"; \
			echo "🌐 前端地址: http://localhost:3000"; \
		else \
			echo "❌ 前端服务启动失败，请查看日志: tail -f frontend.log"; \
			rm -f frontend.pid; \
			exit 1; \
		fi \
	fi

# 停止所有服务
stop: stop-backend stop-frontend
	@echo "🛑 所有服务已停止"

# 停止后端服务
stop-backend:
	@echo "🛑 停止后端服务..."
	@# 首先尝试通过 PID 文件停止
	@if [ -f "backend.pid" ]; then \
		PID=$$(cat backend.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			kill $$PID; \
			echo "✅ 后端主进程已停止 (PID: $$PID)"; \
		else \
			echo "⚠️  PID 文件中的进程不存在"; \
		fi; \
		rm -f backend.pid; \
	fi
	@# 查找并停止所有相关进程
	@echo "🔍 查找所有后端相关进程..."
	@PIDS=$$(ps -ef | grep -E "([Pp]ython.*main\.py|uvicorn.*main|fastapi.*main)" | grep -v grep | awk '{print $$2}' | tr '\n' ' '); \
	if [ -n "$$PIDS" ]; then \
		echo "发现后端进程: $$PIDS"; \
		for pid in $$PIDS; do \
			if kill -0 $$pid 2>/dev/null; then \
				kill $$pid; \
				echo "✅ 已停止进程 $$pid"; \
			fi; \
		done; \
		sleep 2; \
		REMAINING=$$(ps -ef | grep -E "([Pp]ython.*main\.py|uvicorn.*main|fastapi.*main)" | grep -v grep | awk '{print $$2}' | tr '\n' ' '); \
		if [ -n "$$REMAINING" ]; then \
			echo "⚠️  强制停止剩余进程: $$REMAINING"; \
			for pid in $$REMAINING; do \
				kill -9 $$pid 2>/dev/null; \
			done; \
		fi; \
		echo "✅ 所有后端服务已停止"; \
	else \
		echo "⚠️  未发现运行中的后端服务"; \
	fi
	@# 检查并杀掉占用 8000 端口的进程
	@echo "🔍 检查 8000 端口占用情况..."
	@PORT_PIDS=$$(lsof -ti:8000 2>/dev/null | tr '\n' ' '); \
	if [ -n "$$PORT_PIDS" ]; then \
		echo "发现占用 8000 端口的进程: $$PORT_PIDS"; \
		for pid in $$PORT_PIDS; do \
			if kill -0 $$pid 2>/dev/null; then \
				kill $$pid; \
				echo "✅ 已停止占用端口的进程 $$pid"; \
				sleep 1; \
				if kill -0 $$pid 2>/dev/null; then \
					echo "⚠️  强制停止进程 $$pid"; \
					kill -9 $$pid 2>/dev/null; \
				fi; \
			fi; \
		done; \
		echo "✅ 8000 端口已释放"; \
	else \
		echo "✅ 8000 端口未被占用"; \
	fi
# 停止前端服务
stop-frontend:
	@echo "🛑 停止前端服务..."
	@# 首先尝试通过 PID 文件停止
	@if [ -f "frontend.pid" ]; then \
		PID=$$(cat frontend.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			kill $$PID; \
			echo "✅ 前端主进程已停止 (PID: $$PID)"; \
		else \
			echo "⚠️  PID 文件中的进程不存在"; \
		fi; \
		rm -f frontend.pid; \
	fi
	@# 查找并停止所有相关进程
	@echo "🔍 查找所有前端相关进程..."
	@PIDS=$$(ps -ef | grep -E "(npm run dev|vite|esbuild)" | grep -v grep | awk '{print $$2}' | tr '\n' ' '); \
	if [ -n "$$PIDS" ]; then \
		echo "发现前端进程: $$PIDS"; \
		for pid in $$PIDS; do \
			if kill -0 $$pid 2>/dev/null; then \
				kill $$pid; \
				echo "✅ 已停止进程 $$pid"; \
			fi; \
		done; \
		sleep 2; \
		REMAINING=$$(ps -ef | grep -E "(npm run dev|vite|esbuild)" | grep -v grep | awk '{print $$2}' | tr '\n' ' '); \
		if [ -n "$$REMAINING" ]; then \
			echo "⚠️  强制停止剩余进程: $$REMAINING"; \
			for pid in $$REMAINING; do \
				kill -9 $$pid 2>/dev/null; \
			done; \
		fi; \
		echo "✅ 所有前端服务已停止"; \
	else \
		echo "⚠️  未发现运行中的前端服务"; \
	fi

# 查看后端日志
logs:
	@echo "📋 查看后端日志 (按 Ctrl+C 退出):"
	@if [ -f "backend.log" ]; then \
		tail -f backend.log; \
	else \
		echo "❌ 找不到后端日志文件"; \
	fi

# 测试配置
test-config:
	@echo "🧪 测试配置..."
	@poetry run python test_config.py

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	@rm -f *.pid *.log
	@rm -rf __pycache__ */__pycache__ */*/__pycache__
	@rm -rf .pytest_cache
	@echo "✅ 清理完成"

# 强制清理后端进程
force-clean-backend:
	@echo "🧹 强制清理所有后端进程..."
	@BACKEND_PIDS=$$(ps -ef | grep -E "([Pp]ython.*main\.py|uvicorn.*main|fastapi.*main)" | grep -v grep | awk '{print $$2}' | tr '\n' ' '); \
	if [ -n "$$BACKEND_PIDS" ]; then \
		echo "发现后端进程: $$BACKEND_PIDS"; \
		for pid in $$BACKEND_PIDS; do \
			if ps -p $$pid > /dev/null 2>&1; then \
				echo "强制停止后端进程: $$pid"; \
				kill -9 $$pid 2>/dev/null; \
			fi; \
		done; \
		echo "✅ 所有后端进程已清理"; \
	else \
		echo "⚠️  未发现运行中的后端进程"; \
	fi
	@# 检查并强制杀掉占用 8000 端口的进程
	@echo "🔍 强制清理 8000 端口占用..."
	@PORT_PIDS=$$(lsof -ti:8000 2>/dev/null | tr '\n' ' '); \
	if [ -n "$$PORT_PIDS" ]; then \
		echo "强制停止占用 8000 端口的进程: $$PORT_PIDS"; \
		for pid in $$PORT_PIDS; do \
			kill -9 $$pid 2>/dev/null; \
		done; \
		echo "✅ 8000 端口已强制释放"; \
	fi
	@rm -f backend.pid backend.log
	@echo "✅ 后端进程强制清理完成"

# 强制清理前端进程
force-clean-frontend:
	@echo "🧹 强制清理所有前端进程..."
	@FRONTEND_PIDS=$$(ps -ef | grep -E "(npm run dev|vite|esbuild|node.*frontend)" | grep -v grep | awk '{print $$2}' | tr '\n' ' '); \
	if [ -n "$$FRONTEND_PIDS" ]; then \
		echo "发现前端进程: $$FRONTEND_PIDS"; \
		for pid in $$FRONTEND_PIDS; do \
			if ps -p $$pid > /dev/null 2>&1; then \
				echo "强制停止前端进程: $$pid"; \
				kill -9 $$pid 2>/dev/null; \
			fi; \
		done; \
		echo "✅ 所有前端进程已清理"; \
	else \
		echo "⚠️  未发现运行中的前端进程"; \
	fi
	@rm -f frontend.pid frontend.log
	@echo "✅ 前端进程强制清理完成"

# 清理端口占用
clean-ports:
	@echo "🌐 清理端口占用..."
	@echo "🔍 检查后端端口 8000..."
	@PORT_PIDS=$$(lsof -ti:8000 2>/dev/null | tr '\n' ' '); \
	if [ -n "$$PORT_PIDS" ]; then \
		echo "发现占用 8000 端口的进程: $$PORT_PIDS"; \
		for pid in $$PORT_PIDS; do \
			echo "停止进程 $$pid"; \
			kill -9 $$pid 2>/dev/null; \
		done; \
		echo "✅ 8000 端口已释放"; \
	else \
		echo "✅ 8000 端口未被占用"; \
	fi
	@echo "🔍 检查前端端口 3000..."
	@PORT_PIDS=$$(lsof -ti:3000 2>/dev/null | tr '\n' ' '); \
	if [ -n "$$PORT_PIDS" ]; then \
		echo "发现占用 3000 端口的进程: $$PORT_PIDS"; \
		for pid in $$PORT_PIDS; do \
			echo "停止进程 $$pid"; \
			kill -9 $$pid 2>/dev/null; \
		done; \
		echo "✅ 3000 端口已释放"; \
	else \
		echo "✅ 3000 端口未被占用"; \
	fi
	@echo "✅ 端口清理完成"

# 强制清理所有进程
force-clean:
	@echo "🧹 强制清理所有相关进程..."
	@$(MAKE) force-clean-backend
	@$(MAKE) force-clean-frontend
	@$(MAKE) clean-ports
	@echo "✅ 所有进程强制清理完成"

# 显示所有相关进程
show-processes:
	@echo "📊 当前运行的相关进程:"
	@echo ""
	@echo "🔧 后端进程:"
	@ps -ef | grep -E "([Pp]ython.*main\.py|uvicorn.*main|fastapi.*main)" | grep -v grep || echo "  无后端进程"
	@echo ""
	@echo "🎨 前端进程:"
	@ps -ef | grep -E "(npm run dev|vite|esbuild)" | grep -v grep || echo "  无前端进程"
	@echo ""
	@echo "📁 PID 文件:"
	@ls -la *.pid 2>/dev/null || echo "  无 PID 文件"
	@echo ""
	@echo "🌐 端口占用情况:"
	@echo "  后端端口 8000:"
	@lsof -i:8000 2>/dev/null | head -10 || echo "    端口未被占用"
	@echo "  前端端口 3000:"
	@lsof -i:3000 2>/dev/null | head -10 || echo "    端口未被占用"

# 检查服务状态
status:
	@echo "📊 服务状态:"
	@if [ -f "backend.pid" ]; then \
		PID=$$(cat backend.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "🟢 后端服务运行中 (PID: $$PID)"; \
		else \
			echo "🔴 后端服务已停止"; \
			rm -f backend.pid; \
		fi; \
	else \
		echo "🔴 后端服务未运行"; \
	fi
	@if [ -f "frontend.pid" ]; then \
		PID=$$(cat frontend.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "🟢 前端服务运行中 (PID: $$PID)"; \
		else \
			echo "🔴 前端服务已停止"; \
			rm -f frontend.pid; \
		fi; \
	else \
		echo "🔴 前端服务未运行"; \
	fi

# Poetry 管理命令
poetry-shell:
	@echo "🐚 进入 Poetry 虚拟环境..."
	@poetry shell

poetry-show:
	@echo "📋 显示依赖信息..."
	@poetry show

poetry-update:
	@echo "🔄 更新依赖..."
	@poetry update
	@echo "✅ 依赖更新完成"

# 添加依赖
add-dep:
	@echo "📦 添加新依赖..."
	@if [ -z "$(DEP)" ]; then \
		echo "❌ 请指定依赖名称: make add-dep DEP=package_name"; \
		exit 1; \
	fi
	@poetry add $(DEP)
	@echo "✅ 依赖 $(DEP) 添加完成"

# 添加开发依赖
add-dev-dep:
	@echo "📦 添加开发依赖..."
	@if [ -z "$(DEP)" ]; then \
		echo "❌ 请指定依赖名称: make add-dev-dep DEP=package_name"; \
		exit 1; \
	fi
	@poetry add --group dev $(DEP)
	@echo "✅ 开发依赖 $(DEP) 添加完成"

# 移除依赖
remove-dep:
	@echo "🗑️  移除依赖..."
	@if [ -z "$(DEP)" ]; then \
		echo "❌ 请指定依赖名称: make remove-dep DEP=package_name"; \
		exit 1; \
	fi
	@poetry remove $(DEP)
	@echo "✅ 依赖 $(DEP) 移除完成"

# 数据库管理命令
init-db:
	@echo "🗄️ 初始化数据库..."
	@poetry run python scripts/init_db.py
	@echo "✅ 数据库初始化完成"

migrate:
	@echo "🔄 运行数据库迁移..."
	@poetry run aerich upgrade
	@echo "✅ 数据库迁移完成"

makemigrations:
	@echo "📝 创建新的迁移文件..."
	@if [ -z "$(MSG)" ]; then \
		poetry run aerich migrate; \
	else \
		poetry run aerich migrate --name "$(MSG)"; \
	fi
	@echo "✅ 迁移文件创建完成"

reset-db:
	@echo "⚠️  重置数据库..."
	@read -p "确定要重置数据库吗？这将删除所有数据 (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -rf migrations/; \
		rm -f backend/data/aitestlab.db*; \
		echo "🗑️  已删除数据库文件和迁移文件"; \
		$(MAKE) init-db; \
	else \
		echo "❌ 操作已取消"; \
	fi

# 数据库切换命令
switch-to-sqlite:
	@echo "🔄 切换到SQLite数据库..."
	@poetry run python scripts/switch_database.py sqlite
	@echo "💡 请重启应用以使配置生效"

switch-to-mysql:
	@echo "🔄 切换到MySQL数据库..."
	@poetry run python scripts/switch_database.py mysql
	@echo "💡 请重启应用以使配置生效"

db-status:
	@echo "📊 查看当前数据库配置..."
	@poetry run python scripts/switch_database.py status

test-db:
	@echo "🔍 测试数据库连接..."
	@poetry run python scripts/switch_database.py test

# 数据库迁移命令
migrate-sqlite-to-mysql:
	@echo "🚀 从SQLite迁移到MySQL..."
	@poetry run python scripts/migrate_database.py sqlite_to_mysql
	@echo "✅ 数据库迁移完成"

# MySQL设置命令
setup-mysql:
	@echo "🛠️ 设置MySQL数据库..."
	@poetry run python scripts/setup_mysql.py setup
	@echo "✅ MySQL数据库设置完成"

check-mysql:
	@echo "🔍 检查MySQL连接..."
	@poetry run python scripts/setup_mysql.py check

# 测试命令
test:
	@echo "🧪 运行测试..."
	@poetry run pytest tests/ -v
	@echo "✅ 测试完成"

test-coverage:
	@echo "🧪 运行测试并生成覆盖率报告..."
	@poetry run pytest tests/ --cov=backend --cov-report=html --cov-report=term
	@echo "✅ 测试覆盖率报告生成完成"
	@echo "📊 查看详细报告: open htmlcov/index.html"

# Midscene 相关命令
midscene-migrate:
	@echo "🤖 运行 Midscene 数据库迁移..."
	@poetry run aerich upgrade
	@echo "✅ Midscene 数据库迁移完成"

midscene-init:
	@echo "🤖 初始化 Midscene 系统..."
	@$(MAKE) midscene-migrate
	@poetry run python -c "from backend.services.ui_testing.midscene_service import midscene_service; import asyncio; asyncio.run(midscene_service.update_daily_statistics())"
	@echo "✅ Midscene 系统初始化完成"

midscene-clean:
	@echo "🧹 清理 Midscene 上传文件..."
	@rm -rf uploads/midscene/
	@mkdir -p uploads/midscene/
	@echo "✅ Midscene 文件清理完成"

midscene-stats:
	@echo "📊 更新 Midscene 统计数据..."
	@poetry run python -c "from backend.services.ui_testing.midscene_service import midscene_service; import asyncio; asyncio.run(midscene_service.update_daily_statistics())"
	@echo "✅ Midscene 统计数据更新完成"

midscene-test:
	@echo "🧪 测试 Midscene API..."
	@curl -s http://localhost:8000/api/midscene/test | python -m json.tool || echo "❌ Midscene API 测试失败"
	@echo "✅ Midscene API 测试完成"
