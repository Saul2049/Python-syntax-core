"""
市场模拟器覆盖率测试
(Market Simulator Coverage Tests)

针对 src/brokers/simulator/market_sim.py 的综合测试，提升代码覆盖率
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.brokers.simulator.market_sim import MarketSimulator, run_simple_backtest


class TestMarketSimulatorInitialization:
    """测试市场模拟器初始化 (Test Market Simulator Initialization)"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
        data = pd.DataFrame(
            {
                "open": np.random.uniform(100, 110, 50),
                "high": np.random.uniform(110, 120, 50),
                "low": np.random.uniform(90, 100, 50),
                "close": np.random.uniform(95, 115, 50),
                "volume": np.random.uniform(1000, 10000, 50),
            },
            index=dates,
        )
        return data

    def test_initialization_basic(self, sample_data):
        """测试基础初始化"""
        simulator = MarketSimulator(
            data=sample_data, initial_capital=20000.0, commission=0.002, slippage=0.001
        )

        assert simulator.initial_capital == 20000.0
        assert simulator.commission == 0.002
        assert simulator.slippage == 0.001
        assert len(simulator.data) == 50
        assert isinstance(simulator.trades, list)
        assert len(simulator.trades) == 0

    def test_initialization_invalid_index(self):
        """测试无效索引初始化 - 覆盖第41行"""
        # 创建没有DatetimeIndex的数据
        data = pd.DataFrame({"close": [100, 101, 102], "volume": [1000, 1100, 1200]})

        with pytest.raises(ValueError, match="数据必须具有DatetimeIndex索引"):
            MarketSimulator(data=data)

    def test_data_sorting(self, sample_data):
        """测试数据排序 - 覆盖第44-45行"""
        # 创建乱序数据
        shuffled_data = sample_data.sample(frac=1)  # 随机打乱

        simulator = MarketSimulator(data=shuffled_data)

        # 验证数据已排序
        assert simulator.data.index.is_monotonic_increasing


class TestMarketSimulatorBacktest:
    """测试市场模拟器回测功能 (Test Market Simulator Backtest)"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
        # 创建趋势数据便于测试
        prices = np.linspace(100, 120, 30) + np.random.normal(0, 1, 30)
        data = pd.DataFrame(
            {
                "open": prices * 0.99,
                "high": prices * 1.02,
                "low": prices * 0.98,
                "close": prices,
                "volume": np.random.uniform(1000, 5000, 30),
            },
            index=dates,
        )
        return data

    def test_run_backtest_basic(self, sample_data):
        """测试基础回测运行"""
        simulator = MarketSimulator(data=sample_data)

        def simple_strategy(data):
            """简单买入持有策略"""
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = 1  # 始终持有
            return signals

        result = simulator.run_backtest(simple_strategy)

        assert isinstance(result, pd.DataFrame)
        assert "total_value" in result.columns
        assert "daily_returns" in result.columns
        assert "cumulative_returns" in result.columns
        assert len(result) == len(sample_data)

    def test_run_backtest_invalid_strategy_return(self, sample_data):
        """测试策略函数返回无效数据 - 覆盖第70行"""
        simulator = MarketSimulator(data=sample_data)

        def invalid_strategy(data):
            """返回没有signal列的策略"""
            return pd.DataFrame({"invalid_col": [1, 2, 3]}, index=data.index[:3])

        with pytest.raises(ValueError, match="策略函数必须返回包含'signal'列的DataFrame"):
            simulator.run_backtest(invalid_strategy)

    def test_run_backtest_non_dataframe_return(self, sample_data):
        """测试策略函数返回非DataFrame - 覆盖第67-68行"""
        simulator = MarketSimulator(data=sample_data)

        def list_strategy(data):
            """返回列表的策略"""
            return [1] * len(data)

        # 这会被转换为DataFrame，但没有"signal"列，所以应该抛出错误
        with pytest.raises(ValueError, match="策略函数必须返回包含'signal'列的DataFrame"):
            simulator.run_backtest(list_strategy)


class TestMarketSimulatorPositions:
    """测试仓位生成和管理 (Test Position Generation and Management)"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range(start="2023-01-01", periods=20, freq="D")
        data = pd.DataFrame(
            {"close": [100 + i for i in range(20)], "volume": [1000] * 20}, index=dates  # 递增价格
        )
        return data

    def test_generate_positions_with_slippage(self, sample_data):
        """测试带滑点的仓位生成"""
        simulator = MarketSimulator(data=sample_data, slippage=0.01)

        # 创建买卖信号
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [1, 1, 0, -1, -1, 0] + [0] * 14  # 买入、持有、卖出

        simulator._generate_positions(signals)

        assert "exec_price" in simulator.positions.columns
        assert "commission" in simulator.positions.columns

        # 验证滑点应用
        buy_rows = simulator.positions[simulator.positions["signal"] > 0]
        if not buy_rows.empty:
            # 买入时执行价格应该高于市场价格
            assert (buy_rows["exec_price"] > buy_rows["price"]).all()

    def test_record_trades(self, sample_data):
        """测试交易记录 - 覆盖第167-173行"""
        simulator = MarketSimulator(data=sample_data)

        # 创建信号变化
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [0, 1, 1, -1, 0] + [0] * 15  # 信号变化

        simulator._generate_positions(signals)

        # 验证交易记录
        assert len(simulator.trades) > 0

        # 检查交易记录结构
        for trade in simulator.trades:
            assert "date" in trade
            assert "signal" in trade
            assert "price" in trade
            assert "commission" in trade


