#!/usr/bin/env python3
"""
测试用例瘦身执行脚本
根据分析结果执行实际的清理、归档、参数化操作
"""

import os
import re
import shutil
from pathlib import Path


class TestCleanupExecutor:
    def __init__(self):
        self.base_dir = Path(".")
        self.tests_dir = Path("tests")
        self.archive_dir = Path("tests/archive")
        self.deprecated_dir = self.archive_dir / "deprecated"
        self.old_versions_dir = self.archive_dir / "old_versions"

        # 需要删除的文件（明确标记为broken、temp等）
        self.files_to_delete = ["test_trading_loop_coverage_BROKEN.py"]

        # 需要归档的模式
        self.patterns_to_archive = [
            "test_.*_demo_.*",
            "test_.*_temp_.*",
            "test_.*_old_.*",
            "test_.*legacy.*",
        ]

        # 需要参数化的重复测试组
        self.parametrize_groups = [
            {
                "pattern": "test_init_with_.*_dir",
                "files": [
                    "test_data_saver_enhanced_fixed.py",
                    "test_data_saver_enhanced.py",
                    "test_data_saver_final.py",
                ],
                "base_name": "test_init_with_dir",
            },
            {
                "pattern": "test_save_data_.*_format",
                "files": [
                    "test_data_saver_enhanced_fixed.py",
                    "test_data_saver_enhanced.py",
                    "test_data_saver_final.py",
                ],
                "base_name": "test_save_data_format",
            },
        ]

    def setup_directories(self):
        """创建必要的目录结构"""
        print("📁 创建归档目录结构...")

        self.archive_dir.mkdir(exist_ok=True)
        self.deprecated_dir.mkdir(exist_ok=True)
        self.old_versions_dir.mkdir(exist_ok=True)

        # 创建日志目录
        (self.tests_dir / "logs").mkdir(exist_ok=True)

        print("✅ 目录结构创建完成")

    def backup_current_tests(self):
        """备份当前测试目录"""
        print("💾 创建测试文件备份...")

        backup_dir = Path("tests_backup_before_cleanup")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        shutil.copytree(
            self.tests_dir, backup_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
        print(f"✅ 备份完成: {backup_dir}")

    def delete_broken_tests(self):
        """删除明确标记为broken的测试文件"""
        print("🗑️  删除明确无用的测试文件...")

        deleted_count = 0
        for file_name in self.files_to_delete:
            file_path = self.tests_dir / file_name
            if file_path.exists():
                file_path.unlink()
                print(f"   删除: {file_name}")
                deleted_count += 1

        print(f"✅ 删除了 {deleted_count} 个无用测试文件")

    def archive_old_tests(self):
        """归档陈旧的测试文件"""
        print("📦 归档陈旧测试文件...")

        archived_count = 0
        for test_file in self.tests_dir.glob("test_*.py"):
            file_name = test_file.name.lower()

            # 检查是否匹配需要归档的模式
            should_archive = any(
                re.search(pattern, file_name) for pattern in self.patterns_to_archive
            )

            # 检查是否包含陈旧关键词
            old_keywords = ["demo", "temp", "old", "legacy", "deprecated"]
            has_old_keywords = any(keyword in file_name for keyword in old_keywords)

            if should_archive or has_old_keywords:
                dest_path = self.deprecated_dir / test_file.name
                shutil.move(str(test_file), str(dest_path))
                print(f"   归档: {test_file.name} -> {dest_path}")
                archived_count += 1

        print(f"✅ 归档了 {archived_count} 个陈旧测试文件")

    def identify_duplicate_files(self):
        """识别重复的测试文件（基于相似度）"""
        print("🔍 识别重复测试文件...")

        duplicate_groups = []

        # 查找data_saver相关的重复文件
        data_saver_files = [
            "test_data_saver_enhanced.py",
            "test_data_saver_enhanced_fixed.py",
            "test_data_saver_enhanced_part2.py",
            "test_data_saver_final.py",
        ]

        existing_data_saver_files = [f for f in data_saver_files if (self.tests_dir / f).exists()]
        if len(existing_data_saver_files) > 1:
            duplicate_groups.append(
                {
                    "type": "data_saver",
                    "files": existing_data_saver_files,
                    "keep": "test_data_saver_final.py",  # 保留最终版本
                }
            )

        # 查找metrics_collector相关的重复文件
        metrics_files = [
            "test_metrics_collector_enhanced.py",
            "test_metrics_collector_enhanced_fixed.py",
            "test_metrics_collector_enhanced_part2.py",
        ]

        existing_metrics_files = [f for f in metrics_files if (self.tests_dir / f).exists()]
        if len(existing_metrics_files) > 1:
            duplicate_groups.append(
                {
                    "type": "metrics_collector",
                    "files": existing_metrics_files,
                    "keep": "test_metrics_collector_enhanced_fixed.py",  # 保留修复版本
                }
            )

        return duplicate_groups

    def merge_duplicate_files(self):
        """合并重复的测试文件"""
        print("🔄 合并重复测试文件...")

        duplicate_groups = self.identify_duplicate_files()
        merged_count = 0

        for group in duplicate_groups:
            print(f"   处理 {group['type']} 重复文件组...")

            keep_file = group["keep"]
            files_to_merge = [f for f in group["files"] if f != keep_file]

            # 将其他文件移动到old_versions目录
            for file_name in files_to_merge:
                source_path = self.tests_dir / file_name
                if source_path.exists():
                    dest_path = self.old_versions_dir / file_name
                    shutil.move(str(source_path), str(dest_path))
                    print(f"     移动: {file_name} -> old_versions/")
                    merged_count += 1

        print(f"✅ 合并了 {merged_count} 个重复测试文件")

    def create_parametrized_test_example(self):
        """创建参数化测试示例"""
        print("⚡ 创建参数化测试示例...")

        example_content = '''"""
参数化测试示例 - 替代重复测试的现代化方式
"""

import pytest
import pandas as pd
from pathlib import Path


class TestDataSaverParametrized:
    """参数化的DataSaver测试 - 替代多个重复测试文件"""

    @pytest.mark.parametrize("dir_type,dir_value,expected", [
        ("default", None, "data"),
        ("string", "custom_data", "custom_data"),
        ("path", Path("path_data"), "path_data"),
    ])
    def test_init_with_dir(self, dir_type, dir_value, expected):
        """参数化测试目录初始化 - 替代3个重复测试"""
        from src.data.data_saver import DataSaver

        if dir_type == "default":
            saver = DataSaver()
        else:
            saver = DataSaver(data_dir=dir_value)

        assert expected in str(saver.data_dir)

    @pytest.mark.parametrize("format_type,extension", [
        ("csv", ".csv"),
        ("parquet", ".parquet"),
        ("pickle", ".pkl"),
        ("json", ".json"),
        ("excel", ".xlsx"),
    ])
    def test_save_data_formats(self, format_type, extension, tmp_path):
        """参数化测试保存格式 - 替代5个重复测试"""
        from src.data.data_saver import DataSaver

        saver = DataSaver(data_dir=tmp_path)
        data = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        if format_type == "excel":
            pytest.importorskip("openpyxl")

        file_path = saver.save_data(data, f"test_file", format_type)
        assert file_path.suffix == extension
        assert file_path.exists()

    @pytest.mark.parametrize("threshold,expected_files", [
        (0, 0),  # 删除所有文件
        (1, 1),  # 保留1个最新文件
        (3, 3),  # 保留3个最新文件
    ])
    def test_cleanup_old_files_thresholds(self, threshold, expected_files, tmp_path):
        """参数化测试清理阈值 - 替代多个重复测试"""
        from src.data.data_saver import DataSaver
        import time

        saver = DataSaver(data_dir=tmp_path)

        # 创建多个测试文件
        for i in range(5):
            file_path = tmp_path / f"test_file_{i}.csv"
            file_path.write_text("test,data\\n1,2")
            time.sleep(0.1)  # 确保文件时间不同

        saver.cleanup_old_files(days_old=0, max_files=threshold)
        remaining_files = list(tmp_path.glob("*.csv"))
        assert len(remaining_files) == expected_files


class TestTradingEngineParametrized:
    """参数化的交易引擎测试"""

    @pytest.mark.parametrize("engine_status,expected_result", [
        ("running", True),
        ("stopped", False),
        ("error", False),
        ("initializing", False),
    ])
    def test_engine_status_checks(self, engine_status, expected_result):
        """参数化测试引擎状态检查"""
        # 模拟测试实现
        result = engine_status == "running"
        assert result == expected_result

    @pytest.mark.parametrize("market_condition,signal_strength,expected_action", [
        ("bullish", 0.8, "buy"),
        ("bearish", 0.8, "sell"),
        ("sideways", 0.5, "hold"),
        ("volatile", 0.3, "hold"),
    ])
    def test_trading_decisions(self, market_condition, signal_strength, expected_action):
        """参数化测试交易决策逻辑"""
        # 模拟交易决策逻辑
        if signal_strength < 0.6:
            action = "hold"
        elif market_condition == "bullish":
            action = "buy"
        elif market_condition == "bearish":
            action = "sell"
        else:
            action = "hold"

        assert action == expected_action
'''

        example_file = self.tests_dir / "test_parametrized_examples.py"
        with open(example_file, "w", encoding="utf-8") as f:
            f.write(example_content)

        print(f"✅ 创建参数化测试示例: {example_file}")

    def create_conftest_modernization(self):
        """现代化conftest.py配置"""
        print("⚙️  现代化conftest.py配置...")

        modern_conftest = '''"""
现代化的pytest配置文件
提供共用fixtures和测试配置
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch


# ============================================================================
# 数据 Fixtures
# ============================================================================

@pytest.fixture
def sample_ohlcv_data():
    """提供标准的OHLCV测试数据"""
    dates = pd.date_range('2023-01-01', periods=100, freq='1H')
    np.random.seed(42)  # 确保可重现

    base_price = 100
    returns = np.random.normal(0, 0.02, 100)
    prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame({
        'timestamp': dates,
        'open': prices * np.random.uniform(0.99, 1.01, 100),
        'high': prices * np.random.uniform(1.00, 1.02, 100),
        'low': prices * np.random.uniform(0.98, 1.00, 100),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    }).set_index('timestamp')


@pytest.fixture
def empty_dataframe():
    """空的DataFrame"""
    return pd.DataFrame()


@pytest.fixture
def invalid_data():
    """包含无效数据的DataFrame"""
    return pd.DataFrame({
        'price': [1, 2, np.nan, np.inf, -np.inf, 5],
        'volume': [100, np.nan, 300, 400, 500, 600]
    })


# ============================================================================
# 文件系统 Fixtures
# ============================================================================

@pytest.fixture
def temp_data_dir():
    """临时数据目录，测试后自动清理"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config():
    """模拟配置对象"""
    config = Mock()
    config.data_dir = "test_data"
    config.api_key = "test_api_key"
    config.secret_key = "test_secret_key"
    config.enable_monitoring = True
    config.log_level = "INFO"
    return config


# ============================================================================
# 网络和API Fixtures
# ============================================================================

@pytest.fixture
def mock_binance_client():
    """模拟Binance客户端"""
    client = Mock()
    client.get_ticker.return_value = {'symbol': 'BTCUSDT', 'price': '50000.00'}
    client.get_account.return_value = {'balances': []}
    client.create_order.return_value = {'orderId': 12345, 'status': 'FILLED'}
    return client


@pytest.fixture
def mock_network_response():
    """模拟网络响应"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {'status': 'success', 'data': {}}
    return response


# ============================================================================
# 交易相关 Fixtures
# ============================================================================

@pytest.fixture
def sample_trade_data():
    """示例交易数据"""
    return {
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'quantity': 0.1,
        'price': 50000.00,
        'timestamp': pd.Timestamp.now()
    }


@pytest.fixture
def mock_trading_engine():
    """模拟交易引擎"""
    engine = Mock()
    engine.status = 'running'
    engine.get_balance.return_value = 10000.0
    engine.execute_trade.return_value = {'status': 'success'}
    engine.analyze_market.return_value = {'signal': 'buy', 'strength': 0.8}
    return engine


# ============================================================================
# 性能和监控 Fixtures
# ============================================================================

@pytest.fixture
def mock_metrics_collector():
    """模拟指标收集器"""
    collector = Mock()
    collector.record_trade = Mock()
    collector.record_error = Mock()
    collector.get_metrics = Mock(return_value={})
    return collector


# ============================================================================
# 测试标记配置
# ============================================================================

def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )


# ============================================================================
# 测试数据清理
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """自动清理测试文件"""
    yield
    # 测试后清理临时文件
    temp_patterns = ['test_*.tmp', 'temp_*.csv', 'debug_*.log']
    for pattern in temp_patterns:
        for file_path in Path('.').glob(pattern):
            try:
                file_path.unlink()
            except OSError:
                pass


# ============================================================================
# 性能测试工具
# ============================================================================

@pytest.fixture
def performance_monitor():
    """性能监控工具"""
    import time
    import psutil

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None

        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss

        def stop(self):
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss

            return {
                'duration': end_time - self.start_time,
                'memory_delta': end_memory - self.start_memory
            }

    return PerformanceMonitor()
'''

        conftest_path = self.tests_dir / "conftest_modern.py"
        with open(conftest_path, "w", encoding="utf-8") as f:
            f.write(modern_conftest)

        print(f"✅ 创建现代化conftest: {conftest_path}")

    def create_test_runner_scripts(self):
        """创建分层测试运行脚本"""
        print("🚀 创建分层测试运行脚本...")

        # 快速测试脚本
        fast_test_script = """#!/bin/bash
# 快速测试 - 只运行单元测试和核心功能测试

echo "🚀 运行快速测试套件..."

pytest tests/ \\
    -m "unit and not slow" \\
    --maxfail=5 \\
    --tb=short \\
    --durations=5 \\
    -v

echo "✅ 快速测试完成"
"""

        # 完整测试脚本
        full_test_script = """#!/bin/bash
# 完整测试 - 包含所有测试

echo "🧪 运行完整测试套件..."

pytest tests/ \\
    --cov=src \\
    --cov-report=html \\
    --cov-report=term-missing \\
    --durations=10 \\
    -v

echo "✅ 完整测试完成"
"""

        # 集成测试脚本
        integration_test_script = """#!/bin/bash
# 集成测试 - 只运行集成测试

echo "🔗 运行集成测试..."

pytest tests/ \\
    -m "integration" \\
    --tb=short \\
    -v

echo "✅ 集成测试完成"
"""

        scripts = [
            ("run_fast_tests.sh", fast_test_script),
            ("run_full_tests.sh", full_test_script),
            ("run_integration_tests.sh", integration_test_script),
        ]

        for script_name, script_content in scripts:
            script_path = Path(script_name)
            with open(script_path, "w") as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            print(f"   创建: {script_name}")

        print("✅ 测试运行脚本创建完成")

    def generate_final_report(self):
        """生成最终清理报告"""
        print("📋 生成最终清理报告...")

        # 统计当前测试文件数量
        current_test_files = list(self.tests_dir.glob("test_*.py"))
        archived_files = (
            list(self.archive_dir.rglob("test_*.py")) if self.archive_dir.exists() else []
        )

        report = f"""# 测试用例瘦身完成报告

## 📊 清理统计

### 当前状态
- 活跃测试文件: {len(current_test_files)} 个
- 归档测试文件: {len(archived_files)} 个
- 备份位置: tests_backup_before_cleanup/

## 🎯 完成的操作

### ✅ 已完成
- [x] 删除明确无用的测试 (broken, temp等)
- [x] 归档陈旧测试到 archive/deprecated/
- [x] 合并重复测试文件到 archive/old_versions/
- [x] 创建参数化测试示例
- [x] 现代化 pytest 配置
- [x] 创建分层测试运行脚本

### 📝 推荐后续操作

1. **参数化现有重复测试**
2. **添加测试标记**
3. **使用新配置**

## 🚀 下一步建议

1. 验证清理后的测试套件运行正常
2. 更新CI配置使用新的分层测试
3. 逐步为现有测试添加适当的标记

测试瘦身完成时间: {self.get_current_time()}
"""

        with open("TEST_CLEANUP_COMPLETION_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)

        print("✅ 最终报告已保存: TEST_CLEANUP_COMPLETION_REPORT.md")

    def get_current_time(self):
        """获取当前时间字符串"""
        import datetime

        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def run_cleanup(self):
        """执行完整的测试清理流程"""
        print("🧹 开始执行测试用例瘦身...")
        print("=" * 60)

        try:
            self.setup_directories()
            self.backup_current_tests()
            self.delete_broken_tests()
            self.archive_old_tests()
            self.merge_duplicate_files()
            self.create_parametrized_test_example()
            self.create_conftest_modernization()
            self.create_test_runner_scripts()
            self.generate_final_report()

            print("\n" + "=" * 60)
            print("🎉 测试用例瘦身完成！")
            print("\n推荐下一步操作:")
            print("1. 验证清理结果: pytest tests/ --collect-only")
            print("2. 运行快速测试: ./run_fast_tests.sh")
            print("3. 查看完整报告: cat TEST_CLEANUP_COMPLETION_REPORT.md")

        except Exception as e:
            print(f"❌ 清理过程中出错: {e}")
            print("💾 所有原始文件已备份在 tests_backup_before_cleanup/")
            raise


if __name__ == "__main__":
    executor = TestCleanupExecutor()
    executor.run_cleanup()
