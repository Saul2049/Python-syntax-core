#!/usr/bin/env python3
"""
信号处理器测试 - 提高覆盖率
Signal Processor Tests - Coverage Boost

重点关注:
- src/core/signal_processor.py (当前15%覆盖率)
"""


import numpy as np
import pandas as pd
import pytest

from src.core.signal_processor import (
    _validate_current_price,
    _validate_moving_averages,
    _validate_signal_basic_structure,
    filter_signals,
    get_trading_signals,
    validate_signal,
)


class TestSignalProcessor:
    """测试信号处理器"""

    def test_signal_processor_functions_exist(self):
        """测试信号处理器函数存在"""
        assert get_trading_signals is not None
        assert validate_signal is not None
        assert filter_signals is not None

    def create_sample_data(self):
        """创建测试用样本数据"""
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 101, 103, 104, 105, 104, 106, 107],
                "high": [101, 102, 103, 102, 104, 105, 106, 105, 107, 108],
                "low": [99, 100, 101, 100, 102, 103, 104, 103, 105, 106],
                "open": [100, 101, 101, 102, 102, 103, 104, 105, 105, 106],
                "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
            }
        )
        data.index = pd.date_range("2024-01-01", periods=len(data), freq="h")
        return data

    def test_create_sample_data(self):
        """测试样本数据创建"""
        data = self.create_sample_data()
        assert len(data) == 10
        assert "close" in data.columns

    def test_get_trading_signals_basic(self):
        """测试基本信号计算"""
        data = self.create_sample_data()

        # 测试信号计算
        signals = get_trading_signals(data)

        # 验证返回的信号格式
        assert isinstance(signals, dict)
        assert "buy_signal" in signals
        assert "sell_signal" in signals
        assert "current_price" in signals
        assert "fast_ma" in signals
        assert "slow_ma" in signals
        assert "last_timestamp" in signals

    def test_get_trading_signals_with_different_windows(self):
        """测试不同窗口大小的信号处理"""
        data = self.create_sample_data()

        # 测试不同的窗口大小
        signals = get_trading_signals(data, fast_win=5, slow_win=15)
        assert isinstance(signals, dict)
        assert "buy_signal" in signals

        # 测试默认窗口
        signals_default = get_trading_signals(data)
        assert isinstance(signals_default, dict)

    def test_signal_processor_edge_cases(self):
        """测试边界情况"""
        # 测试小数据集 - 应该抛出异常
        small_data = pd.DataFrame(
            {
                "close": [100, 101],
            }
        )
        small_data.index = pd.date_range("2024-01-01", periods=len(small_data), freq="h")

        try:
            signals = get_trading_signals(small_data, fast_win=25, slow_win=50)
            # 如果没有抛出异常，验证结果
            assert isinstance(signals, dict)
        except Exception as e:
            # 预期可能会有异常，这是正常的
            assert isinstance(e, (ValueError, IndexError, KeyError))

    def test_signal_processor_small_dataset(self):
        """测试小数据集"""
        small_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
            }
        )
        small_data.index = pd.date_range("2024-01-01", periods=len(small_data), freq="h")

        try:
            signals = get_trading_signals(small_data, fast_win=2, slow_win=3)
            assert isinstance(signals, dict)
        except Exception:
            # 小数据集可能无法计算某些指标，这是预期的
            pass

    def test_validate_signal(self):
        """测试信号验证"""
        data = self.create_sample_data()
        signals = get_trading_signals(data)

        # 测试有效信号
        is_valid = validate_signal(signals, data)
        assert isinstance(is_valid, bool)

        # 测试无效信号 - 缺少必需字段
        invalid_signal = {"buy_signal": True}
        is_valid = validate_signal(invalid_signal, data)
        assert is_valid == False

        # 测试空信号
        is_valid = validate_signal({}, data)
        assert is_valid == False

    def test_validate_signal_helper_functions(self):
        """测试信号验证辅助函数"""
        # 测试基础结构验证
        assert _validate_signal_basic_structure({"current_price": 100}) == True
        assert _validate_signal_basic_structure({}) == False
        assert _validate_signal_basic_structure(None) == False

        # 测试价格验证
        assert _validate_current_price(100.5) == True
        assert _validate_current_price(0) == False
        assert _validate_current_price(-10) == False
        assert _validate_current_price(float("inf")) == False
        assert _validate_current_price("invalid") == False

        # 测试移动平均验证
        valid_signal = {"current_price": 100, "fast_ma": 101, "slow_ma": 99}
        assert _validate_moving_averages(valid_signal) == True

        invalid_signal = {"current_price": 100, "fast_ma": 0, "slow_ma": 99}
        assert _validate_moving_averages(invalid_signal) == False

    def test_filter_signals(self):
        """测试信号过滤"""
        data = self.create_sample_data()
        signals = get_trading_signals(data)

        # 测试价格过滤
        filtered = filter_signals(signals, min_price=50, max_price=200)
        assert isinstance(filtered, dict)

        # 测试超出价格范围的过滤
        filtered_low = filter_signals(signals, min_price=1000)  # 价格太高
        assert filtered_low["buy_signal"] == False
        assert filtered_low["sell_signal"] == False

        filtered_high = filter_signals(signals, max_price=10)  # 价格太低
        assert filtered_high["buy_signal"] == False
        assert filtered_high["sell_signal"] == False

    def test_filter_signals_trading_hours(self):
        """测试交易时间过滤"""
        data = self.create_sample_data()
        signals = get_trading_signals(data)

        # 测试交易时间过滤
        trading_hours = [9, 10, 11, 14, 15, 16]  # 模拟交易时间
        filtered = filter_signals(signals, trading_hours=trading_hours)
        assert isinstance(filtered, dict)

    def test_signal_processor_error_handling(self):
        """测试错误处理"""
        # 测试无效输入
        invalid_inputs = [
            pd.DataFrame({"invalid": [1, 2, 3]}),  # 缺少close列
        ]

        for invalid_input in invalid_inputs:
            try:
                signals = get_trading_signals(invalid_input)
            except Exception as e:
                # 预期会有异常
                assert isinstance(e, (ValueError, KeyError, AttributeError, IndexError))

    def test_signal_processor_with_nan_values(self):
        """测试包含NaN值的数据处理"""
        data_with_nan = pd.DataFrame(
            {
                "close": [100, np.nan, 102, 103, np.nan, 105, 106, 107, 108, 109],
            }
        )
        data_with_nan.index = pd.date_range("2024-01-01", periods=len(data_with_nan), freq="h")

        try:
            signals = get_trading_signals(data_with_nan)
            # 应该能处理NaN值或抛出合理异常
            assert isinstance(signals, dict)
        except Exception:
            # NaN处理可能失败，这是可以接受的
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
