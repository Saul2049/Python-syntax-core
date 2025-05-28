#!/usr/bin/env python3
"""
测试核心信号处理器模块 (Test Core Signal Processor Module)
"""

from datetime import datetime
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.core.signal_processor import (
    filter_signals,
    get_trading_signals,
    validate_signal,
)


class TestGetTradingSignals:
    """测试获取交易信号功能 (Test Get Trading Signals)"""

    @pytest.fixture
    def sample_price_data(self):
        """创建示例价格数据"""
        dates = pd.date_range("2023-01-01", periods=50, freq="D")
        np.random.seed(42)

        # 创建具有趋势的价格数据
        base_price = 100
        trend = np.linspace(0, 10, 50)  # 上升趋势
        noise = np.random.normal(0, 1, 50)
        prices = base_price + trend + noise

        return pd.DataFrame(
            {
                "close": prices,
                "open": prices * 0.99,
                "high": prices * 1.02,
                "low": prices * 0.98,
                "volume": np.random.randint(1000, 10000, 50),
            },
            index=dates,
        )

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_basic(self, mock_ma, sample_price_data):
        """测试基本交易信号获取"""
        # 设置移动平均线模拟返回值
        fast_ma_values = [101, 102, 103, 104, 105] + [106] * 45
        slow_ma_values = [100, 100.5, 101, 101.5, 102] + [102.5] * 45

        mock_ma.side_effect = [
            pd.Series(fast_ma_values, index=sample_price_data.index),
            pd.Series(slow_ma_values, index=sample_price_data.index),
        ]

        result = get_trading_signals(sample_price_data, fast_win=7, slow_win=25)

        # 验证返回的信号结构
        expected_keys = [
            "buy_signal",
            "sell_signal",
            "current_price",
            "fast_ma",
            "slow_ma",
            "last_timestamp",
        ]
        for key in expected_keys:
            assert key in result

        # 验证数据类型 - 修复数据类型检查，包括numpy类型
        assert isinstance(result["buy_signal"], bool)
        assert isinstance(result["sell_signal"], bool)
        assert isinstance(result["current_price"], (int, float, np.number))
        assert isinstance(result["fast_ma"], (int, float, np.number))
        assert isinstance(result["slow_ma"], (int, float, np.number))

        # 验证移动平均线函数被正确调用
        assert mock_ma.call_count == 2
        # 使用任何调用检查，避免Series比较问题
        call_args_list = mock_ma.call_args_list
        assert len(call_args_list) == 2
        # 检查窗口参数
        assert call_args_list[0][0][1] == 7  # fast_win
        assert call_args_list[1][0][1] == 25  # slow_win

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_golden_cross(self, mock_ma, sample_price_data):
        """测试金叉信号（快线上穿慢线）"""
        # 设置金叉场景：快线从下方穿越慢线
        fast_ma_values = [99] * 48 + [99.5, 101.5]  # 倒数第二个值小于慢线，最后一个值大于慢线
        slow_ma_values = [100] * 50  # 慢线保持不变

        mock_ma.side_effect = [
            pd.Series(fast_ma_values, index=sample_price_data.index),
            pd.Series(slow_ma_values, index=sample_price_data.index),
        ]

        result = get_trading_signals(sample_price_data)

        # 应该产生买入信号 (前一刻快线<=慢线，当前快线>慢线)
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False
        assert float(result["fast_ma"]) > float(result["slow_ma"])

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_death_cross(self, mock_ma, sample_price_data):
        """测试死叉信号（快线下穿慢线）"""
        # 设置死叉场景：快线从上方穿越慢线
        fast_ma_values = [101] * 48 + [100.5, 98.5]  # 倒数第二个值大于慢线，最后一个值小于慢线
        slow_ma_values = [100] * 50  # 慢线保持不变

        mock_ma.side_effect = [
            pd.Series(fast_ma_values, index=sample_price_data.index),
            pd.Series(slow_ma_values, index=sample_price_data.index),
        ]

        result = get_trading_signals(sample_price_data)

        # 应该产生卖出信号 (前一刻快线>=慢线，当前快线<慢线)
        assert result["buy_signal"] is False
        assert result["sell_signal"] is True
        assert float(result["fast_ma"]) < float(result["slow_ma"])

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_no_cross(self, mock_ma, sample_price_data):
        """测试无交叉信号"""
        # 设置无交叉场景：快线始终高于慢线
        fast_ma_values = [101] * 50
        slow_ma_values = [100] * 50

        mock_ma.side_effect = [
            pd.Series(fast_ma_values, index=sample_price_data.index),
            pd.Series(slow_ma_values, index=sample_price_data.index),
        ]

        result = get_trading_signals(sample_price_data)

        # 应该没有信号
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_custom_windows(self, mock_ma, sample_price_data):
        """测试自定义窗口参数"""
        fast_ma_values = [101] * 50
        slow_ma_values = [100] * 50

        mock_ma.side_effect = [
            pd.Series(fast_ma_values, index=sample_price_data.index),
            pd.Series(slow_ma_values, index=sample_price_data.index),
        ]

        _ = get_trading_signals(sample_price_data, fast_win=10, slow_win=30)

        # 验证使用了自定义参数 - 使用call_args_list检查参数
        call_args_list = mock_ma.call_args_list
        assert len(call_args_list) == 2
        # 检查第一个调用的第二个参数（窗口大小）
        assert call_args_list[0][0][1] == 10
        assert call_args_list[1][0][1] == 30
        # 检查关键字参数
        assert call_args_list[0][1]["kind"] == "ema"
        assert call_args_list[1][1]["kind"] == "ema"

    def test_get_trading_signals_single_row_data(self):
        """测试单行数据的处理"""
        single_row_data = pd.DataFrame(
            {"close": [100.0], "open": [99.0], "high": [101.0], "low": [98.0], "volume": [5000]},
            index=[datetime(2023, 1, 1)],
        )

        with patch("src.core.signal_processor.moving_average") as mock_ma:
            mock_ma.side_effect = [
                pd.Series([100.0], index=single_row_data.index),
                pd.Series([100.0], index=single_row_data.index),
            ]

            result = get_trading_signals(single_row_data)

            assert result["current_price"] == 100.0
            assert result["buy_signal"] is False  # 单行数据无法产生交叉信号
            assert result["sell_signal"] is False

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_nan_values(self, mock_ma, sample_price_data):
        """测试包含NaN值的移动平均线处理"""
        # 创建包含NaN的移动平均线数据
        fast_ma_values = [np.nan, np.nan, 101, 102, 103] + [104] * 45
        slow_ma_values = [np.nan] * 5 + [100] * 45

        mock_ma.side_effect = [
            pd.Series(fast_ma_values, index=sample_price_data.index),
            pd.Series(slow_ma_values, index=sample_price_data.index),
        ]

        result = get_trading_signals(sample_price_data)

        # 验证函数能处理NaN值而不崩溃
        assert isinstance(result, dict)
        assert "buy_signal" in result
        assert "sell_signal" in result

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_extreme_values(self, mock_ma, sample_price_data):
        """测试极端价格值"""
        # 设置极端的移动平均线值
        fast_ma_values = [1e6] * 50  # 非常大的值
        slow_ma_values = [1e-6] * 50  # 非常小的值

        mock_ma.side_effect = [
            pd.Series(fast_ma_values, index=sample_price_data.index),
            pd.Series(slow_ma_values, index=sample_price_data.index),
        ]

        result = get_trading_signals(sample_price_data)

        # 验证函数能处理极端值
        assert isinstance(result["fast_ma"], (int, float, np.number))
        assert isinstance(result["slow_ma"], (int, float, np.number))
        assert result["fast_ma"] > result["slow_ma"]

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_equal_ma_values(self, mock_ma, sample_price_data):
        """测试移动平均线相等的情况"""
        # 设置相等的移动平均线值
        ma_values = [100] * 50

        mock_ma.side_effect = [
            pd.Series(ma_values, index=sample_price_data.index),
            pd.Series(ma_values, index=sample_price_data.index),
        ]

        result = get_trading_signals(sample_price_data)

        # 相等情况下不应产生交叉信号
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False
        assert result["fast_ma"] == result["slow_ma"]


