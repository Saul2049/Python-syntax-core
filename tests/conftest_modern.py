"""
现代化的pytest配置文件
提供共用fixtures和测试配置
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

# ============================================================================
# 数据 Fixtures
# ============================================================================


@pytest.fixture
def sample_ohlcv_data():
    """提供标准的OHLCV测试数据"""
    dates = pd.date_range("2023-01-01", periods=100, freq="1H")
    np.random.seed(42)  # 确保可重现

    base_price = 100
    returns = np.random.normal(0, 0.02, 100)
    prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "timestamp": dates,
            "open": prices * np.random.uniform(0.99, 1.01, 100),
            "high": prices * np.random.uniform(1.00, 1.02, 100),
            "low": prices * np.random.uniform(0.98, 1.00, 100),
            "close": prices,
            "volume": np.random.randint(1000, 10000, 100),
        }
    ).set_index("timestamp")


@pytest.fixture
def empty_dataframe():
    """空的DataFrame"""
    return pd.DataFrame()


@pytest.fixture
def invalid_data():
    """包含无效数据的DataFrame"""
    return pd.DataFrame(
        {"price": [1, 2, np.nan, np.inf, -np.inf, 5], "volume": [100, np.nan, 300, 400, 500, 600]}
    )


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
    client.get_ticker.return_value = {"symbol": "BTCUSDT", "price": "50000.00"}
    client.get_account.return_value = {"balances": []}
    client.create_order.return_value = {"orderId": 12345, "status": "FILLED"}
    return client


@pytest.fixture
def mock_network_response():
    """模拟网络响应"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"status": "success", "data": {}}
    return response


# ============================================================================
# 交易相关 Fixtures
# ============================================================================


@pytest.fixture
def sample_trade_data():
    """示例交易数据"""
    return {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.1,
        "price": 50000.00,
        "timestamp": pd.Timestamp.now(),
    }


@pytest.fixture
def mock_trading_engine():
    """模拟交易引擎"""
    engine = Mock()
    engine.status = "running"
    engine.get_balance.return_value = 10000.0
    engine.execute_trade.return_value = {"status": "success"}
    engine.analyze_market.return_value = {"signal": "buy", "strength": 0.8}
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
    config.addinivalue_line("markers", "unit: 单元测试标记")
    config.addinivalue_line("markers", "integration: 集成测试标记")
    config.addinivalue_line("markers", "slow: 慢速测试标记")


# ============================================================================
# 测试数据清理
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """自动清理测试文件"""
    yield
    # 测试后清理临时文件
    temp_patterns = ["test_*.tmp", "temp_*.csv", "debug_*.log"]
    for pattern in temp_patterns:
        for file_path in Path(".").glob(pattern):
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
                "duration": end_time - self.start_time,
                "memory_delta": end_memory - self.start_memory,
            }

    return PerformanceMonitor()
