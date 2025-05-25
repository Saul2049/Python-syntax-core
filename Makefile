# 🚀 M4 Trading System Makefile
# Enhanced with M5 Memory & GC Optimization Support + M1 Development Environment

.PHONY: help test coverage lint format clean install canary-testnet monitor-canary m5-quick m5-demo m5-baseline m5-stress dev test-quick docs health-check metrics

# Default help target
help:
	@echo "🚀 M5 Trading System - Available Commands:"
	@echo ""
	@echo "🔧 Development Environment (M1):"
	@echo "  dev               Create venv + install deps + setup pre-commit hooks"
	@echo "  test-quick        Run fast unit tests only"
	@echo "  lint              Run all linting (ruff, black, isort, mypy)"
	@echo "  docs              Start local documentation server"
	@echo "  health-check      Quick system health scan"
	@echo "  metrics           Collect and display system metrics"
	@echo ""
	@echo "📦 Setup & Dependencies:"
	@echo "  install           Install dependencies"
	@echo "  clean             Clean temporary files"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  test              Run all tests"
	@echo "  coverage          Run tests with coverage"
	@echo "  lint              Run linting checks"
	@echo "  format            Format code"
	@echo ""
	@echo "⚡ Performance & Benchmarks:"
	@echo "  perf-benchmark    Run M4 performance benchmarks"
	@echo "  regression-test   Run performance regression tests"
	@echo "  health            Comprehensive system health check"
	@echo ""
	@echo "🕯️ Canary Deployment:"
	@echo "  canary-testnet    Deploy canary to testnet (pairs=BTCUSDT,ETHUSDT funds=500)"
	@echo "  monitor-canary    Monitor canary deployment metrics"
	@echo "  canary-status     Check canary health status"
	@echo "  canary-rollback   Emergency rollback canary"
	@echo ""
	@echo "🧠 M5 Memory & GC Optimization:"
	@echo "  mem-baseline      30-min memory baseline collection"
	@echo "  mem-benchmark     10-min memory benchmark for PR"
	@echo "  mem-snapshot      Take memory snapshot with tracemalloc"
	@echo "  gc-profile        Profile GC performance"
	@echo "  mem-stress-test   24h memory stress testing"
	@echo "  mem-health        Real-time memory health check"
	@echo "  mem-clean         Clean memory analysis artifacts"
	@echo ""
	@echo "🎯 M5 Weekly Validation:"
	@echo "  w1-cache-test     W1: LRU cache validation (RSS↓25%, alloc↓20%)"
	@echo "  w2-gc-optimize    W2: GC optimization (pause↓50%)"
	@echo "  w3-leak-sentinel  W3: 6h leak-free validation"
	@echo "  w4-stress-canary  W4: 24h pressure test"
	@echo "  m5-completion     Check M5 infrastructure completion"
	@echo ""

# 🔧 M1 Development Environment Commands

# One-command development setup
dev:
	@echo "🔧 Setting up development environment..."
	@if [ ! -d ".venv" ]; then \
		echo "📦 Creating virtual environment..."; \
		python3 -m venv .venv; \
	fi
	@echo "⚡ Activating venv and installing dependencies..."
	@.venv/bin/pip install --upgrade pip setuptools wheel
	@.venv/bin/pip install -r requirements.txt
	@if [ -f "requirements-dev.txt" ]; then \
		.venv/bin/pip install -r requirements-dev.txt; \
	else \
		.venv/bin/pip install pytest pytest-cov black isort ruff mypy pre-commit; \
	fi
	@echo "🪝 Setting up pre-commit hooks..."
	@.venv/bin/pre-commit install || echo "pre-commit not available, skipping hooks"
	@echo "✅ Development environment ready!"
	@echo "💡 Activate with: source .venv/bin/activate"

# Fast unit tests for development
test-quick:
	@echo "🧪 Running quick unit tests..."
	python -m pytest tests/ -v -x --tb=short -q --durations=10

