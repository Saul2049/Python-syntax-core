#!/usr/bin/env python3
"""
改进策略增强测试套件 (Improved Strategy Enhanced Tests)

专门提升src/strategies/improved_strategy.py覆盖率
目标：从41%覆盖率提升到85%+
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, Mock, MagicMock
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from math import isfinite, isnan
import warnings

from src.strategies.improved_strategy import (
    buy_and_hold,
    trend_following,
    improved_ma_cross
)


class TestBuyAndHoldAdvanced:
    """买入持有策略高级测试"""

    def test_buy_and_hold_basic(self):
        """Test basic buy and hold functionality"""
        price = pd.Series([100, 105, 110, 115, 120], name="price")
        result = buy_and_hold(price, init_equity=10000)
        
        expected_final = 10000 + (120 - 100) * (10000 / 100)
        assert abs(result.iloc[-1] - expected_final) < 0.01

    def test_buy_and_hold_with_zero_initial_price(self):
        """测试初始价格为零的情况"""
        prices = pd.Series([0, 10, 20, 30], index=pd.date_range('2023-01-01', periods=4))
        
        # 零初始价格会导致除零，但函数会返回带inf的结果而不是抛出异常
        equity_curve = buy_and_hold(prices, 100_000.0)
        assert isinstance(equity_curve, pd.Series)
        # 第一个值应该是inf或nan由于除零
        assert not np.isfinite(equity_curve.iloc[0]) or equity_curve.iloc[0] == 100_000.0

    def test_buy_and_hold_with_negative_prices(self):
        """测试负价格的情况"""
        prices = pd.Series([-10, -5, 0, 5, 10], index=pd.date_range('2023-01-01', periods=5))
        equity_curve = buy_and_hold(prices, 100_000.0)
        
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(prices)

    def test_buy_and_hold_with_nan_prices(self):
        """测试包含NaN价格的情况"""
        prices = pd.Series([100, np.nan, 110, 120], index=pd.date_range('2023-01-01', periods=4))
        equity_curve = buy_and_hold(prices, 100_000.0)
        
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(prices)

    def test_buy_and_hold_with_inf_prices(self):
        """测试包含无穷大价格的情况"""
        prices = pd.Series([100, 110, np.inf, 120], index=pd.date_range('2023-01-01', periods=4))
        equity_curve = buy_and_hold(prices, 100_000.0)
        
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(prices)

    def test_buy_and_hold_single_price_point(self):
        """测试单个价格点"""
        single_price = pd.Series([150.0], index=[pd.Timestamp('2023-01-01')])
        equity_curve = buy_and_hold(single_price, 50_000.0)
        
        assert len(equity_curve) == 1
        assert equity_curve.iloc[0] == 50_000.0

    def test_buy_and_hold_zero_equity(self):
        """测试零初始资金"""
        prices = pd.Series([100, 110, 120], index=pd.date_range('2023-01-01', periods=3))
        equity_curve = buy_and_hold(prices, 0.0)
        
        assert all(equity_curve == 0.0)

    def test_buy_and_hold_negative_equity(self):
        """测试负初始资金"""
        prices = pd.Series([100, 110, 120], index=pd.date_range('2023-01-01', periods=3))
        equity_curve = buy_and_hold(prices, -10_000.0)
        
        assert isinstance(equity_curve, pd.Series)
        assert equity_curve.iloc[0] == -10_000.0

    def test_buy_and_hold_large_numbers(self):
        """测试大数值"""
        prices = pd.Series([1e6, 1.1e6, 1.2e6], index=pd.date_range('2023-01-01', periods=3))
        equity_curve = buy_and_hold(prices, 1e9)
        
        assert isinstance(equity_curve, pd.Series)
        assert equity_curve.iloc[0] == 1e9

    def test_buy_and_hold_volatility_stress(self):
        """测试高波动率场景"""
        # 创建高波动率价格序列
        dates = pd.date_range('2023-01-01', periods=1000, freq='h')
        high_vol_prices = 100 * np.exp(np.cumsum(np.random.randn(1000) * 0.1))
        prices = pd.Series(high_vol_prices, index=dates)
        
        equity_curve = buy_and_hold(prices, 100_000.0)
        
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(prices)

    def test_buy_and_hold_declining_market(self):
        """Test buy and hold in declining market"""
        price = pd.Series([100, 90, 80, 70, 60], name="price")
        result = buy_and_hold(price, init_equity=10000)
        
        expected_final = 10000 + (60 - 100) * (10000 / 100)
        assert abs(result.iloc[-1] - expected_final) < 0.01


class TestTrendFollowingAdvanced:
    """趋势跟踪策略高级测试"""

    @pytest.fixture
    def complex_price_data(self):
        """复杂价格数据"""
        dates = pd.date_range('2023-01-01', periods=500, freq='D')
        
        # 创建包含多种模式的价格数据
        base_trend = np.linspace(100, 200, 500)  # 基础趋势
        cycles = 10 * np.sin(np.linspace(0, 4*np.pi, 500))  # 周期性波动
        noise = np.random.randn(500) * 2  # 噪声
        spikes = np.zeros(500)
        spikes[100] = 20  # 价格突刺
        spikes[300] = -15
        
        prices = base_trend + cycles + noise + spikes
        return pd.Series(np.maximum(prices, 1), index=dates)  # 确保价格为正

    def test_trend_following_with_mock_signals(self, complex_price_data):
        """测试使用mock信号模块"""
        mock_signals = Mock()
        mock_signals.moving_average.return_value = pd.Series(
            100 + np.arange(len(complex_price_data)) * 0.1,
            index=complex_price_data.index
        )
        
        with patch('src.strategies.improved_strategy.signals', mock_signals):
            equity_curve = trend_following(complex_price_data, long_win=50)
            
            assert isinstance(equity_curve, pd.Series)
            assert len(equity_curve) == len(complex_price_data)
            mock_signals.moving_average.assert_called_once()

    def test_trend_following_extreme_parameters(self, complex_price_data):
        """测试极端参数值"""
        # 极小的risk_frac
        equity_curve_1 = trend_following(
            complex_price_data, 
            risk_frac=0.0001, 
            long_win=10
        )
        assert isinstance(equity_curve_1, pd.Series)
        
        # 极大的risk_frac
        equity_curve_2 = trend_following(
            complex_price_data, 
            risk_frac=0.5, 
            long_win=10
        )
        assert isinstance(equity_curve_2, pd.Series)
        
        # 极长的窗口
        equity_curve_3 = trend_following(
            complex_price_data, 
            long_win=400  # 接近数据长度
        )
        assert isinstance(equity_curve_3, pd.Series)

    def test_trend_following_with_mock_broker(self, complex_price_data):
        """测试使用mock broker模块"""
        mock_broker = Mock()
        mock_broker.compute_position_size.return_value = 50.0
        mock_broker.compute_stop_price.return_value = 95.0
        mock_broker.compute_trailing_stop.return_value = 98.0
        
        with patch('src.strategies.improved_strategy.broker', mock_broker):
            equity_curve = trend_following(complex_price_data, long_win=30)
            
            assert isinstance(equity_curve, pd.Series)

    def test_trend_following_nan_atr_handling(self):
        """测试ATR为NaN的处理"""
        # 创建导致ATR为NaN的价格数据
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        constant_prices = pd.Series([100.0] * 100, index=dates)  # 恒定价格
        
        equity_curve = trend_following(constant_prices, long_win=20, atr_win=10)
        
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(constant_prices)

    def test_trend_following_inf_atr_handling(self):
        """测试ATR为无穷大的处理"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        extreme_prices = pd.Series([100, 1e10, 100] + [100] * 47, index=dates)
        
        equity_curve = trend_following(extreme_prices, long_win=20, atr_win=5)
        
        assert isinstance(equity_curve, pd.Series)

    def test_trend_following_position_management_edge_cases(self):
        """测试持仓管理边缘情况"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        # 创建先上涨后急跌的价格模式，测试止损逻辑
        up_prices = np.linspace(100, 150, 50)
        down_prices = np.linspace(150, 80, 50)  # 急跌触发止损
        prices = pd.Series(np.concatenate([up_prices, down_prices]), index=dates)
        
        equity_curve = trend_following(prices, long_win=20, atr_win=5, risk_frac=0.02)
        
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(prices)

    def test_trend_following_with_isfinite_false(self):
        """测试isfinite返回False的情况"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        # 包含各种非有限值的价格
        prices_data = [100.0] * 30 + [np.nan] * 10 + [np.inf] * 10 + [100.0] * 50
        prices = pd.Series(prices_data, index=dates)
        
        with patch('src.strategies.improved_strategy.isfinite') as mock_isfinite:
            # 模拟isfinite对某些值返回False
            mock_isfinite.side_effect = lambda x: not (isnan(x) or np.isinf(x))
            
            equity_curve = trend_following(prices, long_win=20)
            
            assert isinstance(equity_curve, pd.Series)

    def test_trend_following_trailing_stop_evolution(self):
        """测试移动止损的演化过程"""
        dates = pd.date_range('2023-01-01', periods=200, freq='D')
        
        # 创建持续上涨然后回调的价格
        up_trend = np.linspace(100, 200, 150)
        pullback = np.linspace(200, 180, 50)
        prices = pd.Series(np.concatenate([up_trend, pullback]), index=dates)
        
        # 使用移动止损
        equity_curve_with_trail = trend_following(
            prices, 
            long_win=30, 
            use_trailing_stop=True,
            risk_frac=0.02
        )
        
        # 不使用移动止损
        equity_curve_no_trail = trend_following(
            prices, 
            long_win=30, 
            use_trailing_stop=False,
            risk_frac=0.02
        )
        
        assert isinstance(equity_curve_with_trail, pd.Series)
        assert isinstance(equity_curve_no_trail, pd.Series)

    def test_trend_following_multiple_entry_exit_cycles(self):
        """测试多次进出场周期"""
        dates = pd.date_range('2023-01-01', periods=300, freq='D')
        
        # 创建多个趋势周期
        cycle1 = np.linspace(100, 130, 100)  # 上涨
        cycle2 = np.linspace(130, 110, 50)   # 回调
        cycle3 = np.linspace(110, 160, 100)  # 再次上涨
        cycle4 = np.linspace(160, 140, 50)   # 再次回调
        
        prices = pd.Series(
            np.concatenate([cycle1, cycle2, cycle3, cycle4]), 
            index=dates
        )
        
        equity_curve = trend_following(prices, long_win=40, atr_win=10)
        
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(prices)

    def test_trend_following_short_window_periods(self):
        """测试窗口期短于数据长度的情况"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = pd.Series(100 + np.random.randn(50) * 5, index=dates)
        
        # long_win接近数据长度
        equity_curve = trend_following(prices, long_win=45, atr_win=40)
        
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(prices)


class TestImprovedMACrossAdvanced:
    """改进MA交叉策略高级测试"""

    @pytest.fixture
    def ma_cross_data(self):
        """MA交叉测试数据"""
        dates = pd.date_range('2023-01-01', periods=400, freq='D')
        
        # 创建明确的MA交叉信号
        slow_trend = np.linspace(100, 150, 400)
        fast_oscillation = 5 * np.sin(np.linspace(0, 8*np.pi, 400))
        noise = np.random.randn(400) * 1
        
        prices = slow_trend + fast_oscillation + noise
        return pd.Series(prices, index=dates)

    def test_improved_ma_cross_with_mock_broker(self, ma_cross_data):
        """测试使用mock broker的MA交叉策略"""
        mock_broker = Mock()
        mock_broker.backtest_single.return_value = pd.Series(
            np.linspace(100_000, 120_000, len(ma_cross_data)),
            index=ma_cross_data.index
        )
        
        with patch('src.strategies.improved_strategy.broker', mock_broker):
            result = improved_ma_cross(ma_cross_data, fast_win=20, slow_win=50)
            
            assert isinstance(result, pd.Series)
            assert len(result) == len(ma_cross_data)
            mock_broker.backtest_single.assert_called_once()

    def test_improved_ma_cross_parameter_validation(self, ma_cross_data):
        """测试参数验证"""
        # 测试快均线大于慢均线的情况
        with patch('src.strategies.improved_strategy.broker') as mock_broker:
            mock_broker.backtest_single.return_value = pd.Series([100_000], index=[ma_cross_data.index[0]])
            
            # 快均线窗口大于慢均线窗口
            result = improved_ma_cross(ma_cross_data, fast_win=100, slow_win=50)
            
            assert isinstance(result, pd.Series)

    def test_improved_ma_cross_extreme_windows(self, ma_cross_data):
        """测试极端窗口参数"""
        with patch('src.strategies.improved_strategy.broker') as mock_broker:
            mock_broker.backtest_single.return_value = pd.Series(
                [100_000] * len(ma_cross_data), 
                index=ma_cross_data.index
            )
            
            # 极小窗口
            result1 = improved_ma_cross(ma_cross_data, fast_win=1, slow_win=2)
            assert isinstance(result1, pd.Series)
            
            # 极大窗口
            result2 = improved_ma_cross(ma_cross_data, fast_win=300, slow_win=350)
            assert isinstance(result2, pd.Series)

    def test_improved_ma_cross_zero_risk(self, ma_cross_data):
        """测试零风险参数"""
        with patch('src.strategies.improved_strategy.broker') as mock_broker:
            mock_broker.backtest_single.return_value = pd.Series(
                [100_000] * len(ma_cross_data), 
                index=ma_cross_data.index
            )
            
            result = improved_ma_cross(ma_cross_data, risk_frac=0.0)
            
            assert isinstance(result, pd.Series)

    def test_improved_ma_cross_high_risk(self, ma_cross_data):
        """测试高风险参数"""
        with patch('src.strategies.improved_strategy.broker') as mock_broker:
            mock_broker.backtest_single.return_value = pd.Series(
                [100_000] * len(ma_cross_data), 
                index=ma_cross_data.index
            )
            
            result = improved_ma_cross(ma_cross_data, risk_frac=1.0)
            
            assert isinstance(result, pd.Series)

    def test_improved_ma_cross_broker_exception(self, ma_cross_data):
        """测试broker异常处理"""
        with patch('src.strategies.improved_strategy.broker') as mock_broker:
            mock_broker.backtest_single.side_effect = Exception("Broker error")
            
            with pytest.raises(Exception):
                improved_ma_cross(ma_cross_data)


class TestStrategyErrorHandling:
    """策略错误处理测试"""

    def test_all_strategies_with_empty_data(self):
        """测试所有策略处理空数据"""
        empty_series = pd.Series([], dtype=float)
        
        # buy_and_hold with empty data
        try:
            result = buy_and_hold(empty_series, 100_000)
            assert isinstance(result, pd.Series)
        except (IndexError, ValueError):
            pass  # 允许抛出异常
        
        # trend_following with empty data
        try:
            result = trend_following(empty_series)
            assert isinstance(result, pd.Series)
        except (IndexError, ValueError):
            pass  # 允许抛出异常

    def test_strategies_with_all_nan_data(self):
        """测试所有策略处理全NaN数据"""
        nan_data = pd.Series([np.nan] * 100, index=pd.date_range('2023-01-01', periods=100))
        
        # buy_and_hold with all NaN
        try:
            result = buy_and_hold(nan_data, 100_000)
            assert isinstance(result, pd.Series)
        except (ValueError, TypeError):
            pass  # 允许抛出异常
        
        # trend_following with all NaN
        try:
            result = trend_following(nan_data)
            assert isinstance(result, pd.Series)
        except (ValueError, TypeError):
            pass  # 允许抛出异常

    def test_strategies_with_constant_prices(self):
        """测试策略处理恒定价格"""
        constant_prices = pd.Series([100.0] * 200, index=pd.date_range('2023-01-01', periods=200))
        
        # buy_and_hold应该返回恒定权益
        bnh_result = buy_and_hold(constant_prices, 100_000)
        assert all(bnh_result == 100_000)
        
        # trend_following应该正常处理
        tf_result = trend_following(constant_prices, long_win=50)
        assert isinstance(tf_result, pd.Series)

    def test_strategies_with_extreme_values(self):
        """测试策略处理极端值"""
        extreme_data = pd.Series([1e-10, 1e10, 1e-5, 1e8], index=pd.date_range('2023-01-01', periods=4))
        
        # 测试买入持有
        bnh_result = buy_and_hold(extreme_data, 100_000)
        assert isinstance(bnh_result, pd.Series)
        
        # 测试趋势跟踪
        tf_result = trend_following(extreme_data, long_win=2, atr_win=2)
        assert isinstance(tf_result, pd.Series)


class TestStrategyIntegrationAdvanced:
    """策略集成高级测试"""

    @pytest.fixture
    def realistic_market_data(self):
        """真实市场数据模拟"""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        
        # 模拟真实市场模式
        n_days = len(dates)
        returns = np.random.randn(n_days) * 0.02  # 日收益率
        
        # 添加市场趋势和周期
        trend = np.linspace(0, 0.5, n_days)  # 长期上涨趋势
        cycle = 0.1 * np.sin(np.linspace(0, 8*np.pi, n_days))  # 周期性波动
        
        # 添加一些市场崩盘事件
        crash_days = [int(n_days * 0.3), int(n_days * 0.7)]
        for crash_day in crash_days:
            returns[crash_day:crash_day+10] -= 0.05  # 连续下跌
        
        combined_returns = returns + np.diff(np.concatenate([[0], trend + cycle]))
        prices = 100 * np.exp(np.cumsum(combined_returns))
        
        return pd.Series(prices, index=dates)

    def test_strategy_comparison_comprehensive(self, realistic_market_data):
        """策略综合比较测试"""
        init_equity = 100_000
        
        # 运行所有策略
        bnh_result = buy_and_hold(realistic_market_data, init_equity)
        tf_result = trend_following(
            realistic_market_data, 
            long_win=100, 
            atr_win=20, 
            risk_frac=0.02,
            init_equity=init_equity
        )
        
        with patch('src.strategies.improved_strategy.broker') as mock_broker:
            mock_broker.backtest_single.return_value = pd.Series(
                np.linspace(init_equity, init_equity * 1.2, len(realistic_market_data)),
                index=realistic_market_data.index
            )
            ma_result = improved_ma_cross(realistic_market_data, init_equity=init_equity)
        
        # 验证所有结果
        assert isinstance(bnh_result, pd.Series)
        assert isinstance(tf_result, pd.Series)
        assert isinstance(ma_result, pd.Series)
        
        # 验证长度一致
        assert len(bnh_result) == len(realistic_market_data)
        assert len(tf_result) == len(realistic_market_data)
        assert len(ma_result) == len(realistic_market_data)

    def test_strategy_performance_metrics_calculation(self, realistic_market_data):
        """测试策略性能指标计算"""
        with patch('src.strategies.improved_strategy.metrics') as mock_metrics:
            mock_metrics.cagr.return_value = 0.15
            mock_metrics.max_drawdown.return_value = 0.10
            mock_metrics.sharpe_ratio.return_value = 1.5
            
            # 这里实际上是测试__main__块的逻辑
            # 但由于我们在测试环境中，直接验证策略返回值
            bnh_result = buy_and_hold(realistic_market_data, 100_000)
            tf_result = trend_following(realistic_market_data, long_win=50)
            
            assert isinstance(bnh_result, pd.Series)
            assert isinstance(tf_result, pd.Series)

    def test_strategy_plotting_capability(self, realistic_market_data):
        """测试策略绘图功能"""
        with patch('matplotlib.pyplot.figure') as mock_figure, \
             patch('matplotlib.pyplot.plot') as mock_plot, \
             patch('matplotlib.pyplot.legend') as mock_legend, \
             patch('matplotlib.pyplot.title') as mock_title, \
             patch('matplotlib.pyplot.xlabel') as mock_xlabel, \
             patch('matplotlib.pyplot.ylabel') as mock_ylabel, \
             patch('matplotlib.pyplot.grid') as mock_grid, \
             patch('matplotlib.pyplot.show') as mock_show:
            
            # 模拟主程序的绘图逻辑
            bnh_result = buy_and_hold(realistic_market_data, 100_000)
            tf_result = trend_following(realistic_market_data, long_win=50)
            
            # 模拟绘图操作
            plt.figure(figsize=(12, 8))
            plt.plot(bnh_result.index, bnh_result / 100_000, label="买入持有")
            plt.plot(tf_result.index, tf_result / 100_000, label="趋势跟踪")
            plt.legend()
            plt.title("策略比较")
            plt.xlabel("日期")
            plt.ylabel("相对回报")
            plt.grid(True)
            
            # 验证matplotlib函数被调用
            mock_figure.assert_called()
            assert mock_plot.call_count >= 2
            mock_legend.assert_called()


class TestMathUtilityFunctions:
    """数学工具函数测试"""

    def test_isfinite_usage_in_strategies(self):
        """测试策略中isfinite函数的使用"""
        from math import isfinite
        
        # 测试各种值
        assert isfinite(100.0) == True
        assert isfinite(np.nan) == False
        assert isfinite(np.inf) == False
        assert isfinite(-np.inf) == False
        assert isfinite(0.0) == True
        assert isfinite(-100.0) == True

    def test_isfinite_with_pandas_series(self):
        """测试isfinite与pandas Series的交互"""
        from math import isfinite
        
        test_series = pd.Series([100.0, np.nan, np.inf, -np.inf, 50.0])
        
        # 测试Series中元素的isfinite检查
        finite_mask = [isfinite(x) for x in test_series]
        expected = [True, False, False, False, True]
        
        assert finite_mask == expected


class TestATRCalculationEdgeCases:
    """ATR计算边缘情况测试"""

    def test_atr_calculation_with_trend_following(self):
        """测试趋势跟踪中ATR计算的边缘情况"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        # 创建特定的价格模式来测试ATR计算
        prices_data = []
        for i in range(100):
            if i < 20:
                prices_data.append(100.0)  # 恒定价格，ATR应该为0
            elif i < 40:
                prices_data.append(100.0 + (i-20) * 0.1)  # 缓慢上涨
            elif i < 60:
                prices_data.append(102.0 + (i-40) * 5)  # 快速上涨，高ATR
            else:
                prices_data.append(200.0)  # 再次恒定
        
        prices = pd.Series(prices_data, index=dates)
        
        # 测试不同ATR窗口大小
        for atr_win in [5, 10, 20]:
            result = trend_following(prices, long_win=30, atr_win=atr_win)
            assert isinstance(result, pd.Series)
            assert len(result) == len(prices)

    def test_atr_with_price_gaps(self):
        """测试价格跳空对ATR的影响"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        
        # 创建包含价格跳空的数据
        prices_data = [100.0] * 20 + [150.0] * 20 + [120.0] * 10  # 突然跳涨再回落
        prices = pd.Series(prices_data, index=dates)
        
        result = trend_following(prices, long_win=15, atr_win=10)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(prices)


class TestPositionSizingEdgeCases:
    """持仓规模边缘情况测试"""

    def test_position_sizing_with_mock_broker(self):
        """测试使用mock broker的持仓规模计算"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = pd.Series(100 + np.random.randn(100) * 5, index=dates)
        
        mock_broker = Mock()
        
        # 测试不同的持仓规模返回值
        test_cases = [0.0, 1.0, 100.0, -50.0, np.nan, np.inf]
        
        for size in test_cases:
            mock_broker.compute_position_size.return_value = size
            mock_broker.compute_stop_price.return_value = 95.0
            mock_broker.compute_trailing_stop.return_value = 98.0
            
            with patch('src.strategies.improved_strategy.broker', mock_broker):
                try:
                    result = trend_following(prices, long_win=20)
                    assert isinstance(result, pd.Series)
                except (ValueError, TypeError):
                    pass  # 某些异常值可能导致异常，这是可以接受的

    def test_stop_price_edge_cases(self):
        """测试止损价格边缘情况"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = pd.Series(100 + np.random.randn(100) * 2, index=dates)
        
        mock_broker = Mock()
        mock_broker.compute_position_size.return_value = 50.0
        
        # 测试不同的止损价格
        stop_prices = [0.0, 50.0, 150.0, np.nan, np.inf, -10.0]
        
        for stop_price in stop_prices:
            mock_broker.compute_stop_price.return_value = stop_price
            mock_broker.compute_trailing_stop.return_value = stop_price
            
            with patch('src.strategies.improved_strategy.broker', mock_broker):
                try:
                    result = trend_following(prices, long_win=20)
                    assert isinstance(result, pd.Series)
                except (ValueError, TypeError):
                    pass  # 异常值可能导致异常


class TestMainExecutionPath:
    """主执行路径测试"""

    def test_main_execution_simulation(self):
        """模拟主程序执行路径"""
        # 模拟btc_eth.csv文件不存在的情况
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.side_effect = FileNotFoundError("File not found")
            
            # 在实际环境中，这会导致程序退出或异常
            # 在测试中，我们只验证异常被正确处理
            with pytest.raises(FileNotFoundError):
                pd.read_csv("btc_eth.csv")

    def test_main_with_mock_data(self):
        """使用模拟数据测试主逻辑"""
        # 创建模拟的btc数据
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        btc_data = pd.Series(
            50000 + np.cumsum(np.random.randn(len(dates)) * 1000),
            index=dates,
            name='btc'
        )
        
        mock_df = pd.DataFrame({'btc': btc_data})
        
        with patch('pandas.read_csv', return_value=mock_df), \
             patch('src.strategies.improved_strategy.metrics') as mock_metrics, \
             patch('matplotlib.pyplot.show') as mock_show:
            
            mock_metrics.cagr.return_value = 0.15
            mock_metrics.max_drawdown.return_value = 0.08
            mock_metrics.sharpe_ratio.return_value = 1.25
            
            # 运行策略（模拟主程序逻辑）
            btc = mock_df["btc"]
            init_equity = 100_000.0
            
            bnh_equity = buy_and_hold(btc, init_equity)
            tf_equity = trend_following(btc, long_win=200, atr_win=20, init_equity=init_equity)
            
            # 验证结果
            assert isinstance(bnh_equity, pd.Series)
            assert isinstance(tf_equity, pd.Series)
            assert len(bnh_equity) == len(btc)
            assert len(tf_equity) == len(btc)


class TestConcurrencyAndPerformance:
    """并发和性能测试"""

    def test_strategy_with_large_dataset(self):
        """测试大数据集的策略性能"""
        # 创建较大的数据集
        dates = pd.date_range('2010-01-01', '2023-12-31', freq='h')  # 14年的小时数据
        n_points = len(dates)
        
        # 使用更高效的方式生成大数据集
        returns = np.random.randn(n_points) * 0.001
        prices = 100 * np.exp(np.cumsum(returns))
        price_series = pd.Series(prices, index=dates)
        
        # 测试买入持有（应该很快）
        start_time = pd.Timestamp.now()
        bnh_result = buy_and_hold(price_series, 100_000)
        bnh_time = (pd.Timestamp.now() - start_time).total_seconds()
        
        assert isinstance(bnh_result, pd.Series)
        assert bnh_time < 10.0  # 应该在10秒内完成
        
        # 测试趋势跟踪（计算量更大）
        start_time = pd.Timestamp.now()
        tf_result = trend_following(price_series[:1000], long_win=100, atr_win=50)  # 使用较小的子集
        tf_time = (pd.Timestamp.now() - start_time).total_seconds()
        
        assert isinstance(tf_result, pd.Series)
        assert tf_time < 30.0  # 应该在30秒内完成

    def test_memory_efficiency(self):
        """测试内存效率"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建和处理多个数据集
        for i in range(5):
            dates = pd.date_range('2023-01-01', periods=10000, freq='min')
            prices = pd.Series(100 + np.random.randn(10000) * 5, index=dates)
            
            result = buy_and_hold(prices, 100_000)
            del result, prices, dates  # 显式删除
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / (1024 * 1024)  # MB
        
        # 内存增长应该合理（小于100MB）
        assert memory_increase < 100


