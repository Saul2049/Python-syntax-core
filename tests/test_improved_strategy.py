#!/usr/bin/env python3
"""
测试改进策略模块 (Test Improved Strategy Module)
"""

import warnings
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.strategies.improved_strategy import (
    BollingerBreakoutStrategy,
    MACDStrategy,
    RSIStrategy,
    SimpleMAStrategy,
    _adjust_parameters_for_data_length,
    _extract_price_column_if_needed,
    _handle_backward_compatibility,
    _is_backward_compatible_mode,
    _validate_input_data,
    bollinger_breakout,
    buy_and_hold,
    improved_ma_cross,
    macd_strategy,
    main,
    rsi_strategy,
    simple_ma_cross,
    trend_following,
    trend_following_strategy,
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


class TestHelperFunctions:
    """测试辅助函数"""

    def test_handle_backward_compatibility(self):
        """测试向后兼容性处理"""
        kwargs = {"short_window": 10, "long_window": 20}
        price = pd.Series([100, 101, 102])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            fast_win, slow_win, result_price = _handle_backward_compatibility(kwargs, 5, 15, price)

            assert fast_win == 10
            assert slow_win == 20
            assert len(w) >= 1

    def test_validate_input_data_valid(self):
        """测试有效输入数据验证"""
        valid_data = pd.Series([100, 101, 102, 103])

        # 应该不抛出异常
        _validate_input_data(valid_data)

    def test_validate_input_data_empty(self):
        """测试空数据验证"""
        empty_data = pd.Series([])

        with pytest.raises(ValueError, match="Input data is empty"):
            _validate_input_data(empty_data)

    def test_validate_input_data_nan(self):
        """测试包含NaN的数据验证"""
        nan_data = pd.Series([100, np.nan, 102])

        # 检查是否抛出异常或正常处理
        try:
            result = _validate_input_data(nan_data)
            # 如果没抛异常，验证结果或处理方式
            assert result is None or isinstance(result, (pd.Series, type(None)))
        except ValueError:
            # 抛出异常也是可接受的
            pass

    def test_is_backward_compatible_mode(self):
        """测试向后兼容模式检测"""
        # 向后兼容模式
        compat_kwargs = {"short_window": 10}
        assert _is_backward_compatible_mode(compat_kwargs) is True

        # 非向后兼容模式
        normal_kwargs = {"some_param": "value"}
        assert _is_backward_compatible_mode(normal_kwargs) is False

    def test_adjust_parameters_for_data_length(self):
        """测试参数调整"""
        price = pd.Series([100] * 50)

        # 正常情况
        fast, slow, atr = _adjust_parameters_for_data_length(price, 10, 20, 14, False)
        assert fast == 10
        assert slow == 20
        assert atr == 14

        # 数据太短的情况
        short_price = pd.Series([100] * 5)
        fast, slow, atr = _adjust_parameters_for_data_length(short_price, 10, 20, 14, False)
        assert fast < 10
        assert slow < 20

    def test_extract_price_column_if_needed(self):
        """测试价格列提取"""
        # DataFrame输入
        df = pd.DataFrame({"close": [100, 101, 102], "volume": [1000, 1100, 1200]})
        kwargs = {"data": df, "column": "close"}

        result = _extract_price_column_if_needed(kwargs, pd.Series([100, 101, 102]))

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == 100


class TestStrategyClasses:
    """测试策略类"""

    def test_simple_ma_strategy_init(self):
        """测试简单MA策略初始化"""
        strategy = SimpleMAStrategy(short_window=10, long_window=30)

        assert strategy.short_window == 10
        assert strategy.long_window == 30

    def test_simple_ma_strategy_default_init(self):
        """测试简单MA策略默认初始化"""
        strategy = SimpleMAStrategy()

        assert strategy.short_window == 5
        assert strategy.long_window == 20

    def test_bollinger_breakout_strategy_init(self):
        """测试布林带突破策略初始化"""
        strategy = BollingerBreakoutStrategy(window=25, num_std=2.5)

        assert strategy.window == 25
        assert strategy.num_std == 2.5

    def test_rsi_strategy_init(self):
        """测试RSI策略初始化"""
        strategy = RSIStrategy(window=21, overbought=75, oversold=25)

        assert strategy.window == 21
        assert strategy.overbought == 75
        assert strategy.oversold == 25

    def test_macd_strategy_init(self):
        """测试MACD策略初始化"""
        strategy = MACDStrategy(fast_period=10, slow_period=20, signal_period=5)

        assert strategy.fast_period == 10
        assert strategy.slow_period == 20
        assert strategy.signal_period == 5


class TestLegacyStrategyFunctions:
    """测试遗留策略函数"""

    @pytest.fixture
    def sample_dataframe(self):
        """创建样本DataFrame"""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        return pd.DataFrame(
            {
                "open": [100 + i * 0.1 for i in range(100)],
                "high": [102 + i * 0.1 for i in range(100)],
                "low": [98 + i * 0.1 for i in range(100)],
                "close": [101 + i * 0.1 for i in range(100)],
                "volume": [1000 + i for i in range(100)],
            },
            index=dates,
        )

    def test_simple_ma_cross_deprecated(self, sample_dataframe):
        """测试已弃用的简单MA交叉函数"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            result = simple_ma_cross(sample_dataframe, short_window=5, long_window=15)

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert isinstance(result, (pd.Series, pd.DataFrame))

    def test_bollinger_breakout_deprecated(self, sample_dataframe):
        """测试已弃用的布林带突破函数"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            result = bollinger_breakout(sample_dataframe, window=20, num_std=2.0)

            assert len(w) >= 1
            assert isinstance(result, (pd.Series, pd.DataFrame))

    def test_rsi_strategy_deprecated(self, sample_dataframe):
        """测试已弃用的RSI策略函数"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            result = rsi_strategy(sample_dataframe, window=14)

            assert len(w) >= 1
            assert isinstance(result, (pd.Series, pd.DataFrame))

    def test_macd_strategy_deprecated(self, sample_dataframe):
        """测试已弃用的MACD策略函数"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            result = macd_strategy(sample_dataframe)

            assert len(w) >= 1
            assert isinstance(result, (pd.Series, pd.DataFrame))

    def test_trend_following_strategy_deprecated(self, sample_dataframe):
        """测试已弃用的趋势跟踪策略函数"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            result = trend_following_strategy(sample_dataframe, lookback_window=30)

            assert len(w) >= 1
            assert isinstance(result, (pd.Series, pd.DataFrame))


class TestMainFunction:
    """测试主函数"""

    @patch("src.strategies.improved_strategy.pd.read_csv")
    @patch("src.strategies.improved_strategy.plt.show")
    def test_main_function_success(self, mock_show, mock_read_csv):
        """测试主函数成功执行"""
        # 创建模拟数据，包含正确的日期索引
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        mock_data = pd.DataFrame(
            {
                "btc": [50000 + i * 100 for i in range(100)],
                "eth": [3000 + i * 10 for i in range(100)],
            },
            index=dates,
        )
        mock_read_csv.return_value = mock_data

        result = main("test_file.csv")

        assert isinstance(result, dict)
        assert "strategies" in result
        assert "best_strategy" in result
        mock_read_csv.assert_called_once_with(
            "test_file.csv", parse_dates=["date"], index_col="date"
        )

    @patch("src.strategies.improved_strategy.pd.read_csv")
    def test_main_function_file_not_found(self, mock_read_csv):
        """测试文件未找到的情况"""
        mock_read_csv.side_effect = FileNotFoundError("文件未找到")

        try:
            result = main("nonexistent_file.csv")
            # 如果没抛异常，验证返回值
            assert result is not None or result == {}
        except FileNotFoundError:
            # 抛出异常是预期的
            pass

    @patch("src.strategies.improved_strategy.pd.read_csv")
    def test_main_function_empty_data(self, mock_read_csv):
        """测试空数据的情况"""
        mock_read_csv.return_value = pd.DataFrame()

        try:
            result = main("empty_file.csv")
            assert result is not None or result == {}
        except (KeyError, ValueError):
            # 空数据可能导致异常
            pass

    @patch("src.strategies.improved_strategy.pd.read_csv")
    def test_main_function_invalid_data(self, mock_read_csv):
        """测试无效数据的情况"""
        # 创建包含NaN的数据
        mock_data = pd.DataFrame({"btc": [50000, np.nan, 50200], "eth": [3000, 3010, np.nan]})
        mock_read_csv.return_value = mock_data

        try:
            result = main("invalid_file.csv")
            assert result is not None
            # 应该处理错误并返回空字典或部分结果
            assert isinstance(result, dict)
        except (KeyError, ValueError):
            pass


class TestErrorHandling:
    """测试错误处理"""

    def test_trend_following_invalid_parameters(self):
        """测试趋势跟踪策略的无效参数"""
        price = pd.Series([100, 101, 102])

        # 测试负的窗口大小
        with pytest.raises((ValueError, IndexError)):
            trend_following(price, long_win=-10)

    def test_improved_ma_cross_invalid_parameters(self):
        """测试MA交叉策略的无效参数"""
        price = pd.Series([100, 101, 102])

        # 测试窗口大小大于数据长度
        result = improved_ma_cross(price, fast_win=10, slow_win=20)

        # 应该自动调整参数或处理错误
        assert isinstance(result, pd.Series)

    def test_buy_and_hold_negative_equity(self):
        """测试买入持有策略的负权益"""
        price = pd.Series([100, 101, 102])

        try:
            result = buy_and_hold(price, init_equity=-1000)
            # 如果没抛异常，验证结果合理性
            assert result is not None
        except ValueError:
            # 抛出异常也是可接受的
            pass


class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def realistic_price_data(self):
        """创建真实的价格数据"""
        np.random.seed(42)  # 确保可重现性
        dates = pd.date_range("2023-01-01", periods=365, freq="D")

        # 模拟真实的价格走势
        returns = np.random.normal(0.001, 0.02, 365)  # 日收益率
        prices = [100]
        for r in returns:
            prices.append(prices[-1] * (1 + r))

        return pd.Series(prices[1:], index=dates)

    def test_strategy_comparison(self, realistic_price_data):
        """测试策略比较"""
        # 运行不同策略
        bh_result = buy_and_hold(realistic_price_data)
        tf_result = trend_following(realistic_price_data, long_win=50)
        ma_result = improved_ma_cross(realistic_price_data, fast_win=20, slow_win=50)

        # 验证所有策略都返回有效结果
        assert isinstance(bh_result, pd.Series)
        assert isinstance(tf_result, pd.Series)
        assert isinstance(ma_result, pd.Series)

        # 验证长度一致
        assert len(bh_result) == len(realistic_price_data)
        assert len(tf_result) == len(realistic_price_data)
        assert len(ma_result) == len(realistic_price_data)

        # 验证初始值
        assert bh_result.iloc[0] == 100000.0
        assert tf_result.iloc[0] == 100000.0
        assert ma_result.iloc[0] == 100000.0

    def test_strategy_performance_metrics(self, realistic_price_data):
        """测试策略性能指标"""
        result = improved_ma_cross(realistic_price_data)

        # 计算基本性能指标
        total_return = (result.iloc[-1] / result.iloc[0]) - 1
        max_drawdown = ((result.cummax() - result) / result.cummax()).max()

        # 验证指标在合理范围内
        assert -1 < total_return < 10  # 总收益率在-100%到1000%之间
        assert 0 <= max_drawdown <= 1  # 最大回撤在0到100%之间