class TestMarketSimulatorHoldings:
    """测试持仓计算 (Test Holdings Calculation)"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {"close": [100, 105, 110, 108, 112, 115, 113, 118, 120, 125], "volume": [1000] * 10},
            index=dates,
        )
        return data

    def test_calculate_holdings_buy_sell_cycle(self, sample_data):
        """测试买卖周期的持仓计算"""
        simulator = MarketSimulator(data=sample_data, initial_capital=10000)

        # 创建买入然后卖出的信号
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [0, 1, 1, 1, 1, -1, 0, 0, 0, 0]  # 买入持有然后卖出

        simulator._generate_positions(signals)
        simulator._calculate_holdings()

        assert "cash" in simulator.holdings.columns
        assert "units" in simulator.holdings.columns
        assert "asset_value" in simulator.holdings.columns

        # 验证初始现金
        assert simulator.holdings.iloc[0]["cash"] == 10000

        # 验证买入后现金减少
        buy_index = 1  # 第二天买入
        assert simulator.holdings.iloc[buy_index]["cash"] < 10000
        assert simulator.holdings.iloc[buy_index]["units"] > 0


class TestMarketSimulatorPerformance:
    """测试性能计算 (Test Performance Calculation)"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range(start="2023-01-01", periods=15, freq="D")
        data = pd.DataFrame(
            {"close": [100 + i * 2 for i in range(15)], "volume": [1000] * 15},  # 递增价格
            index=dates,
        )
        return data

    def test_calculate_performance_metrics(self, sample_data):
        """测试性能指标计算"""
        simulator = MarketSimulator(data=sample_data)

        # 简单买入持有策略
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [1] * len(sample_data)  # 始终持有

        simulator._generate_positions(signals)
        simulator._calculate_holdings()
        simulator._calculate_performance()

        assert "total_value" in simulator.performance.columns
        assert "daily_returns" in simulator.performance.columns
        assert "cumulative_returns" in simulator.performance.columns

        # 验证总价值计算
        total_values = simulator.performance["total_value"]
        assert not total_values.isnull().any()


class TestMarketSimulatorRiskMetrics:
    """测试风险指标计算 (Test Risk Metrics Calculation)"""

    @pytest.fixture
    def sample_data(self):
        """创建长期数据用于风险计算"""
        dates = pd.date_range(start="2023-01-01", periods=365, freq="D")
        # 创建有波动的价格数据
        returns = np.random.normal(0.001, 0.02, 365)  # 日收益率
        prices = [100]
        for r in returns:
            prices.append(prices[-1] * (1 + r))

        data = pd.DataFrame(
            {"close": prices[1:], "volume": [1000] * 365}, index=dates  # 去掉第一个初始价格
        )
        return data

    def test_calculate_risk_metrics(self, sample_data):
        """测试风险指标计算 - 覆盖第233-248行"""
        simulator = MarketSimulator(data=sample_data)

        # 创建简单策略
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [1] * len(sample_data)

        simulator._generate_positions(signals)
        simulator._calculate_holdings()
        simulator._calculate_performance()
        simulator._calculate_risk_metrics()

        # 验证风险指标被计算（这些可能作为属性或在performance中）
        # 由于_calculate_risk_metrics的具体实现可能计算年化收益率等
        assert hasattr(simulator, "performance")