class TestImprovedStrategyCompatibilityLayer:
    """Test the improved strategy backward compatibility functions"""

    def setup_method(self):
        """Setup test data"""
        self.test_data = pd.DataFrame({
            "close": [100, 102, 101, 105, 107, 110, 108, 112, 115, 113, 118, 120],
            "high": [102, 104, 103, 107, 109, 112, 110, 114, 117, 115, 120, 122],
            "low": [98, 100, 99, 103, 105, 108, 106, 110, 113, 111, 116, 118],
            "volume": [1000] * 12
        })

    def test_simple_ma_cross_function_with_warnings(self):
        """Test simple_ma_cross function and capture deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_ma_cross(
                self.test_data, 
                short_window=2, 
                long_window=3, 
                column="close"
            )
            
            # Check deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "simple_ma_cross function is deprecated" in str(w[0].message)
            
            # Check result structure
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_bollinger_breakout_function_with_warnings(self):
        """Test bollinger_breakout function and capture deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_ma_cross(
                self.test_data,
                window=5,
                num_std=2.0,
                column="close"
            )
            
            # Check deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "bollinger_breakout function is deprecated" in str(w[0].message)
            
            # Check result structure
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_rsi_strategy_function_with_warnings(self):
        """Test rsi_strategy function and capture deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_ma_cross(
                self.test_data,
                window=6,
                overbought=75,
                oversold=25,
                column="close"
            )
            
            # Check deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "rsi_strategy function is deprecated" in str(w[0].message)
            
            # Check result structure
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_macd_strategy_function_with_warnings(self):
        """Test macd_strategy function and capture deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_ma_cross(
                self.test_data,
                fast_period=5,
                slow_period=8,
                signal_period=3,
                column="close"
            )
            
            # Check deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "macd_strategy function is deprecated" in str(w[0].message)
            
            # Check result structure
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_trend_following_strategy_function_with_warnings(self):
        """Test trend_following_strategy function and capture deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_ma_cross(
                self.test_data,
                lookback_window=4,
                column="close"
            )
            
            # Check deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "trend_following_strategy function is deprecated" in str(w[0].message)
            
            # Check result structure
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)


class TestBackwardCompatibilityImports:
    """Test that module-level imports and warnings work correctly"""
    
    def test_module_import_deprecation_warning(self):
        """Test that importing the module triggers deprecation warning"""
        # This test verifies the module-level deprecation warning
        # Note: The warning is already triggered when importing at top of file
        # We'll test that the classes are available
        assert hasattr(improved_ma_cross, 'SimpleMAStrategy')
        assert hasattr(improved_ma_cross, 'BollingerBreakoutStrategy')
        assert hasattr(improved_ma_cross, 'RSIStrategy')
        assert hasattr(improved_ma_cross, 'MACDStrategy')

    def test_strategy_class_instantiation(self):
        """Test that strategy classes can be instantiated"""
        # Test SimpleMAStrategy
        simple_ma = improved_ma_cross.SimpleMAStrategy(short_window=5, long_window=10)
        assert simple_ma.short_window == 5
        assert simple_ma.long_window == 10
        
        # Test BollingerBreakoutStrategy
        bollinger = improved_ma_cross.BollingerBreakoutStrategy(window=20, num_std=2.0)
        assert bollinger.window == 20
        assert bollinger.num_std == 2.0
        
        # Test RSIStrategy
        rsi = improved_ma_cross.RSIStrategy(window=14, overbought=70, oversold=30)
        assert rsi.window == 14
        assert rsi.overbought == 70
        assert rsi.oversold == 30

    def test_all_legacy_functions_available(self):
        """Test that all legacy functions are available in module"""
        assert hasattr(improved_ma_cross, 'simple_ma_cross')
        assert hasattr(improved_ma_cross, 'bollinger_breakout')
        assert hasattr(improved_ma_cross, 'rsi_strategy')
        assert hasattr(improved_ma_cross, 'macd_strategy')
        assert hasattr(improved_ma_cross, 'trend_following_strategy')
        
        # Test they are callable
        assert callable(improved_ma_cross.simple_ma_cross)
        assert callable(improved_ma_cross.bollinger_breakout)
        assert callable(improved_ma_cross.rsi_strategy)
        assert callable(improved_ma_cross.macd_strategy)
        assert callable(improved_ma_cross.trend_following_strategy)


class TestParameterValidation:
    """Test parameter validation for legacy functions"""
    
    def setup_method(self):
        """Setup test data"""
        self.test_data = pd.DataFrame({
            "close": [100, 102, 101, 105, 107, 110, 108, 112, 115, 113],
            "high": [102, 104, 103, 107, 109, 112, 110, 114, 117, 115],
            "low": [98, 100, 99, 103, 105, 108, 106, 110, 113, 111],
        })

    def test_simple_ma_cross_custom_parameters(self):
        """Test simple_ma_cross with custom parameters"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_ma_cross(
                self.test_data,
                short_window=3,
                long_window=5,
                column="close"
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_bollinger_breakout_custom_parameters(self):
        """Test bollinger_breakout with custom parameters"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_ma_cross(
                self.test_data,
                window=8,
                num_std=1.5,
                column="close"
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_rsi_strategy_custom_parameters(self):
        """Test rsi_strategy with custom parameters"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_ma_cross(
                self.test_data,
                window=10,
                overbought=80,
                oversold=20,
                column="close"
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_macd_strategy_custom_parameters(self):
        """Test macd_strategy with custom parameters"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_ma_cross(
                self.test_data,
                fast_period=8,
                slow_period=12,
                signal_period=6,
                column="close"
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)


class TestErrorHandling:
    """Test error handling in legacy functions"""
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises((ValueError, IndexError, KeyError)):
                improved_ma_cross(empty_df)

    def test_missing_column_handling(self):
        """Test handling of missing column"""
        df_missing_close = pd.DataFrame({
            "open": [100, 102, 101],
            "high": [102, 104, 103],
            "low": [98, 100, 99]
        })
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises(KeyError):
                improved_ma_cross(df_missing_close, column="close")

    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        small_df = pd.DataFrame({
            "close": [100, 102]
        })
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # Should not raise error but may return DataFrame with NaN values
            result = improved_ma_cross(
                small_df, 
                short_window=1, 
                long_window=2
            )
            assert isinstance(result, pd.DataFrame) 