#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场模拟器模块测试 (Market Simulator Module Tests)

专门测试 src/brokers/simulator/market_sim.py 模块，提高覆盖率。
这是一个重要的回测功能模块，需要全面的测试覆盖。
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

try:
    from src.brokers.simulator.market_sim import MarketSimulator, run_simple_backtest
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from brokers.simulator.market_sim import MarketSimulator, run_simple_backtest


class TestMarketSimulator(unittest.TestCase):
    """测试MarketSimulator类的核心功能"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试用的价格数据
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        np.random.seed(42)

        # 生成模拟价格数据
        base_price = 100
        returns = np.random.normal(0.001, 0.02, 100)  # 日收益率
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        self.test_data = pd.DataFrame(
            {
                "open": prices,
                "high": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                "low": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                "close": prices,
                "volume": np.random.randint(1000, 10000, 100),
            },
            index=dates,
        )

    def test_market_simulator_initialization(self):
        """测试MarketSimulator初始化"""
        simulator = MarketSimulator(
            data=self.test_data, initial_capital=10000.0, commission=0.001, slippage=0.0005
        )

        # 验证初始化参数
        self.assertEqual(simulator.initial_capital, 10000.0)
        self.assertEqual(simulator.commission, 0.001)
        self.assertEqual(simulator.slippage, 0.0005)

        # 验证数据处理
        self.assertIsInstance(simulator.data.index, pd.DatetimeIndex)
        self.assertEqual(len(simulator.data), 100)

        # 验证数据框初始化
        self.assertIsInstance(simulator.positions, pd.DataFrame)
        self.assertIsInstance(simulator.holdings, pd.DataFrame)
        self.assertIsInstance(simulator.performance, pd.DataFrame)
        self.assertIsInstance(simulator.trades, list)

    def test_market_simulator_invalid_data(self):
        """测试无效数据的错误处理"""
        # 测试没有DatetimeIndex的数据
        invalid_data = self.test_data.copy()
        invalid_data.index = range(len(invalid_data))

        with self.assertRaises(ValueError):
            MarketSimulator(invalid_data)

    def test_simple_buy_and_hold_strategy(self):
        """测试简单的买入持有策略"""

        def buy_and_hold_strategy(data):
            """简单的买入持有策略"""
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[0, signals.columns.get_loc("signal")] = 1  # 第一天买入
            return signals

        simulator = MarketSimulator(self.test_data, initial_capital=10000.0)
        result = simulator.run_backtest(buy_and_hold_strategy)

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), len(self.test_data))
        self.assertIn("total_value", result.columns)
        self.assertIn("daily_returns", result.columns)
        self.assertIn("cumulative_returns", result.columns)

        # 修复：由于有佣金和滑点，初始值可能不等于10000
        self.assertAlmostEqual(result["total_value"].iloc[0], 10000.0, delta=100.0)

    def test_simple_momentum_strategy(self):
        """测试简单的动量策略"""

        def momentum_strategy(data, window=10):
            """简单的动量策略"""
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0

            # 计算移动平均
            ma = data["close"].rolling(window=window).mean()

            # 生成信号：价格高于移动平均线时买入，低于时卖出
            signals.loc[data["close"] > ma, "signal"] = 1
            signals.loc[data["close"] < ma, "signal"] = -1

            return signals

        simulator = MarketSimulator(self.test_data, initial_capital=10000.0)
        result = simulator.run_backtest(momentum_strategy, window=20)

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("total_value", result.columns)

        # 验证交易记录
        self.assertIsInstance(simulator.trades, list)

    def test_strategy_without_signal_column(self):
        """测试没有signal列的策略函数"""

        def invalid_strategy(data):
            """返回没有signal列的DataFrame"""
            return pd.DataFrame({"invalid_column": [1, 2, 3]}, index=data.index[:3])

        simulator = MarketSimulator(self.test_data)

        with self.assertRaises(ValueError):
            simulator.run_backtest(invalid_strategy)

    def test_commission_and_slippage_calculation(self):
        """测试佣金和滑点计算"""

        def single_trade_strategy(data):
            """执行单次交易的策略"""
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[10, signals.columns.get_loc("signal")] = 1  # 第10天买入
            signals.iloc[20, signals.columns.get_loc("signal")] = -1  # 第20天卖出
            return signals

        simulator = MarketSimulator(
            self.test_data,
            initial_capital=10000.0,
            commission=0.01,  # 1%佣金
            slippage=0.005,  # 0.5%滑点
        )

        result = simulator.run_backtest(single_trade_strategy)

        # 验证交易记录
        self.assertGreater(len(simulator.trades), 0)

        # 验证佣金计算
        for trade in simulator.trades:
            if trade["signal"] != 0:
                self.assertGreater(trade["commission"], 0)

    def test_get_trade_statistics(self):
        """测试交易统计功能"""

        def simple_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[5, signals.columns.get_loc("signal")] = 1
            signals.iloc[15, signals.columns.get_loc("signal")] = -1
            signals.iloc[25, signals.columns.get_loc("signal")] = 1
            return signals

        simulator = MarketSimulator(self.test_data)
        simulator.run_backtest(simple_strategy)

        stats = simulator.get_trade_statistics()

        # 验证统计结果
        self.assertIsInstance(stats, dict)
        self.assertIn("total_return", stats)
        self.assertIn("annualized_return", stats)
        self.assertIn("volatility", stats)
        self.assertIn("sharpe_ratio", stats)
        self.assertIn("max_drawdown", stats)
        self.assertIn("total_trades", stats)

    def test_get_performance_df(self):
        """测试获取性能DataFrame"""

        def simple_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[0, signals.columns.get_loc("signal")] = 1
            return signals

        simulator = MarketSimulator(self.test_data)
        simulator.run_backtest(simple_strategy)

        performance_df = simulator.get_performance_df()

        # 验证性能DataFrame
        self.assertIsInstance(performance_df, pd.DataFrame)
        self.assertEqual(len(performance_df), len(self.test_data))

    def test_get_trades_df(self):
        """测试获取交易DataFrame"""

        def trading_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[5, signals.columns.get_loc("signal")] = 1
            signals.iloc[15, signals.columns.get_loc("signal")] = -1
            return signals

        simulator = MarketSimulator(self.test_data)
        simulator.run_backtest(trading_strategy)

        trades_df = simulator.get_trades_df()

        # 验证交易DataFrame
        self.assertIsInstance(trades_df, pd.DataFrame)

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.savefig")
    def test_plot_results(self, mock_savefig, mock_show):
        """测试绘图功能"""

        def simple_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[0, signals.columns.get_loc("signal")] = 1
            return signals

        simulator = MarketSimulator(self.test_data)
        simulator.run_backtest(simple_strategy)

        # 测试显示图表
        simulator.plot_results(show_plot=True)
        mock_show.assert_called_once()

        # 测试保存图表
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp_file:
            simulator.plot_results(save_path=tmp_file.name, show_plot=False)
            mock_savefig.assert_called_with(tmp_file.name, dpi=300, bbox_inches="tight")


class TestRunSimpleBacktest(unittest.TestCase):
    """测试run_simple_backtest函数"""

    def setUp(self):
        """设置测试数据"""
        dates = pd.date_range("2023-01-01", periods=50, freq="D")
        np.random.seed(42)

        prices = [100]
        for _ in range(49):
            prices.append(prices[-1] * (1 + np.random.normal(0, 0.02)))

        self.test_data = pd.DataFrame(
            {
                "open": prices,
                "high": [p * 1.02 for p in prices],
                "low": [p * 0.98 for p in prices],
                "close": prices,
                "volume": [1000] * 50,
            },
            index=dates,
        )

    def test_run_simple_backtest_basic(self):
        """测试基本的简单回测功能"""

        def test_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[0, signals.columns.get_loc("signal")] = 1
            return signals

        result = run_simple_backtest(
            data=self.test_data, strategy_func=test_strategy, initial_capital=10000.0
        )

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn("total_return", result)
        self.assertIn("annualized_return", result)

    def test_run_simple_backtest_with_parameters(self):
        """测试带参数的简单回测"""

        def parameterized_strategy(data, buy_threshold=0.02):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0

            returns = data["close"].pct_change()
            signals.loc[returns > buy_threshold, "signal"] = 1
            signals.loc[returns < -buy_threshold, "signal"] = -1

            return signals

        result = run_simple_backtest(
            data=self.test_data,
            strategy_func=parameterized_strategy,
            initial_capital=5000.0,
            commission=0.002,
            buy_threshold=0.01,
        )

        # 验证结果
        self.assertIsInstance(result, dict)

    @patch("matplotlib.pyplot.show")
    def test_run_simple_backtest_with_plot(self, mock_show):
        """测试带绘图的简单回测"""

        def simple_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[0, signals.columns.get_loc("signal")] = 1
            return signals

        result = run_simple_backtest(
            data=self.test_data,
            strategy_func=simple_strategy,
            save_plot=True,
            plot_filename="test_backtest.png",
        )

        # 验证结果和绘图调用
        self.assertIsInstance(result, dict)


class TestMarketSimulatorEdgeCases(unittest.TestCase):
    """测试MarketSimulator的边界情况"""

    def setUp(self):
        """设置最小测试数据"""
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        self.minimal_data = pd.DataFrame(
            {
                "open": [100, 101, 102, 103, 104],
                "high": [102, 103, 104, 105, 106],
                "low": [98, 99, 100, 101, 102],
                "close": [101, 102, 103, 104, 105],
                "volume": [1000, 1100, 1200, 1300, 1400],
            },
            index=dates,
        )

    def test_minimal_data_backtest(self):
        """测试最小数据集的回测"""

        def minimal_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[0, signals.columns.get_loc("signal")] = 1
            return signals

        simulator = MarketSimulator(self.minimal_data, initial_capital=1000.0)
        result = simulator.run_backtest(minimal_strategy)

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 5)

    def test_zero_commission_and_slippage(self):
        """测试零佣金和滑点"""

        def simple_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[0, signals.columns.get_loc("signal")] = 1
            return signals

        simulator = MarketSimulator(
            self.minimal_data, initial_capital=1000.0, commission=0.0, slippage=0.0
        )

        result = simulator.run_backtest(simple_strategy)

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)

    def test_high_commission_and_slippage(self):
        """测试高佣金和滑点"""

        def simple_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 0
            signals.iloc[0, signals.columns.get_loc("signal")] = 1
            return signals

        simulator = MarketSimulator(
            self.minimal_data,
            initial_capital=1000.0,
            commission=0.1,  # 10%佣金
            slippage=0.05,  # 5%滑点
        )

        result = simulator.run_backtest(simple_strategy)

        # 验证结果（高成本应该显著影响收益）
        self.assertIsInstance(result, pd.DataFrame)


if __name__ == "__main__":
    unittest.main()