# Comprehensive linting
lint:
	@echo "🔍 Running comprehensive linting..."
	@echo "📝 Running ruff..."
	@ruff check src/ tests/ || echo "⚠️ Ruff found issues"
	@echo "🎨 Running black..."
	@black --check src/ tests/ || echo "⚠️ Black formatting needed"
	@echo "🔧 Running isort..."
	@isort --check-only src/ tests/ || echo "⚠️ Import sorting needed"
	@echo "🔍 Running mypy..."
	@mypy src/ || echo "⚠️ Type checking issues found"
	@echo "✅ Linting complete"

# Documentation server
docs:
	@echo "📚 Starting documentation server..."
	@if [ -f "mkdocs.yml" ]; then \
		mkdocs serve; \
	else \
		echo "📝 MkDocs not configured yet"; \
		echo "💡 Consider adding mkdocs.yml for documentation"; \
	fi

# M1 Health Check Integration
health-check:
	@echo "🏥 Quick System Health Check..."
	python scripts/monitoring/health_check.py --mode quick

# M1 Metrics Collection
metrics:
	@echo "📊 Collecting System Metrics..."
	python scripts/monitoring/metrics_collector.py --format json | jq -r '.metrics[] | select(.name | contains("memory") or contains("cpu")) | "\(.name): \(.value)"' 2>/dev/null || python scripts/monitoring/metrics_collector.py

# Dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Testing
test:
	python -m pytest tests/ -v

coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