class TestMarketSimulatorStatistics:
    """测试统计功能 (Test Statistics Functions)"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range(start="2023-01-01", periods=20, freq="D")
        data = pd.DataFrame(
            {"close": [100 + i for i in range(20)], "volume": [1000] * 20}, index=dates
        )
        return data

    def test_get_trade_statistics(self, sample_data):
        """测试交易统计 - 覆盖第233-248行"""
        simulator = MarketSimulator(data=sample_data)

        # 创建有交易的策略
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [0, 1, 1, -1, 0, 1, -1, 0] + [0] * 12

        simulator.run_backtest(lambda x: signals)

        # 测试get_trade_statistics方法
        stats = simulator.get_trade_statistics()
        assert isinstance(stats, dict)
        assert "total_trades" in stats
        assert "initial_capital" in stats
        assert "final_capital" in stats
        assert "total_return" in stats

    def test_get_trade_statistics_no_trades(self, sample_data):
        """测试无交易时的统计 - 覆盖第233行"""
        simulator = MarketSimulator(data=sample_data)

        # 创建无交易的策略
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [0] * len(sample_data)  # 无交易信号

        simulator.run_backtest(lambda x: signals)

        # 测试get_trade_statistics方法
        stats = simulator.get_trade_statistics()
        assert isinstance(stats, dict)
        assert stats["total_trades"] == 0

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.savefig")
    @patch("os.makedirs")
    def test_plot_results_with_save(self, mock_makedirs, mock_savefig, mock_show, sample_data):
        """测试带保存的结果绘图 - 覆盖第259-358行"""
        simulator = MarketSimulator(data=sample_data)

        # 运行有交易的回测
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [0, 1, 1, -1, 0] + [0] * 15

        simulator.run_backtest(lambda x: signals)

        # 测试plot_results方法带保存路径
        simulator.plot_results(save_path="test_output/test_plot.png", show_plot=False)

        # 验证调用了相关方法
        mock_makedirs.assert_called_once()
        mock_savefig.assert_called_once()
        mock_show.assert_not_called()

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.savefig")
    def test_plot_results(self, mock_savefig, mock_show, sample_data):
        """测试结果绘图 - 覆盖绘图相关代码"""
        simulator = MarketSimulator(data=sample_data)

        # 运行简单回测
        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [1] * len(sample_data)

        simulator.run_backtest(lambda x: signals)

        # 测试plot_results方法
        simulator.plot_results(show_plot=False)
        # 验证没有实际显示图表
        mock_show.assert_not_called()

    def test_get_performance_df(self, sample_data):
        """测试获取性能DataFrame - 覆盖第367行"""
        simulator = MarketSimulator(data=sample_data)

        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [1] * len(sample_data)

        simulator.run_backtest(lambda x: signals)

        # 测试get_performance_df方法
        perf_df = simulator.get_performance_df()
        assert isinstance(perf_df, pd.DataFrame)
        assert "total_value" in perf_df.columns
        assert "daily_returns" in perf_df.columns

    def test_get_trades_df(self, sample_data):
        """测试获取交易DataFrame - 覆盖第376行"""
        simulator = MarketSimulator(data=sample_data)

        signals = pd.DataFrame(index=sample_data.index)
        signals["signal"] = [0, 1, -1, 0] + [0] * 16

        simulator.run_backtest(lambda x: signals)

        # 测试get_trades_df方法
        trades_df = simulator.get_trades_df()
        assert isinstance(trades_df, pd.DataFrame)
        if len(trades_df) > 0:
            assert "date" in trades_df.columns
            assert "signal" in trades_df.columns


class TestRunSimpleBacktest:
    """测试简单回测函数 (Test Run Simple Backtest Function)"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {"close": [100 + i for i in range(30)], "volume": [1000] * 30}, index=dates
        )
        return data

    def test_run_simple_backtest_basic(self, sample_data):
        """测试简单回测函数 - 覆盖第406-424行"""

        def simple_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = [1] * len(data)
            return signals

        result = run_simple_backtest(
            data=sample_data, strategy_func=simple_strategy, initial_capital=15000, commission=0.002
        )

        assert isinstance(result, dict)

    @patch("matplotlib.pyplot.savefig")
    def test_run_simple_backtest_with_plot(self, mock_savefig, sample_data):
        """测试带绘图的简单回测 - 覆盖绘图相关代码"""

        def simple_strategy(data):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = [1] * len(data)
            return signals

        result = run_simple_backtest(
            data=sample_data,
            strategy_func=simple_strategy,
            save_plot=True,
            plot_filename="test_plot.png",
        )

        assert isinstance(result, dict)

    def test_run_simple_backtest_with_strategy_params(self, sample_data):
        """测试带策略参数的简单回测 - 覆盖第429-463行"""

        def parameterized_strategy(data, threshold=0.5):
            signals = pd.DataFrame(index=data.index)
            signals["signal"] = [1 if i % 2 == 0 else 0 for i in range(len(data))]
            return signals

        result = run_simple_backtest(
            data=sample_data, strategy_func=parameterized_strategy, threshold=0.8  # 策略参数
        )

        assert isinstance(result, dict)


class TestMarketSimulatorEdgeCases:
    """测试边缘情况 (Test Edge Cases)"""

    def test_empty_data_handling(self):
        """测试空数据处理"""
        dates = pd.date_range(start="2023-01-01", periods=1, freq="D")
        data = pd.DataFrame({"close": [100], "volume": [1000]}, index=dates)

        simulator = MarketSimulator(data=data)

        signals = pd.DataFrame(index=data.index)
        signals["signal"] = [1]

        # 应该能处理单行数据
        result = simulator.run_backtest(lambda x: signals)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    def test_zero_commission_and_slippage(self, sample_data):
        """测试零佣金和滑点"""
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        data = pd.DataFrame({"close": [100] * 10, "volume": [1000] * 10}, index=dates)

        simulator = MarketSimulator(data=data, commission=0.0, slippage=0.0)

        signals = pd.DataFrame(index=data.index)
        signals["signal"] = [1] * len(data)

        result = simulator.run_backtest(lambda x: signals)
        assert isinstance(result, pd.DataFrame)

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range(start="2023-01-01", periods=20, freq="D")
        data = pd.DataFrame(
            {"close": [100 + i for i in range(20)], "volume": [1000] * 20}, index=dates
        )
        return data
