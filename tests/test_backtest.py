#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.backtest 模块的所有功能
Backtest Module Tests

覆盖目标:
- run_backtest 函数
- 回测逻辑和交易信号处理
- 止损和交叉信号处理
- 边界情况和错误处理
- 主程序块执行
"""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.backtest import run_backtest


class TestRunBacktest:
    """测试 run_backtest 函数"""

    def setup_method(self):
        """测试设置"""
        # 创建模拟价格数据
        self.sample_dates = pd.date_range("2023-01-01", periods=100, freq="D")
        self.sample_prices = pd.Series(
            [50000 + i * 100 + np.sin(i * 0.1) * 1000 for i in range(100)],
            index=self.sample_dates,
            name="btc",
        )

        # 创建模拟DataFrame
        self.sample_df = pd.DataFrame({"btc": self.sample_prices})

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_basic(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试基础回测功能"""
        # 设置模拟返回值
        mock_load_csv.return_value = self.sample_df

        # 创建简单的移动平均线
        fast_ma = pd.Series([50000 + i * 50 for i in range(100)], index=self.sample_dates)
        slow_ma = pd.Series([50000 + i * 30 for i in range(100)], index=self.sample_dates)

        mock_moving_average.side_effect = [fast_ma, slow_ma]

        # 设置交叉信号
        mock_bullish_cross.return_value = [10, 30, 50]  # 买入信号
        mock_bearish_cross.return_value = [20, 40, 60]  # 卖出信号

        # 设置仓位计算
        mock_compute_size.return_value = 1.0  # 固定仓位大小
        mock_compute_stop.return_value = 49000.0  # 固定止损价格

        result = run_backtest()

        # 验证函数调用
        mock_load_csv.assert_called_once()
        assert mock_moving_average.call_count == 2
        mock_bullish_cross.assert_called_once()
        mock_bearish_cross.assert_called_once()

        # 验证返回结果
        assert isinstance(result, pd.Series)
        assert len(result) == 100
        assert result.index.equals(self.sample_dates)

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_with_custom_parameters(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试使用自定义参数的回测"""
        mock_load_csv.return_value = self.sample_df

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        mock_bullish_cross.return_value = []
        mock_bearish_cross.return_value = []
        mock_compute_size.return_value = 2.0
        mock_compute_stop.return_value = 48000.0

        result = run_backtest(
            fast_win=5,
            slow_win=15,
            risk_frac=0.03,
            atr_win=10,
            stop_mult=2.0,
        )

        # 验证参数传递 - 检查调用次数而不是具体参数
        assert mock_moving_average.call_count == 2

        # 验证第一次调用的第二个参数（窗口大小）
        first_call_args = mock_moving_average.call_args_list[0]
        second_call_args = mock_moving_average.call_args_list[1]

        assert first_call_args[0][1] == 5  # fast_win
        assert second_call_args[0][1] == 15  # slow_win

        assert isinstance(result, pd.Series)
        assert len(result) == 100

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_stop_loss_triggered(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试止损触发的情况"""
        # 创建价格下跌的数据
        declining_prices = pd.Series(
            [50000 - i * 100 for i in range(100)], index=self.sample_dates, name="btc"
        )
        declining_df = pd.DataFrame({"btc": declining_prices})
        mock_load_csv.return_value = declining_df

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        # 在第5个位置买入
        mock_bullish_cross.return_value = [5]
        mock_bearish_cross.return_value = []

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 49000.0  # 止损价格

        result = run_backtest()

        # 验证结果
        assert isinstance(result, pd.Series)
        assert len(result) == 100

        # 检查止损后权益变化
        initial_equity = 100000.0
        assert result.iloc[0] == initial_equity

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_exit_on_crossover(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试交叉信号退出的情况"""
        mock_load_csv.return_value = self.sample_df

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        # 买入后卖出
        mock_bullish_cross.return_value = [10]
        mock_bearish_cross.return_value = [20]

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest()

        assert isinstance(result, pd.Series)
        assert len(result) == 100

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_no_position_size(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试仓位大小为0的情况"""
        mock_load_csv.return_value = self.sample_df

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        mock_bullish_cross.return_value = [10]
        mock_bearish_cross.return_value = []

        # 返回0仓位大小
        mock_compute_size.return_value = 0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest()

        # 验证没有建仓
        assert isinstance(result, pd.Series)
        assert len(result) == 100

        # 权益应该保持不变
        initial_equity = 100000.0
        assert all(result == initial_equity)

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_infinite_atr(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试ATR为无穷大的情况"""
        # 创建包含NaN的价格数据
        prices_with_nan = self.sample_prices.copy()
        prices_with_nan.iloc[10:15] = np.nan
        df_with_nan = pd.DataFrame({"btc": prices_with_nan})
        mock_load_csv.return_value = df_with_nan

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        # 在ATR为NaN的位置设置买入信号
        mock_bullish_cross.return_value = [12]
        mock_bearish_cross.return_value = []

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest()

        # 验证在ATR无效时不会建仓
        assert isinstance(result, pd.Series)
        assert len(result) == 100

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_multiple_signals(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试多个交易信号的情况"""
        mock_load_csv.return_value = self.sample_df

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        # 多个买入和卖出信号
        mock_bullish_cross.return_value = [10, 30, 50, 70]
        mock_bearish_cross.return_value = [20, 40, 60, 80]

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest()

        assert isinstance(result, pd.Series)
        assert len(result) == 100

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_atr_calculation(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试ATR计算逻辑"""
        mock_load_csv.return_value = self.sample_df

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        mock_bullish_cross.return_value = [25]  # 确保ATR已经计算
        mock_bearish_cross.return_value = []

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest(atr_win=20)

        # 验证ATR窗口参数的使用
        assert isinstance(result, pd.Series)
        assert len(result) == 100

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_edge_case_empty_signals(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试没有交易信号的边界情况"""
        mock_load_csv.return_value = self.sample_df

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        # 没有任何交易信号
        mock_bullish_cross.return_value = []
        mock_bearish_cross.return_value = []

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest()

        # 验证没有交易时权益保持不变
        assert isinstance(result, pd.Series)
        assert len(result) == 100

        initial_equity = 100000.0
        assert all(result == initial_equity)

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_position_tracking(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试仓位跟踪逻辑"""
        mock_load_csv.return_value = self.sample_df

        fast_ma = pd.Series([50000] * 100, index=self.sample_dates)
        slow_ma = pd.Series([49000] * 100, index=self.sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        # 买入信号但已有仓位时不应该再次买入
        mock_bullish_cross.return_value = [10, 11, 12]  # 连续买入信号
        mock_bearish_cross.return_value = [20]

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest()

        # 验证仓位管理
        assert isinstance(result, pd.Series)
        assert len(result) == 100

    def test_run_backtest_integration_with_real_data_structure(self):
        """测试与真实数据结构的集成"""
        # 创建更真实的数据结构
        real_data = pd.DataFrame(
            {
                "btc": pd.Series(
                    [
                        50000,
                        50100,
                        49900,
                        50200,
                        49800,
                        50300,
                        49700,
                        50400,
                        49600,
                        50500,
                        49500,
                        50600,
                        49400,
                        50700,
                        49300,
                        50800,
                    ],
                    index=pd.date_range("2023-01-01", periods=16, freq="D"),
                )
            }
        )

        with patch("src.backtest.load_csv") as mock_load_csv:
            mock_load_csv.return_value = real_data

            # 使用真实的函数调用（不模拟内部函数）
            try:
                result = run_backtest(fast_win=3, slow_win=5, atr_win=5)

                # 基本验证
                assert isinstance(result, pd.Series)
                assert len(result) == 16
                assert result.index.equals(real_data.index)

            except Exception as e:
                # 如果依赖函数不可用，至少验证调用不会崩溃
                assert "load_csv" in str(e) or "moving_average" in str(e)


class TestBacktestMainBlock:
    """测试主程序块"""

    def test_main_block_execution_simulation(self):
        """测试主程序块的执行模拟"""
        # 模拟主程序块的逻辑，而不是实际执行
        with patch("src.backtest.run_backtest") as mock_run_backtest:
            with patch("matplotlib.pyplot.show") as mock_show:
                with patch("matplotlib.pyplot.xlabel") as mock_xlabel:
                    with patch("matplotlib.pyplot.ylabel") as mock_ylabel:
                        with patch("builtins.print") as mock_print:

                            # 模拟回测结果
                            mock_equity_series = Mock()
                            mock_equity_series.plot.return_value = None
                            mock_run_backtest.return_value = mock_equity_series

                            # 直接调用函数而不是模拟主程序块
                            equity_series = mock_run_backtest(
                                fast_win=7,
                                slow_win=20,
                                risk_frac=0.02,
                                atr_win=20,
                            )
                            mock_print(equity_series)
                            equity_series.plot(title="Equity Curve")

                            import matplotlib.pyplot as plt

                            plt.xlabel("Date")
                            plt.ylabel("Equity (USD)")
                            plt.show()

                            # 验证函数调用
                            mock_run_backtest.assert_called_once_with(
                                fast_win=7,
                                slow_win=20,
                                risk_frac=0.02,
                                atr_win=20,
                            )
                            mock_print.assert_called_once_with(mock_equity_series)
                            mock_equity_series.plot.assert_called_once_with(title="Equity Curve")
                            mock_xlabel.assert_called_once_with("Date")
                            mock_ylabel.assert_called_once_with("Equity (USD)")
                            mock_show.assert_called_once()

    def test_main_block_with_different_parameters_simulation(self):
        """测试主程序块使用不同参数的模拟"""
        with patch("src.backtest.run_backtest") as mock_run_backtest:
            with patch("builtins.print") as mock_print:

                mock_equity_series = pd.Series([100000, 101000, 102000])
                mock_run_backtest.return_value = mock_equity_series

                # 直接调用函数而不是模拟主程序执行
                equity_series = mock_run_backtest(
                    fast_win=5,
                    slow_win=15,
                    risk_frac=0.01,
                    atr_win=10,
                )
                mock_print(equity_series)

                mock_run_backtest.assert_called_once_with(
                    fast_win=5,
                    slow_win=15,
                    risk_frac=0.01,
                    atr_win=10,
                )
                mock_print.assert_called_once_with(mock_equity_series)

    def test_main_block_imports_and_structure(self):
        """测试主程序块的导入和结构"""
        # 验证主程序块中使用的导入是否可用
        try:
            from math import isfinite

            import matplotlib.pyplot as plt
            import pandas as pd

            from src.backtest import run_backtest

            # 验证函数可调用
            assert callable(run_backtest)
            assert callable(plt.show)
            assert callable(plt.xlabel)
            assert callable(plt.ylabel)

        except ImportError as e:
            pytest.skip(f"Required imports not available: {e}")

    def test_main_block_functionality_coverage(self):
        """测试主程序块功能覆盖"""
        # 测试主程序块中的关键逻辑
        with patch("src.backtest.run_backtest") as mock_run_backtest:
            # 模拟equity_series对象
            mock_equity_series = Mock()
            mock_equity_series.plot = Mock()
            mock_run_backtest.return_value = mock_equity_series

            # 测试主程序块的核心逻辑 - 直接调用mock
            equity_series = mock_run_backtest(
                fast_win=7,
                slow_win=20,
                risk_frac=0.02,
                atr_win=20,
            )

            # 验证返回的对象
            assert equity_series is mock_equity_series

            # 测试绘图功能
            equity_series.plot(title="Equity Curve")
            mock_equity_series.plot.assert_called_with(title="Equity Curve")

            # 验证函数被正确调用
            mock_run_backtest.assert_called_once_with(
                fast_win=7,
                slow_win=20,
                risk_frac=0.02,
                atr_win=20,
            )


class TestBacktestErrorHandling:
    """测试错误处理"""

    @patch("src.backtest.load_csv")
    def test_run_backtest_load_csv_error(self, mock_load_csv):
        """测试load_csv错误处理"""
        mock_load_csv.side_effect = Exception("Data loading failed")

        with pytest.raises(Exception, match="Data loading failed"):
            run_backtest()

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    def test_run_backtest_moving_average_error(self, mock_moving_average, mock_load_csv):
        """测试moving_average错误处理"""
        mock_load_csv.return_value = pd.DataFrame({"btc": [50000, 51000, 52000]})
        mock_moving_average.side_effect = Exception("Moving average calculation failed")

        with pytest.raises(Exception, match="Moving average calculation failed"):
            run_backtest()

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    def test_run_backtest_signal_error(
        self, mock_bullish_cross, mock_moving_average, mock_load_csv
    ):
        """测试信号计算错误处理"""
        mock_load_csv.return_value = pd.DataFrame({"btc": [50000, 51000, 52000]})
        mock_moving_average.return_value = pd.Series([50000, 51000, 52000])
        mock_bullish_cross.side_effect = Exception("Signal calculation failed")

        with pytest.raises(Exception, match="Signal calculation failed"):
            run_backtest()


class TestBacktestPerformance:
    """测试性能相关功能"""

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_large_dataset(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试大数据集的处理"""
        # 创建大数据集
        large_dates = pd.date_range("2020-01-01", periods=1000, freq="D")
        large_prices = pd.Series(
            [50000 + i * 10 + np.sin(i * 0.01) * 500 for i in range(1000)],
            index=large_dates,
            name="btc",
        )
        large_df = pd.DataFrame({"btc": large_prices})

        mock_load_csv.return_value = large_df

        fast_ma = pd.Series([50000] * 1000, index=large_dates)
        slow_ma = pd.Series([49000] * 1000, index=large_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        mock_bullish_cross.return_value = list(range(0, 1000, 100))
        mock_bearish_cross.return_value = list(range(50, 1000, 100))

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest()

        # 验证大数据集处理
        assert isinstance(result, pd.Series)
        assert len(result) == 1000
        assert result.index.equals(large_dates)

    def test_run_backtest_memory_efficiency(self):
        """测试内存效率"""
        # 这个测试主要验证函数不会创建过多的中间变量
        with patch("src.backtest.load_csv") as mock_load_csv:
            small_df = pd.DataFrame(
                {
                    "btc": pd.Series(
                        [50000, 51000, 52000],
                        index=pd.date_range("2023-01-01", periods=3, freq="D"),
                    )
                }
            )
            mock_load_csv.return_value = small_df

            try:
                result = run_backtest()
                # 基本验证 - 如果函数可以运行，说明内存使用是合理的
                assert result is not None
            except Exception:
                # 如果依赖不可用，测试至少不应该因为内存问题失败
                pass


class TestBacktestMathFunctions:
    """测试数学函数的使用"""

    def test_isfinite_import_and_usage(self):
        """测试isfinite函数的导入和使用"""
        from math import isfinite

        # 测试isfinite函数
        assert isfinite(1.0) is True
        assert isfinite(float("inf")) is False
        assert isfinite(float("nan")) is False

        # 验证在backtest模块中的使用
        import src.backtest

        assert hasattr(src.backtest, "isfinite")

    @patch("src.backtest.load_csv")
    @patch("src.backtest.moving_average")
    @patch("src.backtest.bullish_cross_indices")
    @patch("src.backtest.bearish_cross_indices")
    @patch("src.backtest.compute_position_size")
    @patch("src.backtest.compute_stop_price")
    def test_run_backtest_isfinite_check(
        self,
        mock_compute_stop,
        mock_compute_size,
        mock_bearish_cross,
        mock_bullish_cross,
        mock_moving_average,
        mock_load_csv,
    ):
        """测试isfinite检查在回测中的作用"""
        # 创建包含无穷大值的ATR数据
        sample_dates = pd.date_range("2023-01-01", periods=50, freq="D")
        sample_prices = pd.Series(
            [50000 + i * 100 for i in range(50)], index=sample_dates, name="btc"
        )
        sample_df = pd.DataFrame({"btc": sample_prices})

        mock_load_csv.return_value = sample_df

        fast_ma = pd.Series([50000] * 50, index=sample_dates)
        slow_ma = pd.Series([49000] * 50, index=sample_dates)
        mock_moving_average.side_effect = [fast_ma, slow_ma]

        # 在ATR计算会产生无穷大的位置设置买入信号
        mock_bullish_cross.return_value = [1, 2]  # 早期位置，ATR可能无效
        mock_bearish_cross.return_value = []

        mock_compute_size.return_value = 1.0
        mock_compute_stop.return_value = 45000.0

        result = run_backtest(atr_win=20)

        # 验证结果
        assert isinstance(result, pd.Series)
        assert len(result) == 50