# Code quality
format:
	black src tests
	isort src tests

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -rf output/temp_* output/*_temp.json

# Performance benchmarks
perf-benchmark:
	@echo "🚀 Running M4 Performance Benchmark..."
	python scripts/performance/m4_simple_benchmark.py

regression-test:
	@echo "🔍 Running Performance Regression Tests..."
	python scripts/performance/performance_regression_test.py

# Canary deployment commands
canary-testnet:
	@echo "🕯️ Starting Canary Deployment to Testnet..."
	@pairs=$${pairs:-BTCUSDT,ETHUSDT}; \
	funds=$${funds:-500}; \
	echo "📊 Trading Pairs: $$pairs"; \
	echo "💰 Test Funds: $$funds USD"; \
	python scripts/deployment/canary_deploy.py --testnet --pairs=$$pairs --funds=$$funds --duration=24h

monitor-canary:
	@echo "📊 Monitoring Canary Deployment..."
	python scripts/deployment/canary_monitor.py --check-all

canary-status:
	@echo "🔍 Checking Canary Health Status..."
	python scripts/deployment/canary_status.py

canary-rollback:
	@echo "🚨 Emergency Canary Rollback..."
	python scripts/deployment/canary_rollback.py --emergency

restart-ws:
	@echo "🔄 Restarting WebSocket connections..."
	python scripts/deployment/restart_websocket.py

fallback-rest:
	@echo "⏮️ Falling back to REST API mode..."
	python scripts/deployment/fallback_rest_mode.py

# Helper targets for CI/CD
health:
	@echo "🏥 System Health Check Report"
	@echo "="*60
	@echo "📅 检查时间: $$(date)"
	@echo ""
	@echo "🧠 内存状态:"
	@make mem-health 2>/dev/null || true
	@echo ""
	@echo "📊 Prometheus指标:"
	@make prometheus-check 2>/dev/null || true
	@echo ""
	@echo "🕯️ Canary状态:"
	@make canary-status 2>/dev/null || true
	@echo ""
	@echo "📈 M5基础设施:"
	@make m5-completion 2>/dev/null || true
	@echo ""
	@echo "✅ 健康检查完成"

assert-p95:
	@threshold=$${threshold:-0.25}; \
	echo "🎯 Asserting P95 latency < $$threshold seconds"; \
	python scripts/health/assert_p95.py $$threshold

# M5 Memory & GC Optimization Commands
mem-baseline:
	@echo "📊 Collecting 30-minute memory baseline..."
	python scripts/memory/mem_baseline.py --duration 1800 --save output/mem_baseline.json

mem-benchmark:
	@echo "🧠 Running 10-minute memory benchmark for PR..."
	python scripts/memory/mem_benchmark.py --duration 600 --diff-threshold 15

mem-snapshot:
	@echo "📸 Taking memory snapshot with tracemalloc..."
	python scripts/memory/mem_snapshot.py --top 20 --save

gc-profile:
	@echo "🗑️ Profiling GC performance..."
	python scripts/memory/gc_profiler.py --duration 300

mem-stress-test:
	@echo "💪 Running 24h memory stress test..."
	python scripts/memory/mem_stress_test.py --duration 24h --max-rss 40

# Memory health checks
mem-health:
	@echo "🏥 Memory health status check..."
	@echo "📊 Current RSS:"
	@ps -o pid,rss,command -p $$(pgrep -f "python.*trading") 2>/dev/null || echo "No trading processes found"
	@echo "🗑️ GC stats:"
	@python -c "import gc; print(f'GC counts: gen0={gc.get_count()[0]}, gen1={gc.get_count()[1]}, gen2={gc.get_count()[2]}')"
	@echo "🔗 Open FDs:"
	@lsof -p $$(pgrep -f "python.*trading") 2>/dev/null | wc -l || echo "Cannot check FDs"

# Clean memory artifacts
mem-clean:
	@echo "🧹 Cleaning memory profile artifacts..."
	rm -f output/mem_*.json output/gc_*.json output/*.tracemalloc
	rm -f *.prof *.memprof

# M5 Weekly Validation Commands

# W1: Cache Optimization Testing
w1-cache-test:
	@echo "🧠 W1: LRU缓存优化验收测试"
	@echo "验收标准: RSS增长<5MB, 内存分配率降低≥20%"
	python scripts/memory/w1_cache_benchmark.py

# W2: GC Optimization
w2-gc-optimize:
	@echo "🗑️ W2: GC优化验收测试"
	@echo "验收标准: GC暂停时间减少≥50%"
	python scripts/memory/gc_profiler.py --duration 600 --optimize
	@echo "✅ 应用最优GC配置..."

# 🔥 W2: 自动化GC调参 (新增)
w2-gc-tuning:
	@echo "🗑️ W2: 自动化GC调参"
	@echo "🎯 目标: GC暂停时间减少≥50%"
	python scripts/memory/w2_gc_tuning.py

# 🔥 W2: 快速GC调参 (FAST模式)
w2-gc-tuning-fast:
	@echo "⚡ W2: 快速GC调参 (1分钟测试)"
	FAST=1 python scripts/memory/w2_gc_tuning.py

# 🔥 W2: 锁定最优配置
w2-lock-config:
	@echo "🔒 W2: 锁定最优GC配置"
	@echo "应用配置: (900, 20, 10)"
	python config/gc_settings.py
	@echo "✅ 配置已锁定并自动应用"

# 🔥 W2: 验证优化效果
w2-validate:
	@echo "🔍 W2: 验证GC优化效果"
	@echo "🎯 检查配置正确性和性能持续性"
	python scripts/testing/w2_validation.py --duration 300

# 🔥 W2: 快速验证 (1分钟)
w2-validate-fast:
	@echo "⚡ W2: 快速验证 (1分钟测试)"
	python scripts/testing/w2_validation.py --duration 60

# 🔥 W2: 自动修复配置
w2-fix-config:
	@echo "🔧 W2: 自动修复GC配置"
	python scripts/testing/w2_validation.py --fix-config --duration 60

# 🔥 W2: 完整流程 (调参→锁定→验证)
w2-complete:
	@echo "🎯 W2: 完整GC优化流程"
	@echo "Step 1: 自动调参..."
	make w2-gc-tuning-fast
	@echo "Step 2: 锁定配置..."
	make w2-lock-config
	@echo "Step 3: 验证效果..."
	make w2-validate-fast
	@echo "✅ W2完整流程完成"

# W3: Leak Detection Sentinel
w3-leak-sentinel:
	@echo "🔍 W3: 连续泄漏监控验收测试"
	@echo "验收标准: 连续6小时无内存泄漏"
	@hours=$${hours:-6}; \
	echo "目标: 连续$$hours小时无泄漏"; \
	python scripts/testing/w3_leak_sentinel.py --target-hours $$hours

# 🔥 W3: 标签化启动
w3-start-tagged:
	@echo "🏷️ W3: 启动带标签的泄漏哨兵"
	@run_name=$${run_name:-W3-Prep}; \
	hours=$${hours:-6}; \
	echo "📋 运行标签: $$run_name"; \
	echo "🎯 目标时长: $$hours 小时"; \
	python scripts/testing/w3_start_sentinel.py --run-name $$run_name --target-hours $$hours

# 🔥 W3: 快速测试 (1小时)
w3-quick-test:
	@echo "⚡ W3: 快速泄漏检测测试 (1小时)"
	python scripts/testing/w3_start_sentinel.py --run-name W3-Quick --target-hours 1 --check-interval 60

# 🔥 W3: 状态检查
w3-status:
	@echo "📊 W3: 哨兵状态检查"
	@run_name=$${run_name:-W3-Prep}; \
	python scripts/testing/w3_start_sentinel.py --run-name $$run_name --status-only

# 🔥 W3: 创建定时任务
w3-schedule:
	@echo "📅 W3: 创建夜间定时任务"
	@run_name=$${run_name:-W3-Nightly}; \
	cron=$${cron:-"0 3 * * *"}; \
	echo "定时: $$cron"; \
	python scripts/testing/w3_start_sentinel.py --run-name $$run_name --create-schedule "$$cron"

# W4: 24h Stress Testing
w4-stress-canary:
	@echo "🔥 W4: 24小时压力Canary测试"
	@echo "验收标准: RSS<40MB, GC pause P95<50ms, 延迟P95≤5.5ms"
	@pairs=$${pairs:-BTCUSDT,ETHUSDT,XRPUSDT}; \
	freq=$${freq:-5}; \
	duration=$${duration:-24}; \
	echo "交易对: $$pairs, 频率: $$freq Hz, 时长: $$duration 小时"; \
	python scripts/testing/w4_stress_canary.py --pairs $$pairs --freq $$freq --duration $$duration

# W4 Dry Run (for testing)
w4-dry-run:
	@echo "🧪 W4: 6分钟压力测试 (干运行)"
	python scripts/testing/w4_stress_canary.py --dry-run --freq 10

# M5 Infrastructure Completion Check
m5-completion:
	@echo "📋 M5基础设施完成度检查"
	python scripts/memory/m5_completion_check.py

# M5 Full Validation Pipeline
m5-full-validation:
	@echo "🎯 M5完整验收流程 (4周计划)"
	@echo "开始完整的M5内存优化验收..."
	make w1-cache-test
	@echo "⏸️ W1完成，等待确认后继续W2..."
	@read -p "继续W2测试? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	make w2-gc-optimize
	@echo "⏸️ W2完成，等待确认后继续W3..."
	@read -p "继续W3测试? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	make w3-leak-sentinel
	@echo "⏸️ W3完成，等待确认后继续W4..."
	@read -p "继续W4测试? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	make w4-stress-canary
	@echo "🎉 M5全部验收完成！"

# Quick M5 Demo (all tests in fast mode)
# 🔥已删除: 旧的m5-demo定义，使用下方的分层测试版本

# Prometheus metrics validation
prometheus-check:
	@echo "📊 检查Prometheus指标可用性..."
	@curl -s http://localhost:8000/metrics | grep -E "(process_memory_rss_bytes|gc_pause_duration_seconds)" || echo "⚠️ 部分M5指标不可用"

# M5内存优化相关命令 - 分层测试策略

# 🔥新增: 快速缓存逻辑验证 (< 1分钟)
m5-quick:
	@echo "⚡ M5快速验证模式 (缓存逻辑检查)"
	@echo "🎯 预期耗时: < 1分钟"
	FAST=1 python scripts/memory/w1_quick_test.py

# 🔥优化: M5演示模式 (2-3分钟)
m5-demo:
	@if [ "$(FAST)" = "1" ]; then \
		echo "⚡ M5超快演示模式 (缩短到30秒)"; \
		FAST=1 DEMO_SIGNALS=200 python scripts/memory/w1_cache_benchmark.py; \
	else \
		echo "🚀 M5标准演示模式 (2-3分钟)"; \
		DEMO_MODE=1 python scripts/memory/w1_cache_benchmark.py; \
	fi

# 🔥新增: 30分钟基线采集 (后台运行)
m5-baseline:
	@echo "📊 M5基线采集模式 (30分钟后台)"
	@echo "🎯 建议: 放到后台运行 - make m5-baseline &"
	python scripts/memory/mem_baseline.py --duration $(or $(duration),1800) --output output/m5_baseline_$(shell date +%s).json

# 🔥新增: 完整压力测试 (小时级)
m5-stress:
	@echo "💪 M5压力测试模式 (长时间高负载)"
	@echo "🎯 预期耗时: 10分钟 - 数小时"
	@echo "⚠️ 建议在独立容器/Screen会话中运行"
	python scripts/memory/w1_cache_benchmark.py --signals $(or $(signals),100000) --duration $(or $(duration),3600)

# 帮助信息
m5-help:
	@echo "🧠 M5内存优化测试命令指南"
	@echo "============================================================"
	@echo "📊 测试级别 (按耗时排序):"
	@echo ""
	@echo "⚡ make m5-quick           # < 1分钟  - 快速缓存逻辑验证"
	@echo "🚀 make m5-demo            # 2-3分钟  - 标准演示测试"  
	@echo "⚡ make m5-demo FAST=1     # 30秒    - 超快演示模式"
	@echo "📊 make m5-baseline &      # 30分钟  - 基线采集(后台)"
	@echo "💪 make m5-stress          # 数小时  - 完整压力测试"
	@echo ""
	@echo "🛠️ 实用工具:"
	@echo "📋 make m5-completion      # M5基础设施检查"
	@echo "📸 make mem-snapshot       # 内存快照"
	@echo "🏥 make mem-health         # 内存健康检查"
	@echo "🧹 make mem-clean          # 清理输出文件"
	@echo ""
	@echo "💡 日常开发建议:"
	@echo "   开发时: make m5-quick"
	@echo "   PR前:   make m5-demo" 
	@echo "   CI/CD:  make m5-baseline & && make m5-demo"
	@echo "============================================================"

# 🔥 W3+W4 并行运行
w3-w4-parallel:
	@echo "🚀 启动 W3+W4 并行验收"
	@echo "🔍 W3: 6小时泄漏哨兵 (W3-Production)"
	@echo "🔥 W4: 24小时压力测试 (W4-stress)"
	@echo "📊 并行监控已启动"
	@echo "======================================="
	@echo "⚠️  资源控制: 总 RSS ≤ 40MB"
	@echo "📋 标签分离: W3-Production + W4-stress"
	@echo "======================================="
	@echo "已运行的任务:"
	@make w3-status run_name=W3-Production
	@echo ""
	@echo "启动并行监控..."
	python scripts/monitoring/w3_w4_parallel_monitor.py --interval 60 &

# 🔥 W3+W4 状态检查
w3-w4-status:
	@echo "📊 W3+W4 并行任务状态"
	@echo "========================="
	@echo "🔍 W3 泄漏哨兵:"
	@make w3-status run_name=W3-Production
	@echo ""
	@echo "🔥 W4 压力测试:"
	@if pgrep -f "w4.*stress" > /dev/null; then \
		echo "   状态: ✅ 运行中"; \
		echo "   进程: $$(pgrep -f 'w4.*stress')"; \
	else \
		echo "   状态: ❌ 未运行"; \
	fi
	@echo ""
	@echo "📊 系统资源:"
	@python -c "import psutil; rss=sum(p.memory_info().rss for p in psutil.process_iter() if 'python' in p.name().lower())/1024/1024; print(f'   总 RSS: {rss:.1f}MB')"

# 🔥 W3+W4 快速报告
w3-w4-report:
	@echo "📋 W3+W4 并行验收报告"
	python scripts/monitoring/w3_w4_parallel_monitor.py --interval 1 --duration 5 --quiet 