class TestValidateSignal:
    """测试信号验证功能 (Test Signal Validation)"""

    @pytest.fixture
    def sample_price_data(self):
        """创建示例价格数据"""
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        return pd.DataFrame(
            {"close": prices, "open": prices, "high": prices, "low": prices, "volume": [1000] * 10},
            index=dates,
        )

    def test_validate_signal_valid_signal(self, sample_price_data):
        """测试有效信号验证"""
        valid_signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
            "last_timestamp": datetime(2023, 1, 10),
        }

        result = validate_signal(valid_signal, sample_price_data)
        assert result is True

    def test_validate_signal_empty_signal(self, sample_price_data):
        """测试空信号验证"""
        empty_signal = {}
        result = validate_signal(empty_signal, sample_price_data)
        assert result is False

    def test_validate_signal_none_signal(self, sample_price_data):
        """测试None信号验证"""
        result = validate_signal(None, sample_price_data)
        assert result is False

    def test_validate_signal_missing_current_price(self, sample_price_data):
        """测试缺少当前价格的信号"""
        signal_without_price = {
            "buy_signal": True,
            "sell_signal": False,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = validate_signal(signal_without_price, sample_price_data)
        assert result is False

    def test_validate_signal_negative_price(self, sample_price_data):
        """测试负价格信号"""
        negative_price_signal = {"current_price": -10.0, "fast_ma": 104.0, "slow_ma": 103.0}

        result = validate_signal(negative_price_signal, sample_price_data)
        assert result is False

    def test_validate_signal_zero_price(self, sample_price_data):
        """测试零价格信号"""
        zero_price_signal = {"current_price": 0.0, "fast_ma": 104.0, "slow_ma": 103.0}

        result = validate_signal(zero_price_signal, sample_price_data)
        assert result is False

    def test_validate_signal_negative_ma(self, sample_price_data):
        """测试负移动平均线值"""
        negative_ma_signal = {"current_price": 105.0, "fast_ma": -10.0, "slow_ma": 103.0}

        result = validate_signal(negative_ma_signal, sample_price_data)
        assert result is False

    def test_validate_signal_excessive_price_deviation(self, sample_price_data):
        """测试价格偏离过大的信号"""
        excessive_deviation_signal = {
            "current_price": 200.0,  # 相对于快线104.0偏离过大
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = validate_signal(excessive_deviation_signal, sample_price_data)
        assert result is False

    def test_validate_signal_acceptable_price_deviation(self, sample_price_data):
        """测试可接受价格偏离的信号"""
        acceptable_deviation_signal = {
            "current_price": 108.0,  # 相对于快线104.0偏离约3.8%，在10%限制内
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = validate_signal(acceptable_deviation_signal, sample_price_data)
        assert result is True

    def test_validate_signal_without_ma_values(self, sample_price_data):
        """测试没有移动平均线值的信号"""
        signal_without_ma = {"current_price": 105.0, "buy_signal": True, "sell_signal": False}

        result = validate_signal(signal_without_ma, sample_price_data)
        assert result is True  # 没有MA值时只检查价格

    def test_validate_signal_inf_price(self, sample_price_data):
        """测试无穷大价格值"""
        inf_price_signal = {"current_price": float("inf"), "fast_ma": 104.0, "slow_ma": 103.0}

        result = validate_signal(inf_price_signal, sample_price_data)
        assert result is False

    def test_validate_signal_nan_price(self, sample_price_data):
        """测试NaN价格值"""
        nan_price_signal = {"current_price": float("nan"), "fast_ma": 104.0, "slow_ma": 103.0}

        result = validate_signal(nan_price_signal, sample_price_data)
        assert result is False

    def test_validate_signal_nan_ma_values(self, sample_price_data):
        """测试NaN移动平均线值"""
        nan_ma_signal = {"current_price": 105.0, "fast_ma": float("nan"), "slow_ma": 103.0}

        result = validate_signal(nan_ma_signal, sample_price_data)
        assert result is False

    def test_validate_signal_missing_one_ma(self, sample_price_data):
        """测试只有一个移动平均线的信号"""
        partial_ma_signal = {
            "current_price": 105.0,
            "fast_ma": 104.0,
            # 缺少slow_ma
        }

        result = validate_signal(partial_ma_signal, sample_price_data)
        assert result is True  # 只要价格有效就可以

    def test_validate_signal_zero_ma_values(self, sample_price_data):
        """测试零值移动平均线"""
        zero_ma_signal = {"current_price": 105.0, "fast_ma": 0.0, "slow_ma": 103.0}

        result = validate_signal(zero_ma_signal, sample_price_data)
        assert result is False

    def test_validate_signal_extreme_deviation(self, sample_price_data):
        """测试边界偏离度（刚好10%）"""
        boundary_deviation_signal = {
            "current_price": 114.4,  # 相对于快线104.0偏离刚好10%
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = validate_signal(boundary_deviation_signal, sample_price_data)
        assert result is False  # 10%偏离度应该被拒绝

    def test_validate_signal_string_price(self, sample_price_data):
        """测试字符串价格的验证"""
        signal_with_string_price = {
            "current_price": "100.0",  # 字符串价格
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = validate_signal(signal_with_string_price, sample_price_data)
        assert result is False

    def test_validate_signal_ma_calculation_error(self, sample_price_data):
        """测试移动平均线计算错误的情况"""
        signal_with_invalid_ma = {
            "current_price": 105.0,
            "fast_ma": "invalid_ma",  # 字符串MA值
            "slow_ma": 103.0,
        }

        result = validate_signal(signal_with_invalid_ma, sample_price_data)
        assert result is False  # 应该被except块捕获并返回False


class TestFilterSignals:
    """测试信号过滤功能 (Test Signal Filtering)"""

    @pytest.fixture
    def base_signal(self):
        """创建基础信号"""
        return {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
            "last_timestamp": datetime(2023, 1, 10, 14, 30),  # 下午2:30
        }

    def test_filter_signals_no_filters(self, base_signal):
        """测试无过滤条件"""
        result = filter_signals(base_signal)

        # 应该返回原始信号的副本
        assert result == base_signal
        assert result is not base_signal  # 确保是副本

    def test_filter_signals_min_price_pass(self, base_signal):
        """测试最小价格过滤 - 通过"""
        result = filter_signals(base_signal, min_price=100.0)

        # 价格105.0 > 100.0，应该保持信号
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_min_price_fail(self, base_signal):
        """测试最小价格过滤 - 不通过"""
        result = filter_signals(base_signal, min_price=110.0)

        # 价格105.0 < 110.0，应该取消信号
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False
        assert result["current_price"] == 105.0  # 价格信息保留

    def test_filter_signals_max_price_pass(self, base_signal):
        """测试最大价格过滤 - 通过"""
        result = filter_signals(base_signal, max_price=110.0)

        # 价格105.0 < 110.0，应该保持信号
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_max_price_fail(self, base_signal):
        """测试最大价格过滤 - 不通过"""
        result = filter_signals(base_signal, max_price=100.0)

        # 价格105.0 > 100.0，应该取消信号
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_filter_signals_trading_hours_pass(self, base_signal):
        """测试交易时间过滤 - 通过"""
        trading_hours = [9, 10, 11, 12, 13, 14, 15]  # 交易时间包含14点
        result = filter_signals(base_signal, trading_hours=trading_hours)

        # 时间14:30在交易时间内，应该保持信号
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_trading_hours_fail(self, base_signal):
        """测试交易时间过滤 - 不通过"""
        trading_hours = [9, 10, 11, 12]  # 交易时间不包含14点
        result = filter_signals(base_signal, trading_hours=trading_hours)

        # 时间14:30不在交易时间内，应该取消信号
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_filter_signals_multiple_filters_pass(self, base_signal):
        """测试多重过滤条件 - 全部通过"""
        result = filter_signals(
            base_signal, min_price=100.0, max_price=110.0, trading_hours=[14, 15, 16]
        )

        # 所有条件都满足，应该保持信号
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_multiple_filters_partial_fail(self, base_signal):
        """测试多重过滤条件 - 部分不通过"""
        result = filter_signals(
            base_signal,
            min_price=100.0,  # 通过：105.0 > 100.0
            max_price=110.0,  # 通过：105.0 < 110.0
            trading_hours=[9, 10, 11],  # 不通过：14不在列表中
        )

        # 有一个条件不满足，应该取消信号
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_filter_signals_sell_signal(self):
        """测试卖出信号的过滤"""
        sell_signal = {
            "buy_signal": False,
            "sell_signal": True,
            "current_price": 95.0,
            "fast_ma": 94.0,
            "slow_ma": 96.0,
            "last_timestamp": datetime(2023, 1, 10, 16, 30),
        }

        result = filter_signals(sell_signal, min_price=100.0)

        # 价格不满足最小价格要求，卖出信号也应该被取消
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_filter_signals_without_timestamp(self, base_signal):
        """测试没有时间戳的信号过滤"""
        signal_without_timestamp = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = filter_signals(signal_without_timestamp, trading_hours=[14, 15])

        # 没有时间戳时，交易时间过滤应该被跳过
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_missing_current_price(self, base_signal):
        """测试缺少当前价格的信号过滤"""
        signal_without_price = base_signal.copy()
        del signal_without_price["current_price"]

        result = filter_signals(signal_without_price, min_price=100.0)

        # 没有价格时应该被取消
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_filter_signals_boundary_prices(self, base_signal):
        """测试边界价格值"""
        # 测试刚好等于最小价格
        result = filter_signals(base_signal, min_price=105.0)
        assert result["buy_signal"] is True  # 等于边界值应该通过

        # 测试刚好等于最大价格
        result = filter_signals(base_signal, max_price=105.0)
        assert result["buy_signal"] is True  # 等于边界值应该通过

    def test_filter_signals_zero_min_price(self, base_signal):
        """测试零最小价格过滤"""
        result = filter_signals(base_signal, min_price=0)

        # 零最小价格应该让所有正价格通过
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_inf_max_price(self, base_signal):
        """测试无穷大最大价格过滤"""
        result = filter_signals(base_signal, max_price=float("inf"))

        # 无穷大最大价格应该让所有价格通过
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_empty_trading_hours(self, base_signal):
        """测试空交易时间列表"""
        result = filter_signals(base_signal, trading_hours=[])

        # 空交易时间列表应该拒绝所有信号
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_filter_signals_timezone_aware_timestamp(self):
        """测试带时区的时间戳"""
        import pytz

        utc_tz = pytz.UTC

        signal_with_tz = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
            "last_timestamp": datetime(2023, 1, 10, 14, 30, tzinfo=utc_tz),
        }

        result = filter_signals(signal_with_tz, trading_hours=[14, 15])

        # 应该正确提取小时数，不受时区影响
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False


class TestSignalProcessorIntegration:
    """测试信号处理器集成 (Test Signal Processor Integration)"""

    @pytest.fixture
    def realistic_price_data(self):
        """创建更真实的价格数据"""
        dates = pd.date_range("2023-01-01", periods=100, freq="h")  # 修复频率警告
        np.random.seed(42)

        # 创建真实的价格走势
        base_price = 50000  # BTC价格
        trend = np.sin(np.linspace(0, 4 * np.pi, 100)) * 2000  # 波动趋势
        noise = np.random.normal(0, 500, 100)  # 随机噪声
        prices = base_price + trend + noise

        return pd.DataFrame(
            {
                "close": prices,
                "open": prices * 0.999,
                "high": prices * 1.002,
                "low": prices * 0.998,
                "volume": np.random.randint(100, 1000, 100),
            },
            index=dates,
        )

    def test_full_signal_processing_workflow(self, realistic_price_data):
        """测试完整信号处理工作流程"""
        with patch("src.core.signal_processor.moving_average") as mock_ma:
            # 设置移动平均线返回值
            fast_ma = realistic_price_data["close"].rolling(7).mean()
            slow_ma = realistic_price_data["close"].rolling(25).mean()
            mock_ma.side_effect = [fast_ma, slow_ma]

            # 1. 获取交易信号
            signals = get_trading_signals(realistic_price_data)

            # 2. 验证信号
            is_valid = validate_signal(signals, realistic_price_data)

            # 3. 过滤信号
            filtered_signals = filter_signals(
                signals, min_price=45000, max_price=55000, trading_hours=list(range(9, 17))
            )

            # 验证整个流程
            assert isinstance(signals, dict)
            assert isinstance(is_valid, bool)
            assert isinstance(filtered_signals, dict)

            # 验证信号结构保持一致
            assert set(signals.keys()) == set(filtered_signals.keys())

    def test_signal_edge_cases(self):
        """测试信号处理的边缘情况"""
        # 测试极小数据集
        minimal_data = pd.DataFrame(
            {
                "close": [100, 101],
                "open": [99, 100],
                "high": [102, 103],
                "low": [98, 99],
                "volume": [1000, 1100],
            },
            index=pd.date_range("2023-01-01", periods=2, freq="D"),
        )

        with patch("src.core.signal_processor.moving_average") as mock_ma:
            mock_ma.side_effect = [
                pd.Series([100, 101], index=minimal_data.index),
                pd.Series([100, 101], index=minimal_data.index),
            ]

            signals = get_trading_signals(minimal_data)
            is_valid = validate_signal(signals, minimal_data)
            filtered = filter_signals(signals)

            assert signals is not None
            assert isinstance(is_valid, bool)
            assert filtered is not None

    def test_signal_processing_with_invalid_data(self):
        """测试无效数据的信号处理"""
        # 创建包含无效值的数据
        invalid_data = pd.DataFrame(
            {
                "close": [100, np.nan, -50, float("inf")],
                "open": [99, 98, -51, float("inf")],
                "high": [102, 103, -49, float("inf")],
                "low": [98, 97, -52, float("inf")],
                "volume": [1000, 1100, 1200, 1300],
            },
            index=pd.date_range("2023-01-01", periods=4, freq="D"),
        )

        with patch("src.core.signal_processor.moving_average") as mock_ma:
            # 模拟移动平均线也可能包含无效值
            mock_ma.side_effect = [
                pd.Series([100, np.nan, -50, float("inf")], index=invalid_data.index),
                pd.Series([99, 98, -51, float("inf")], index=invalid_data.index),
            ]

            try:
                signals = get_trading_signals(invalid_data)
                assert isinstance(signals, dict)
                # 即使数据无效，函数也应该返回信号结构
                assert "buy_signal" in signals
                assert "sell_signal" in signals
            except Exception as e:
                # 如果抛出异常，应该是可预期的
                assert isinstance(e, (ValueError, TypeError))

    def test_performance_with_large_dataset(self):
        """测试大数据集的性能"""
        # 创建大数据集
        large_data = pd.DataFrame(
            {
                "close": np.random.normal(100, 10, 10000),
                "open": np.random.normal(99, 10, 10000),
                "high": np.random.normal(102, 10, 10000),
                "low": np.random.normal(98, 10, 10000),
                "volume": np.random.randint(1000, 10000, 10000),
            },
            index=pd.date_range("2020-01-01", periods=10000, freq="h"),
        )

        with patch("src.core.signal_processor.moving_average") as mock_ma:
            # 模拟移动平均线计算
            mock_ma.side_effect = [
                large_data["close"].rolling(7).mean(),
                large_data["close"].rolling(25).mean(),
            ]

            import time

            start_time = time.time()

            signals = get_trading_signals(large_data)
            is_valid = validate_signal(signals, large_data)
            filtered = filter_signals(signals, min_price=50, max_price=150)

            end_time = time.time()
            execution_time = end_time - start_time

            # 验证处理完成
            assert isinstance(signals, dict)
            assert isinstance(is_valid, bool)
            assert isinstance(filtered, dict)

            # 验证性能（应该在合理时间内完成，如1秒）
            assert execution_time < 1.0, f"处理时间过长: {execution_time:.3f}秒"

    def test_concurrent_signal_processing(self):
        """测试并发信号处理（模拟多线程场景）"""
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104],
                "open": [99, 100, 101, 102, 103],
                "high": [102, 103, 104, 105, 106],
                "low": [98, 99, 100, 101, 102],
                "volume": [1000, 1100, 1200, 1300, 1400],
            },
            index=pd.date_range("2023-01-01", periods=5, freq="D"),
        )

        import concurrent.futures

        def process_signals():
            with patch("src.core.signal_processor.moving_average") as mock_ma:
                mock_ma.side_effect = [
                    data["close"].rolling(2).mean(),
                    data["close"].rolling(3).mean(),
                ]

                signals = get_trading_signals(data)
                is_valid = validate_signal(signals, data)
                filtered = filter_signals(signals)

                return signals, is_valid, filtered

        # 模拟并发处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_signals) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # 验证所有结果都正确
        for signals, is_valid, filtered in results:
            assert isinstance(signals, dict)
            assert isinstance(is_valid, bool)
            assert isinstance(filtered, dict)


class TestSignalProcessorEdgeCases:
    """测试信号处理器边缘情况 (Test Signal Processor Edge Cases)"""

    def test_get_trading_signals_empty_dataframe(self):
        """测试空DataFrame的处理"""
        empty_df = pd.DataFrame()

        with patch("src.core.signal_processor.moving_average") as mock_ma:
            mock_ma.side_effect = [pd.Series([]), pd.Series([])]

            with pytest.raises((IndexError, KeyError)):
                get_trading_signals(empty_df)

    def test_get_trading_signals_missing_close_column(self):
        """测试缺少close列的DataFrame"""
        df_without_close = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [98, 99, 100],
                "volume": [1000, 1100, 1200],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        with pytest.raises(KeyError):
            get_trading_signals(df_without_close)

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_all_nan_ma(self, mock_ma):
        """测试移动平均线全为NaN的情况"""
        sample_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
                "open": [99, 100, 101],
                "high": [102, 103, 104],
                "low": [98, 99, 100],
                "volume": [1000, 1100, 1200],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        mock_ma.side_effect = [
            pd.Series([np.nan, np.nan, np.nan], index=sample_data.index),
            pd.Series([np.nan, np.nan, np.nan], index=sample_data.index),
        ]

        result = get_trading_signals(sample_data)

        # 应该能处理全NaN的移动平均线
        assert isinstance(result, dict)
        assert "buy_signal" in result
        assert "sell_signal" in result

    def test_validate_signal_complex_number_price(self):
        """测试复数价格的验证"""
        signal_with_complex_price = {
            "current_price": 100 + 5j,  # 复数价格
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        sample_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        result = validate_signal(signal_with_complex_price, sample_data)
        assert result is False  # 复数价格应该被拒绝

    def test_filter_signals_negative_min_price(self):
        """测试负数最小价格过滤"""
        signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = filter_signals(signal, min_price=-50.0)

        # 负数最小价格应该让所有正价格通过
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_negative_max_price(self):
        """测试负数最大价格过滤"""
        signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = filter_signals(signal, max_price=-10.0)

        # 负数最大价格应该拒绝所有正价格
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_filter_signals_invalid_trading_hours(self):
        """测试无效交易时间过滤"""
        signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
            "last_timestamp": datetime(2023, 1, 10, 14, 30),
        }

        # 测试包含无效小时数的交易时间列表
        result = filter_signals(signal, trading_hours=[25, 26, 27])  # 无效小时数

        # 14点不在无效小时数列表中，应该被拒绝
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_filter_signals_none_timestamp(self):
        """测试None时间戳的过滤"""
        signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
            "last_timestamp": None,
        }

        result = filter_signals(signal, trading_hours=[14, 15])

        # None时间戳应该跳过时间过滤
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_multiple_unknown_filters(self):
        """测试多个未知过滤条件"""
        signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        result = filter_signals(
            signal, unknown_filter1="value1", unknown_filter2=123, unknown_filter3=True
        )

        # 未知过滤条件应该被忽略
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_zero_windows(self, mock_ma):
        """测试零窗口大小"""
        sample_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
                "open": [99, 100, 101],
                "high": [102, 103, 104],
                "low": [98, 99, 100],
                "volume": [1000, 1100, 1200],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        # 模拟moving_average可能抛出的异常
        mock_ma.side_effect = ValueError("窗口大小必须大于0")

        with pytest.raises(ValueError):
            get_trading_signals(sample_data, fast_win=0, slow_win=25)

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_negative_windows(self, mock_ma):
        """测试负数窗口大小"""
        sample_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
                "open": [99, 100, 101],
                "high": [102, 103, 104],
                "low": [98, 99, 100],
                "volume": [1000, 1100, 1200],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        # 模拟moving_average可能抛出的异常
        mock_ma.side_effect = ValueError("窗口大小必须大于0")

        with pytest.raises(ValueError):
            get_trading_signals(sample_data, fast_win=-5, slow_win=25)

    def test_validate_signal_very_large_deviation(self):
        """测试非常大的价格偏离"""
        signal_with_large_deviation = {
            "current_price": 1000000.0,  # 相对于快线104.0偏离巨大
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        sample_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        result = validate_signal(signal_with_large_deviation, sample_data)
        assert result is False  # 巨大偏离应该被拒绝

    def test_validate_signal_edge_case_deviation(self):
        """测试边缘偏离情况"""
        # 测试刚好小于10%的偏离
        signal_acceptable = {
            "current_price": 114.39,  # 相对于快线104.0偏离约9.99%
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        sample_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        result = validate_signal(signal_acceptable, sample_data)
        assert result is True  # 9.99%偏离应该被接受

    def test_filter_signals_price_exactly_at_boundaries(self):
        """测试价格刚好在边界值的情况"""
        signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 100.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
        }

        # 测试价格刚好等于最小和最大价格
        result = filter_signals(signal, min_price=100.0, max_price=100.0)

        # 刚好在边界的价格应该通过
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_filter_signals_with_microsecond_timestamp(self):
        """测试包含微秒的时间戳"""
        signal_with_microseconds = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
            "last_timestamp": datetime(2023, 1, 10, 14, 30, 45, 123456),  # 包含微秒
        }

        result = filter_signals(signal_with_microseconds, trading_hours=[14, 15])

        # 微秒不应该影响小时提取
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False


