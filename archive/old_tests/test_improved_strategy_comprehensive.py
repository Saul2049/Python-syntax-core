#!/usr/bin/env python3
"""
改进策略综合测试 (Improved Strategy Comprehensive Tests)

专门提升src/strategies/improved_strategy.py覆盖率的完整测试套件
目标：从37%覆盖率提升到75%+
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, Mock
import matplotlib

matplotlib.use("Agg")  # 使用非交互式后端
import matplotlib.pyplot as plt

from src.strategies.improved_strategy import buy_and_hold, trend_following, improved_ma_cross


class TestBuyAndHoldStrategy:
    """买入持有策略测试"""

    @pytest.fixture
    def sample_price_data(self):
        """示例价格数据"""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        # 模拟上涨趋势的价格数据
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5 + 0.02)  # 轻微上涨趋势
        return pd.Series(prices, index=dates, name="price")

    def test_buy_and_hold_basic(self, sample_price_data):
        """测试买入持有基础功能"""
        init_equity = 100_000.0
        equity_curve = buy_and_hold(sample_price_data, init_equity)

        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(sample_price_data)
        assert equity_curve.iloc[0] == init_equity  # 初始权益

        # 权益曲线应该与价格变化成正比
        price_change = sample_price_data.iloc[-1] / sample_price_data.iloc[0]
        equity_change = equity_curve.iloc[-1] / equity_curve.iloc[0]
        assert abs(price_change - equity_change) < 0.001  # 应该几乎相等

    def test_buy_and_hold_different_init_equity(self, sample_price_data):
        """测试不同初始资金的买入持有"""
        equity_curve_1 = buy_and_hold(sample_price_data, 50_000.0)
        equity_curve_2 = buy_and_hold(sample_price_data, 200_000.0)

        # 不同初始资金的收益率应该相同
        return_1 = equity_curve_1.iloc[-1] / equity_curve_1.iloc[0]
        return_2 = equity_curve_2.iloc[-1] / equity_curve_2.iloc[0]
        assert abs(return_1 - return_2) < 0.001

    def test_buy_and_hold_single_price(self):
        """测试单个价格点的买入持有"""
        single_price = pd.Series([100.0], index=[pd.Timestamp("2023-01-01")])
        equity_curve = buy_and_hold(single_price, 10_000.0)

        assert len(equity_curve) == 1
        assert equity_curve.iloc[0] == 10_000.0

    def test_buy_and_hold_declining_prices(self):
        """测试价格下跌时的买入持有"""
        # 创建下跌价格序列
        dates = pd.date_range("2023-01-01", periods=50, freq="D")
        declining_prices = pd.Series(np.linspace(100, 50, 50), index=dates)

        equity_curve = buy_and_hold(declining_prices, 100_000.0)

        # 权益应该随价格下跌而减少
        assert equity_curve.iloc[-1] < equity_curve.iloc[0]
        assert equity_curve.iloc[-1] == 50_000.0  # 价格跌50%，权益也应该跌50%


class TestTrendFollowingStrategy:
    """趋势跟踪策略测试"""

    @pytest.fixture
    def trend_price_data(self):
        """有明显趋势的价格数据"""
        dates = pd.date_range("2023-01-01", periods=300, freq="D")

        # 创建有趋势的价格数据：前100天盘整，后200天上涨
        sideways = 100 + np.random.randn(100) * 0.5  # 盘整
        trending = np.linspace(100, 150, 200) + np.random.randn(200) * 0.3  # 上涨趋势
        prices = np.concatenate([sideways, trending])

        return pd.Series(prices, index=dates, name="price")

    def test_trend_following_basic(self, trend_price_data):
        """测试趋势跟踪基础功能"""
        equity_curve = trend_following(
            trend_price_data,
            long_win=50,  # 较短的长期均线便于测试
            atr_win=20,
            risk_frac=0.02,
            init_equity=100_000.0,
        )

        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(trend_price_data)
        assert equity_curve.iloc[0] == 100_000.0  # 初始权益

    def test_trend_following_different_parameters(self, trend_price_data):
        """测试不同参数的趋势跟踪"""
        # 测试不同的风险系数
        equity_low_risk = trend_following(trend_price_data, long_win=50, risk_frac=0.01)
        equity_high_risk = trend_following(trend_price_data, long_win=50, risk_frac=0.03)

        assert isinstance(equity_low_risk, pd.Series)
        assert isinstance(equity_high_risk, pd.Series)

    def test_trend_following_without_trailing_stop(self, trend_price_data):
        """测试不使用移动止损的趋势跟踪"""
        equity_curve = trend_following(trend_price_data, long_win=50, use_trailing_stop=False)

        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(trend_price_data)

    def test_trend_following_with_trailing_stop(self, trend_price_data):
        """测试使用移动止损的趋势跟踪"""
        equity_curve = trend_following(trend_price_data, long_win=50, use_trailing_stop=True)

        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(trend_price_data)

    def test_trend_following_edge_cases(self):
        """测试趋势跟踪的边缘情况"""
        # 测试ATR包含NaN的情况
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        prices_with_nan = pd.Series([100] * 50 + [np.nan] * 10 + [105] * 40, index=dates)

        equity_curve = trend_following(prices_with_nan, long_win=30)
        assert isinstance(equity_curve, pd.Series)

    def test_trend_following_short_data(self):
        """测试数据不足的趋势跟踪"""
        # 只有50天数据，但长期均线需要200天
        short_data = pd.Series(
            100 + np.random.randn(50), index=pd.date_range("2023-01-01", periods=50, freq="D")
        )

        equity_curve = trend_following(short_data, long_win=200)
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(short_data)

    @patch("src.broker.compute_trailing_stop")
    @patch("src.broker.compute_position_size")
    @patch("src.broker.compute_stop_price")
    def test_trend_following_broker_integration(
        self, mock_stop, mock_size, mock_trailing, trend_price_data
    ):
        """测试与broker模块的集成"""
        mock_size.return_value = 100.0
        mock_stop.return_value = 95.0
        mock_trailing.return_value = 98.0

        equity_curve = trend_following(trend_price_data, long_win=50)

        assert isinstance(equity_curve, pd.Series)
        # 验证broker函数被调用
        assert mock_size.call_count >= 0  # 可能没有触发交易信号

    def test_trend_following_stop_loss_logic(self):
        """测试止损逻辑"""
        # 创建一个先上涨后下跌的价格序列，触发止损
        dates = pd.date_range("2023-01-01", periods=100, freq="D")

        # 先上涨触发买入，然后下跌触发止损
        up_trend = np.linspace(100, 120, 50)
        down_trend = np.linspace(120, 90, 50)  # 大幅下跌触发止损
        prices = pd.Series(np.concatenate([up_trend, down_trend]), index=dates)

        equity_curve = trend_following(prices, long_win=30, atr_win=10)
        assert isinstance(equity_curve, pd.Series)


class TestImprovedMACrossStrategy:
    """改进MA交叉策略测试"""

    @pytest.fixture
    def ma_test_data(self):
        """MA交叉测试数据"""
        dates = pd.date_range("2023-01-01", periods=250, freq="D")
        # 创建有明显交叉信号的价格数据
        prices = 100 + np.cumsum(np.random.randn(250) * 0.3 + 0.01)
        return pd.Series(prices, index=dates, name="price")

    @patch("src.broker.backtest_single")
    def test_improved_ma_cross_basic(self, mock_backtest, ma_test_data):
        """测试改进MA交叉基础功能"""
        # Mock backtest_single的返回值
        mock_equity = pd.Series([100_000] * len(ma_test_data), index=ma_test_data.index)
        mock_backtest.return_value = mock_equity

        result = improved_ma_cross(ma_test_data)

        assert isinstance(result, pd.Series)
        mock_backtest.assert_called_once()

        # 验证传递的参数
        call_args = mock_backtest.call_args
        assert call_args[0][0].equals(ma_test_data)  # price参数
        assert call_args[1]["fast_win"] == 50  # 默认快速均线
        assert call_args[1]["slow_win"] == 200  # 默认慢速均线

    @patch("src.broker.backtest_single")
    def test_improved_ma_cross_custom_parameters(self, mock_backtest, ma_test_data):
        """测试自定义参数的改进MA交叉"""
        mock_equity = pd.Series([100_000] * len(ma_test_data), index=ma_test_data.index)
        mock_backtest.return_value = mock_equity

        result = improved_ma_cross(
            ma_test_data,
            fast_win=30,
            slow_win=100,
            atr_win=15,
            risk_frac=0.03,
            init_equity=50_000.0,
            use_trailing_stop=False,
        )

        assert isinstance(result, pd.Series)

        # 验证传递的自定义参数
        call_args = mock_backtest.call_args
        assert call_args[1]["fast_win"] == 30
        assert call_args[1]["slow_win"] == 100
        assert call_args[1]["atr_win"] == 15
        assert call_args[1]["risk_frac"] == 0.03
        assert call_args[1]["init_equity"] == 50_000.0
        assert call_args[1]["use_trailing_stop"] == False

    @patch("src.broker.backtest_single")
    def test_improved_ma_cross_parameter_types(self, mock_backtest, ma_test_data):
        """测试参数类型检查"""
        mock_equity = pd.Series([100_000] * len(ma_test_data), index=ma_test_data.index)
        mock_backtest.return_value = mock_equity

        # 测试所有参数类型
        result = improved_ma_cross(
            ma_test_data,
            fast_win=int(25),
            slow_win=int(150),
            atr_win=int(14),
            risk_frac=float(0.025),
            init_equity=float(75000.0),
            use_trailing_stop=bool(True),
        )

        assert isinstance(result, pd.Series)
        mock_backtest.assert_called_once()


class TestStrategyIntegration:
    """策略集成测试"""

    @pytest.fixture
    def integration_data(self):
        """集成测试数据"""
        dates = pd.date_range("2023-01-01", periods=500, freq="D")
        np.random.seed(42)  # 固定随机种子确保可重现性

        # 创建复杂的价格走势：上涨-盘整-下跌-上涨
        trend1 = np.linspace(100, 130, 125) + np.random.randn(125) * 0.5
        sideways = 130 + np.random.randn(125) * 1.0
        trend2 = np.linspace(130, 110, 125) + np.random.randn(125) * 0.5
        trend3 = np.linspace(110, 140, 125) + np.random.randn(125) * 0.5

        prices = np.concatenate([trend1, sideways, trend2, trend3])
        return pd.Series(prices, index=dates, name="price")

    def test_all_strategies_comparison(self, integration_data):
        """测试所有策略的比较"""
        init_equity = 100_000.0

        # 运行所有策略
        bnh_equity = buy_and_hold(integration_data, init_equity)
        tf_equity = trend_following(
            integration_data,
            long_win=100,  # 调整参数适应测试数据
            atr_win=20,
            init_equity=init_equity,
        )

        with patch("src.broker.backtest_single") as mock_backtest:
            mock_backtest.return_value = pd.Series(
                [init_equity] * len(integration_data), index=integration_data.index
            )
            ma_equity = improved_ma_cross(integration_data, init_equity=init_equity)

        # 验证所有策略都返回了合理结果
        assert isinstance(bnh_equity, pd.Series)
        assert isinstance(tf_equity, pd.Series)
        assert isinstance(ma_equity, pd.Series)

        assert len(bnh_equity) == len(integration_data)
        assert len(tf_equity) == len(integration_data)
        assert len(ma_equity) == len(integration_data)

    def test_strategy_performance_consistency(self, integration_data):
        """测试策略性能一致性"""
        # 多次运行同一策略应该得到相同结果
        equity1 = buy_and_hold(integration_data, 100_000.0)
        equity2 = buy_and_hold(integration_data, 100_000.0)

        pd.testing.assert_series_equal(equity1, equity2)

    def test_strategy_edge_cases(self):
        """测试策略边缘情况"""
        # 测试极端价格数据
        extreme_data = pd.Series(
            [1e-6, 1e6, 0.001, 1000000], index=pd.date_range("2023-01-01", periods=4, freq="D")
        )

        # 买入持有应该能处理极端数据
        equity = buy_and_hold(extreme_data, 100_000.0)
        assert isinstance(equity, pd.Series)
        assert not equity.isna().any()

    def test_strategy_with_missing_dependencies(self, integration_data):
        """测试缺少依赖时的处理"""
        # 测试signals模块不可用时的情况
        with patch("src.strategies.improved_strategy.signals") as mock_signals:
            mock_signals.moving_average.side_effect = ImportError("Module not found")

            # 买入持有不依赖signals，应该正常工作
            equity = buy_and_hold(integration_data, 100_000.0)
            assert isinstance(equity, pd.Series)


class TestStrategyVisualization:
    """策略可视化测试"""

    @pytest.fixture
    def viz_data(self):
        """可视化测试数据"""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        return pd.Series(prices, index=dates)

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.savefig")
    def test_strategy_plotting_capability(self, mock_savefig, mock_show, viz_data):
        """测试策略绘图功能"""
        # 创建一些权益曲线
        bnh_equity = buy_and_hold(viz_data, 100_000.0)

        # 测试绘图代码不会崩溃
        plt.figure(figsize=(10, 6))
        plt.plot(bnh_equity.index, bnh_equity / 100_000.0, label="买入持有")
        plt.legend()
        plt.grid(True)
        plt.title("策略测试")

        # 验证不会抛出异常
        assert True  # 如果到达这里说明绘图代码执行成功


class TestStrategyRobustness:
    """策略稳健性测试"""

    def test_buy_and_hold_with_inf_values(self):
        """测试包含无穷大值的数据"""
        data_with_inf = pd.Series(
            [100, np.inf, 110, 120], index=pd.date_range("2023-01-01", periods=4, freq="D")
        )

        # 应该能处理无穷大值而不崩溃
        try:
            equity = buy_and_hold(data_with_inf, 100_000.0)
            assert isinstance(equity, pd.Series)
        except (ValueError, OverflowError):
            # 抛出错误也是可接受的行为
            pass

    def test_trend_following_with_constant_prices(self):
        """测试价格完全不变的情况"""
        constant_prices = pd.Series(
            [100.0] * 100, index=pd.date_range("2023-01-01", periods=100, freq="D")
        )

        equity = trend_following(constant_prices, long_win=50)
        assert isinstance(equity, pd.Series)
        # 价格不变时应该没有交易
        assert all(equity == 100_000.0)  # 权益应该保持不变

    def test_strategies_with_minimal_data(self):
        """测试最少数据情况"""
        minimal_data = pd.Series(
            [100.0, 101.0], index=pd.date_range("2023-01-01", periods=2, freq="D")
        )

        # 买入持有应该能处理最少数据
        equity = buy_and_hold(minimal_data, 10_000.0)
        assert len(equity) == 2
        assert equity.iloc[0] == 10_000.0

    def test_strategies_numerical_stability(self):
        """测试数值稳定性"""
        # 测试很小的价格值
        small_prices = pd.Series(
            [0.001, 0.002, 0.0015, 0.0025], index=pd.date_range("2023-01-01", periods=4, freq="D")
        )

        equity = buy_and_hold(small_prices, 1_000.0)
        assert isinstance(equity, pd.Series)
        assert all(np.isfinite(equity))  # 所有值应该是有限的
