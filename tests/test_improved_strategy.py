#!/usr/bin/env python3
"""
测试改进策略模块 (Test Improved Strategy Module)
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.strategies.improved_strategy import (
    buy_and_hold,
    improved_ma_cross,
    trend_following,
)


class TestBuyAndHoldStrategy:
    """测试买入持有策略 (Test Buy and Hold Strategy)"""

    @pytest.fixture
    def sample_price_data(self):
        """创建示例价格数据"""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.02)
        return pd.Series(prices, index=dates)

    def test_buy_and_hold_basic(self, sample_price_data):
        """测试买入持有策略基本功能"""
        result = buy_and_hold(sample_price_data, init_equity=100000.0)

        # 验证结果类型和长度
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_price_data)

        # 验证初始值
        assert result.iloc[0] == 100000.0

        # 验证权益随价格变化
        price_change = sample_price_data.iloc[-1] - sample_price_data.iloc[0]
        expected_final_equity = 100000.0 + price_change * (100000.0 / sample_price_data.iloc[0])
        assert abs(result.iloc[-1] - expected_final_equity) < 0.01

    def test_buy_and_hold_different_init_equity(self, sample_price_data):
        """测试不同初始资金的买入持有策略"""
        init_equity = 50000.0
        result = buy_and_hold(sample_price_data, init_equity=init_equity)

        assert result.iloc[0] == init_equity

        # 验证权益比例正确
        position_size = init_equity / sample_price_data.iloc[0]
        expected_final = (
            init_equity + (sample_price_data.iloc[-1] - sample_price_data.iloc[0]) * position_size
        )
        assert abs(result.iloc[-1] - expected_final) < 0.01

    def test_buy_and_hold_empty_data(self):
        """测试空数据情况"""
        empty_prices = pd.Series([], dtype=float)

        with pytest.raises(IndexError):
            buy_and_hold(empty_prices)

    def test_buy_and_hold_single_price(self):
        """测试单个价格点情况"""
        single_price = pd.Series([100.0])
        result = buy_and_hold(single_price, init_equity=10000.0)

        assert len(result) == 1
        assert result.iloc[0] == 10000.0


class TestTrendFollowingStrategy:
    """测试趋势跟踪策略 (Test Trend Following Strategy)"""

    @pytest.fixture
    def trending_price_data(self):
        """创建有趋势的价格数据"""
        dates = pd.date_range("2023-01-01", periods=250, freq="D")
        # 创建一个上升趋势的价格序列
        trend = np.linspace(100, 150, 250)
        noise = np.random.normal(0, 1, 250)
        prices = trend + noise
        return pd.Series(prices, index=dates)

    @patch("src.signals.moving_average")
    @patch("src.broker.compute_position_size")
    @patch("src.broker.compute_stop_price")
    @patch("src.broker.compute_trailing_stop")
    @patch("pandas.concat")
    def test_trend_following_basic(
        self,
        mock_concat,
        mock_trailing_stop,
        mock_stop_price,
        mock_position_size,
        mock_ma,
        trending_price_data,
    ):
        """测试趋势跟踪策略基本功能"""
        # 设置模拟返回值
        mock_ma.return_value = pd.Series([95] * 250, index=trending_price_data.index)
        mock_position_size.return_value = 100
        mock_stop_price.return_value = 90.0
        mock_trailing_stop.return_value = 92.0

        # 模拟ATR计算结果，避免pandas内部错误
        mock_atr_series = pd.Series([2.0] * 250, index=trending_price_data.index)
        mock_concat.return_value.max.return_value = mock_atr_series
        mock_atr_series.rolling = Mock()
        mock_atr_series.rolling.return_value.mean.return_value = mock_atr_series

        result = trend_following(
            trending_price_data,
            long_win=200,
            atr_win=20,
            risk_frac=0.02,
            init_equity=100000.0,
            use_trailing_stop=True,
        )

        # 验证结果
        assert isinstance(result, pd.Series)
        assert len(result) == len(trending_price_data)
        assert result.iloc[0] == 100000.0

    @patch("src.signals.moving_average")
    @patch("pandas.concat")
    def test_trend_following_no_trailing_stop(self, mock_concat, mock_ma, trending_price_data):
        """测试不使用移动止损的趋势跟踪策略"""
        mock_ma.return_value = pd.Series([95] * 250, index=trending_price_data.index)

        # 模拟ATR计算结果
        mock_atr_series = pd.Series([2.0] * 250, index=trending_price_data.index)
        mock_concat.return_value.max.return_value = mock_atr_series
        mock_atr_series.rolling = Mock()
        mock_atr_series.rolling.return_value.mean.return_value = mock_atr_series

        result = trend_following(trending_price_data, use_trailing_stop=False)

        assert isinstance(result, pd.Series)
        assert len(result) == len(trending_price_data)

    @patch("src.signals.moving_average")
    @patch("pandas.concat")
    def test_trend_following_different_parameters(self, mock_concat, mock_ma, trending_price_data):
        """测试不同参数的趋势跟踪策略"""
        mock_ma.return_value = pd.Series([95] * 250, index=trending_price_data.index)

        # 模拟ATR计算结果
        mock_atr_series = pd.Series([2.0] * 250, index=trending_price_data.index)
        mock_concat.return_value.max.return_value = mock_atr_series
        mock_atr_series.rolling = Mock()
        mock_atr_series.rolling.return_value.mean.return_value = mock_atr_series

        result = trend_following(
            trending_price_data, long_win=100, atr_win=10, risk_frac=0.01, init_equity=50000.0
        )

        assert isinstance(result, pd.Series)
        assert result.iloc[0] == 50000.0

    @patch("pandas.concat")
    def test_trend_following_short_data(self, mock_concat):
        """测试数据长度不足的情况"""
        short_data = pd.Series([100, 101, 102])

        # 模拟ATR计算结果
        mock_atr_series = pd.Series([1.0, 1.0, 1.0])
        mock_concat.return_value.max.return_value = mock_atr_series
        mock_atr_series.rolling = Mock()
        mock_atr_series.rolling.return_value.mean.return_value = mock_atr_series

        result = trend_following(short_data, long_win=200)

        assert isinstance(result, pd.Series)
        assert len(result) == len(short_data)


class TestImprovedMACrossStrategy:
    """测试改进MA交叉策略 (Test Improved MA Cross Strategy)"""

    @pytest.fixture
    def sample_price_data(self):
        """创建示例价格数据"""
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(300) * 0.02)
        return pd.Series(prices, index=dates)

    @patch("src.broker.backtest_single")
    def test_improved_ma_cross_basic(self, mock_backtest, sample_price_data):
        """测试改进MA交叉策略基本功能"""
        # 设置模拟返回值
        expected_equity = pd.Series([100000] * 300, index=sample_price_data.index)
        mock_backtest.return_value = expected_equity

        result = improved_ma_cross(
            sample_price_data,
            fast_win=50,
            slow_win=200,
            atr_win=20,
            risk_frac=0.02,
            init_equity=100000.0,
            use_trailing_stop=True,
        )

        # 验证调用了正确的函数
        mock_backtest.assert_called_once_with(
            sample_price_data,
            fast_win=50,
            slow_win=200,
            atr_win=20,
            risk_frac=0.02,
            init_equity=100000.0,
            use_trailing_stop=True,
        )

        # 验证结果
        assert isinstance(result, pd.Series)
        pd.testing.assert_series_equal(result, expected_equity)

    @patch("src.broker.backtest_single")
    def test_improved_ma_cross_custom_parameters(self, mock_backtest, sample_price_data):
        """测试自定义参数的改进MA交叉策略"""
        expected_equity = pd.Series([50000] * 300, index=sample_price_data.index)
        mock_backtest.return_value = expected_equity

        result = improved_ma_cross(
            sample_price_data,
            fast_win=30,
            slow_win=100,
            atr_win=15,
            risk_frac=0.01,
            init_equity=50000.0,
            use_trailing_stop=False,
        )

        mock_backtest.assert_called_once_with(
            sample_price_data,
            fast_win=30,
            slow_win=100,
            atr_win=15,
            risk_frac=0.01,
            init_equity=50000.0,
            use_trailing_stop=False,
        )

        pd.testing.assert_series_equal(result, expected_equity)

    @patch("src.broker.backtest_single")
    def test_improved_ma_cross_error_handling(self, mock_backtest, sample_price_data):
        """测试策略的错误处理"""
        mock_backtest.side_effect = ValueError("测试错误")

        with pytest.raises(ValueError, match="测试错误"):
            improved_ma_cross(sample_price_data)


class TestImprovedStrategyIntegration:
    """测试改进策略集成 (Test Improved Strategy Integration)"""

    @pytest.fixture
    def realistic_price_data(self):
        """创建更真实的价格数据"""
        dates = pd.date_range("2023-01-01", periods=365, freq="D")
        np.random.seed(42)

        # 模拟真实的价格走势
        returns = np.random.normal(0.0005, 0.02, 365)  # 日收益率
        prices = [100]
        for r in returns[1:]:
            prices.append(prices[-1] * (1 + r))

        return pd.Series(prices, index=dates)

    def test_strategy_comparison(self, realistic_price_data):
        """测试策略比较功能"""
        # 测试买入持有策略
        bnh_result = buy_and_hold(realistic_price_data, init_equity=100000.0)

        assert isinstance(bnh_result, pd.Series)
        assert len(bnh_result) == len(realistic_price_data)
        assert bnh_result.iloc[0] == 100000.0

        # 验证权益曲线是合理的
        assert all(bnh_result > 0)  # 权益应该保持正值

    @patch("src.broker.backtest_single")
    def test_multiple_strategies_same_data(self, mock_backtest, realistic_price_data):
        """测试多个策略在相同数据上的表现"""
        mock_backtest.return_value = pd.Series(
            [120000] * len(realistic_price_data), index=realistic_price_data.index
        )

        # 运行多个策略
        bnh_equity = buy_and_hold(realistic_price_data, init_equity=100000.0)
        ma_equity = improved_ma_cross(realistic_price_data, init_equity=100000.0)

        # 验证结果类型
        assert isinstance(bnh_equity, pd.Series)
        assert isinstance(ma_equity, pd.Series)

        # 验证长度一致
        assert len(bnh_equity) == len(realistic_price_data)
        assert len(ma_equity) == len(realistic_price_data)

    def test_edge_cases(self):
        """测试边缘情况"""
        # 测试价格为零的情况
        zero_price_data = pd.Series([0.0001, 0.0002, 0.0003])

        result = buy_and_hold(zero_price_data, init_equity=1000.0)
        assert isinstance(result, pd.Series)
        assert len(result) == 3

        # 测试非常大的初始资金
        large_equity_result = buy_and_hold(zero_price_data, init_equity=1e10)
        assert isinstance(large_equity_result, pd.Series)
        assert large_equity_result.iloc[0] == 1e10