class TestSignalProcessorStressTests:
    """测试信号处理器压力测试 (Test Signal Processor Stress Tests)"""

    def test_validate_signal_with_very_small_ma(self):
        """测试非常小的移动平均线值"""
        signal_with_tiny_ma = {
            "current_price": 1e-10,
            "fast_ma": 1e-15,  # 非常小的值
            "slow_ma": 1e-16,
        }

        sample_data = pd.DataFrame(
            {
                "close": [1e-10, 1e-10, 1e-10],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        result = validate_signal(signal_with_tiny_ma, sample_data)
        assert result is False  # 非常小的MA值应该被拒绝（<=0检查）

    def test_filter_signals_extreme_price_ranges(self):
        """测试极端价格范围过滤"""
        signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 1e6,  # 非常大的价格
            "fast_ma": 1e6,
            "slow_ma": 1e6,
        }

        # 测试非常大的价格范围
        result = filter_signals(signal, min_price=1e5, max_price=1e7)

        # 在范围内应该通过
        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    @patch("src.core.signal_processor.moving_average")
    def test_get_trading_signals_with_duplicate_timestamps(self, mock_ma):
        """测试重复时间戳的数据"""
        duplicate_timestamp = datetime(2023, 1, 1)
        sample_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
                "open": [99, 100, 101],
                "high": [102, 103, 104],
                "low": [98, 99, 100],
                "volume": [1000, 1100, 1200],
            },
            index=[duplicate_timestamp, duplicate_timestamp, duplicate_timestamp],
        )

        mock_ma.side_effect = [
            pd.Series([100, 101, 102], index=sample_data.index),
            pd.Series([99, 100, 101], index=sample_data.index),
        ]

        result = get_trading_signals(sample_data)

        # 应该能处理重复时间戳
        assert isinstance(result, dict)
        assert "last_timestamp" in result
        assert result["last_timestamp"] == duplicate_timestamp

    def test_memory_efficiency_large_signal_dict(self):
        """测试大信号字典的内存效率"""
        # 创建包含大量额外数据的信号字典
        large_signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 105.0,
            "fast_ma": 104.0,
            "slow_ma": 103.0,
            "last_timestamp": datetime(2023, 1, 10, 14, 30),
        }

        # 添加大量额外数据
        for i in range(1000):
            large_signal[f"extra_data_{i}"] = f"value_{i}"

        result = filter_signals(large_signal, min_price=100.0)

        # 过滤后应该保留所有原始数据
        assert len(result) == len(large_signal)
        assert result["buy_signal"] is True
        assert "extra_data_999" in result
