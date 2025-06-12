#!/usr/bin/env python3
"""
缓存优化策略测试模块
测试 src.strategies.cache_optimized_strategy 模块的所有功能
"""

from unittest.mock import MagicMock, patch

import numpy as np

from src.strategies.cache_optimized_strategy import CacheOptimizedStrategy


class TestCacheOptimizedStrategy:
    """测试CacheOptimizedStrategy类"""

    def setup_method(self):
        """测试前准备"""
        self.config = {
            "name": "test_cache_strategy",
            "max_window_size": 100,
            "enable_logging": False,
        }
        self.strategy = CacheOptimizedStrategy(self.config)

    def test_init(self):
        """测试初始化"""
        assert self.strategy.symbol_pools == {}
        assert self.strategy.max_window_size == 200  # 默认值
        assert "calculations" in self.strategy.stats
        assert "array_reuses" in self.strategy.stats
        assert "memory_saves" in self.strategy.stats
        assert "gc_collections" in self.strategy.stats

    def test_init_with_gc_freeze_available(self):
        """测试在gc.freeze可用时的初始化"""
        with patch("gc.freeze") as mock_freeze, patch("gc.set_threshold") as mock_threshold:
            CacheOptimizedStrategy(self.config)
            # 验证GC优化被调用
            mock_freeze.assert_called_once()
            mock_threshold.assert_called_once_with(900, 15, 12)

    def test_init_with_gc_freeze_unavailable(self):
        """测试在gc.freeze不可用时的初始化"""
        with patch("gc.freeze", side_effect=AttributeError("freeze not available")):
            # 应该不抛出异常
            strategy = CacheOptimizedStrategy(self.config)
            assert strategy is not None

    def test_get_symbol_pool_new_symbol(self):
        """测试获取新symbol的池"""
        symbol = "AAPL"
        pool = self.strategy.get_symbol_pool(symbol)

        # 检查池结构
        assert symbol in self.strategy.symbol_pools
        assert "window_data" in pool
        assert "idx" in pool
        assert "count" in pool
        assert "ma_buffer_20" in pool
        assert "ma_buffer_50" in pool
        assert "atr_buffer_high" in pool
        assert "atr_buffer_low" in pool
        assert "atr_buffer_close" in pool
        assert "tr_buffer" in pool
        assert "last_ma_20" in pool
        assert "last_ma_50" in pool
        assert "last_atr" in pool
        assert "last_price" in pool

        # 检查数组形状
        assert pool["window_data"].shape == (200, 5)
        assert pool["ma_buffer_20"].shape == (20,)
        assert pool["ma_buffer_50"].shape == (50,)
        assert pool["atr_buffer_high"].shape == (15,)
        assert pool["tr_buffer"].shape == (14,)

        # 检查初始值
        assert pool["idx"] == 0
        assert pool["count"] == 0
        assert pool["last_ma_20"] == 0.0

    def test_get_symbol_pool_existing_symbol(self):
        """测试获取已存在symbol的池"""
        symbol = "AAPL"

        # 第一次获取
        pool1 = self.strategy.get_symbol_pool(symbol)
        initial_reuses = self.strategy.stats["array_reuses"]

        # 第二次获取
        pool2 = self.strategy.get_symbol_pool(symbol)

        # 应该返回同一个池
        assert pool1 is pool2
        # 统计应该增加
        assert self.strategy.stats["array_reuses"] == initial_reuses + 1

    def test_push_price_data_basic(self):
        """测试基本的价格数据推送"""
        symbol = "AAPL"
        ohlcv_row = np.array([100.0, 105.0, 95.0, 102.0, 1000.0])

        initial_saves = self.strategy.stats["memory_saves"]
        self.strategy.push_price_data(symbol, ohlcv_row)

        pool = self.strategy.get_symbol_pool(symbol)

        # 检查数据被正确存储
        assert pool["idx"] == 1
        assert pool["count"] == 1
        np.testing.assert_array_equal(pool["window_data"][0], ohlcv_row)

        # 检查统计
        assert self.strategy.stats["memory_saves"] == initial_saves + 1

    def test_push_price_data_multiple(self):
        """测试多次价格数据推送"""
        symbol = "AAPL"

        # 推送多个价格数据
        for i in range(5):
            ohlcv_row = np.array([100.0 + i, 105.0 + i, 95.0 + i, 102.0 + i, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        pool = self.strategy.get_symbol_pool(symbol)

        # 检查索引和计数
        assert pool["idx"] == 5
        assert pool["count"] == 5

        # 检查最后一个数据
        expected_last = np.array([104.0, 109.0, 99.0, 106.0, 1000.0])
        np.testing.assert_array_equal(pool["window_data"][4], expected_last)

    def test_push_price_data_circular_buffer(self):
        """测试环形缓冲区功能"""
        symbol = "AAPL"
        max_size = self.strategy.max_window_size

        # 推送超过最大大小的数据
        for i in range(max_size + 10):
            ohlcv_row = np.array([100.0 + i, 105.0 + i, 95.0 + i, 102.0 + i, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        pool = self.strategy.get_symbol_pool(symbol)

        # 检查环形缓冲区行为
        assert pool["idx"] == max_size + 10
        assert pool["count"] == max_size  # 不应超过最大大小

        # 检查最新数据在正确位置
        expected_idx = (max_size + 10 - 1) % max_size
        expected_data = np.array(
            [
                100.0 + max_size + 9,
                105.0 + max_size + 9,
                95.0 + max_size + 9,
                102.0 + max_size + 9,
                1000.0,
            ]
        )
        np.testing.assert_array_equal(pool["window_data"][expected_idx], expected_data)

    def test_calculate_ma_inplace_insufficient_data(self):
        """测试数据不足时的移动平均计算"""
        symbol = "AAPL"

        # 只推送少量数据
        for i in range(5):
            ohlcv_row = np.array([100.0 + i, 105.0 + i, 95.0 + i, 102.0 + i, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        # 请求20期移动平均（数据不足）
        result = self.strategy.calculate_ma_inplace(symbol, 20)
        assert result == 0.0

    def test_calculate_ma_inplace_period_20(self):
        """测试20期移动平均计算"""
        symbol = "AAPL"

        # 推送足够的数据
        prices = []
        for i in range(25):
            price = 100.0 + i
            prices.append(price)
            ohlcv_row = np.array([price, price + 5, price - 5, price + 2, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        initial_calculations = self.strategy.stats["calculations"]
        result = self.strategy.calculate_ma_inplace(symbol, 20)

        # 检查结果合理性
        assert result > 0
        # 应该接近最近20个收盘价的平均值
        expected_prices = [p + 2 for p in prices[-20:]]  # 收盘价 = price + 2
        expected_ma = np.mean(expected_prices)
        assert abs(result - expected_ma) < 0.01

        # 检查统计
        assert self.strategy.stats["calculations"] == initial_calculations + 1

        # 检查缓存
        pool = self.strategy.get_symbol_pool(symbol)
        assert pool["last_ma_20"] == result

    def test_calculate_ma_inplace_period_50(self):
        """测试50期移动平均计算"""
        symbol = "AAPL"

        # 推送足够的数据
        for i in range(55):
            price = 100.0 + i
            ohlcv_row = np.array([price, price + 5, price - 5, price + 2, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        result = self.strategy.calculate_ma_inplace(symbol, 50)

        # 检查结果合理性
        assert result > 0

        # 检查缓存
        pool = self.strategy.get_symbol_pool(symbol)
        assert pool["last_ma_50"] == result

    def test_calculate_ma_inplace_custom_period(self):
        """测试自定义期间的移动平均计算"""
        symbol = "AAPL"

        # 推送足够的数据
        for i in range(35):
            price = 100.0 + i
            ohlcv_row = np.array([price, price + 5, price - 5, price + 2, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        result = self.strategy.calculate_ma_inplace(symbol, 30)

        # 检查结果合理性
        assert result > 0

    def test_calculate_ma_inplace_circular_buffer_continuous(self):
        """测试环形缓冲区连续区域的移动平均计算"""
        symbol = "AAPL"

        # 推送数据，但不超过缓冲区大小
        for i in range(50):
            price = 100.0 + i
            ohlcv_row = np.array([price, price + 5, price - 5, price + 2, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        result = self.strategy.calculate_ma_inplace(symbol, 20)
        assert result > 0

    def test_calculate_ma_inplace_circular_buffer_wrapped(self):
        """测试环形缓冲区跨界区域的移动平均计算"""
        symbol = "AAPL"
        max_size = self.strategy.max_window_size

        # 推送超过缓冲区大小的数据，触发跨界情况
        for i in range(max_size + 30):
            price = 100.0 + i
            ohlcv_row = np.array([price, price + 5, price - 5, price + 2, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        result = self.strategy.calculate_ma_inplace(symbol, 20)
        assert result > 0

    def test_calculate_atr_inplace_insufficient_data(self):
        """测试数据不足时的ATR计算"""
        symbol = "AAPL"

        # 只推送少量数据
        for i in range(10):
            price = 100.0 + i
            ohlcv_row = np.array([price, price + 5, price - 5, price + 2, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        # 请求14期ATR（数据不足，需要15个数据点）
        result = self.strategy.calculate_atr_inplace(symbol, 14)
        assert result == 0.0

    def test_calculate_atr_inplace_sufficient_data(self):
        """测试有足够数据时的ATR计算"""
        symbol = "AAPL"

        # 推送足够的数据
        for i in range(20):
            price = 100.0 + i
            high = price + 5 + (i % 3)  # 添加一些变化
            low = price - 5 - (i % 2)
            close = price + 2
            ohlcv_row = np.array([price, high, low, close, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        initial_calculations = self.strategy.stats["calculations"]
        result = self.strategy.calculate_atr_inplace(symbol, 14)

        # 检查结果合理性
        assert result > 0
        assert result < 50  # 应该在合理范围内

        # 检查统计
        assert self.strategy.stats["calculations"] == initial_calculations + 1

        # 检查缓存
        pool = self.strategy.get_symbol_pool(symbol)
        assert pool["last_atr"] == result

    def test_calculate_atr_inplace_custom_period(self):
        """测试自定义期间的ATR计算"""
        symbol = "AAPL"

        # 推送足够的数据
        for i in range(25):
            price = 100.0 + i
            high = price + 5
            low = price - 5
            close = price + 2
            ohlcv_row = np.array([price, high, low, close, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        result = self.strategy.calculate_atr_inplace(symbol, 10)
        assert result > 0

    @patch("src.monitoring.get_metrics_collector")
    def test_generate_signals_insufficient_data(self, mock_metrics):
        """测试数据不足时的信号生成"""
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__enter__ = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__exit__ = MagicMock()
        mock_metrics.return_value = mock_collector

        symbol = "AAPL"
        current_price = 100.0

        result = self.strategy.generate_signals(symbol, current_price)

        # 数据不足时应该返回hold
        assert result["action"] == "hold"
        assert result["confidence"] == 0.0

    @patch("src.monitoring.get_metrics_collector")
    def test_generate_signals_cached_result(self, mock_metrics):
        """测试缓存结果的信号生成"""
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__enter__ = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__exit__ = MagicMock()
        mock_metrics.return_value = mock_collector

        symbol = "AAPL"
        current_price = 100.0

        # 预设缓存数据
        pool = self.strategy.get_symbol_pool(symbol)
        pool["last_price"] = current_price
        pool["last_ma_20"] = 98.0
        pool["last_ma_50"] = 95.0
        pool["last_atr"] = 2.0

        result = self.strategy.generate_signals(symbol, current_price)

        # 应该返回缓存结果
        assert result["cached"] is True
        assert result["action"] == "hold"
        assert result["ma_short"] == 98.0
        assert result["ma_long"] == 95.0
        assert result["atr"] == 2.0

    @patch("src.monitoring.get_metrics_collector")
    def test_generate_signals_buy_signal(self, mock_metrics):
        """测试买入信号生成"""
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__enter__ = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__exit__ = MagicMock()
        mock_metrics.return_value = mock_collector

        symbol = "AAPL"

        # 推送数据创建买入条件（短期MA > 长期MA）
        for i in range(60):
            if i < 30:
                price = 100.0 + i * 0.1  # 缓慢上升
            else:
                price = 100.0 + i * 0.5  # 快速上升

            high = price + 2
            low = price - 2
            close = price + 1
            ohlcv_row = np.array([price, high, low, close, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        current_price = 130.0
        result = self.strategy.generate_signals(symbol, current_price)

        # 应该生成买入信号
        assert result["action"] == "buy"
        assert result["confidence"] > 0
        assert result["ma_short"] > result["ma_long"]
        assert result["cached"] is False

    @patch("src.monitoring.get_metrics_collector")
    def test_generate_signals_sell_signal(self, mock_metrics):
        """测试卖出信号生成"""
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__enter__ = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__exit__ = MagicMock()
        mock_metrics.return_value = mock_collector

        symbol = "AAPL"

        # 推送数据创建卖出条件（短期MA < 长期MA）
        for i in range(60):
            if i < 30:
                price = 130.0 - i * 0.1  # 缓慢下降
            else:
                price = 130.0 - i * 0.5  # 快速下降

            high = price + 2
            low = price - 2
            close = price + 1
            ohlcv_row = np.array([price, high, low, close, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        current_price = 100.0
        result = self.strategy.generate_signals(symbol, current_price)

        # 应该生成卖出信号
        assert result["action"] == "sell"
        assert result["confidence"] > 0
        assert result["ma_short"] < result["ma_long"]

    @patch("src.monitoring.get_metrics_collector")
    def test_generate_signals_hold_signal(self, mock_metrics):
        """测试持有信号生成"""
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__enter__ = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__exit__ = MagicMock()
        mock_metrics.return_value = mock_collector

        symbol = "AAPL"

        # 推送数据创建持有条件（MA差异很小）
        for i in range(60):
            price = 100.0 + (i % 5) * 0.1  # 小幅波动
            high = price + 1
            low = price - 1
            close = price + 0.5
            ohlcv_row = np.array([price, high, low, close, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        current_price = 102.0
        result = self.strategy.generate_signals(symbol, current_price)

        # 应该生成持有信号
        assert result["action"] == "hold"
        assert result["confidence"] == 0.0

    @patch("src.monitoring.get_metrics_collector")
    def test_generate_signals_gc_collection(self, mock_metrics):
        """测试GC收集触发"""
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__enter__ = MagicMock()
        mock_collector.monitor_memory_allocation.return_value.__exit__ = MagicMock()
        mock_metrics.return_value = mock_collector

        symbol = "AAPL"

        # 设置计算次数，考虑到会有4次计算增加（ma_short, ma_long, atr, generate_signals）
        # 497 + 4 = 501，不是500的倍数，所以设置为496
        self.strategy.stats["calculations"] = 496

        # 推送足够的数据
        for i in range(60):
            price = 100.0 + i
            ohlcv_row = np.array([price, price + 2, price - 2, price + 1, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        initial_gc_collections = self.strategy.stats["gc_collections"]

        with (
            patch("gc.collect") as mock_gc_collect,
            patch.object(self.strategy, "_log_stats") as mock_log_stats,
        ):

            self.strategy.generate_signals(symbol, 160.0)

            # 应该触发GC收集（496 + 4 = 500）
            mock_gc_collect.assert_called_once()
            mock_log_stats.assert_called_once()
            assert self.strategy.stats["gc_collections"] == initial_gc_collections + 1

    def test_generate_signals_exception_handling(self):
        """测试信号生成的异常处理"""
        symbol = "AAPL"
        current_price = 100.0

        # 使用无效的symbol名称或其他方式触发异常处理路径
        # 这里我们测试一个边界情况：没有足够数据时的处理
        result = self.strategy.generate_signals(symbol, current_price)

        # 数据不足时应该返回hold信号
        assert result["action"] == "hold"
        assert result["confidence"] == 0.0

    def test_log_stats(self):
        """测试统计日志记录"""
        with patch.object(self.strategy, "logger") as mock_logger:
            self.strategy.stats["calculations"] = 100
            self.strategy.stats["array_reuses"] = 50
            self.strategy.stats["memory_saves"] = 200
            self.strategy.stats["gc_collections"] = 5

            self.strategy._log_stats()

            # 验证日志被调用
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "计算次数: 100" in call_args
            assert "数组复用: 50" in call_args
            assert "内存节省: 200" in call_args
            assert "GC次数: 5" in call_args

    def test_get_cache_info(self):
        """测试缓存信息获取"""
        # 添加一些测试数据
        self.strategy.get_symbol_pool("AAPL")
        self.strategy.get_symbol_pool("GOOGL")
        self.strategy.stats["calculations"] = 100
        self.strategy.stats["array_reuses"] = 50

        info = self.strategy.get_cache_info()

        assert info["strategy_type"] == "zero_allocation"
        assert info["symbol_pools"] == 2
        assert info["total_calculations"] == 100
        assert info["array_reuses"] == 50
        assert info["memory_saves"] == 0
        assert info["gc_collections"] == 0

    def test_clear_caches(self):
        """测试缓存清理"""
        # 添加一些测试数据
        self.strategy.get_symbol_pool("AAPL")
        self.strategy.get_symbol_pool("GOOGL")
        self.strategy.stats["calculations"] = 100

        with (
            patch("gc.collect") as mock_gc_collect,
            patch.object(self.strategy, "logger") as mock_logger,
        ):

            self.strategy.clear_caches()

            # 验证清理效果
            assert len(self.strategy.symbol_pools) == 0
            assert self.strategy.stats["calculations"] == 0

            # 验证GC被调用
            mock_gc_collect.assert_called_once()
            mock_logger.info.assert_called_once()

    def test_memory_optimization_report(self):
        """测试内存优化报告"""
        # 设置一些测试数据
        self.strategy.stats["calculations"] = 1000
        self.strategy.stats["array_reuses"] = 500
        self.strategy.stats["memory_saves"] = 800
        self.strategy.stats["gc_collections"] = 10

        report = self.strategy.memory_optimization_report()

        # 检查报告结构
        assert "cache_info" in report
        assert "performance_savings" in report
        assert "memory_efficiency" in report
        assert "optimization_status" in report

        # 检查性能节省
        perf = report["performance_savings"]
        assert perf["total_calculations"] == 1000
        assert perf["array_reuses"] == 500
        assert perf["memory_saves"] == 800
        assert perf["estimated_allocations_avoided"] == 4000  # 800 * 5
        assert perf["gc_efficiency"] == 10

        # 检查内存效率
        efficiency = report["memory_efficiency"]
        assert efficiency["ma_cache_hit_rate"] == 1.0
        assert efficiency["atr_cache_hit_rate"] == 1.0
        assert efficiency["window_reuse_efficiency"] == 0.5  # 500/1000
        assert efficiency["memory_save_ratio"] == 1.0

        # 检查优化状态
        status = report["optimization_status"]
        assert status["zero_allocation"] is True
        assert status["inplace_operations"] is True
        assert status["gc_optimized"] is True
        assert status["numpy_only"] is True


class TestEdgeCases:
    """测试边界情况"""

    def setup_method(self):
        """测试前准备"""
        self.config = {"name": "test_strategy"}
        self.strategy = CacheOptimizedStrategy(self.config)

    def test_zero_price_data(self):
        """测试零价格数据"""
        symbol = "AAPL"
        ohlcv_row = np.array([0.0, 0.0, 0.0, 0.0, 0.0])

        self.strategy.push_price_data(symbol, ohlcv_row)

        # 应该能正常处理
        pool = self.strategy.get_symbol_pool(symbol)
        assert pool["count"] == 1

    def test_negative_price_data(self):
        """测试负价格数据"""
        symbol = "AAPL"
        ohlcv_row = np.array([-100.0, -95.0, -105.0, -98.0, 1000.0])

        self.strategy.push_price_data(symbol, ohlcv_row)

        # 应该能正常处理
        pool = self.strategy.get_symbol_pool(symbol)
        assert pool["count"] == 1

    def test_very_large_price_data(self):
        """测试非常大的价格数据"""
        symbol = "AAPL"
        ohlcv_row = np.array([1e6, 1.1e6, 0.9e6, 1.05e6, 1e9])

        self.strategy.push_price_data(symbol, ohlcv_row)

        # 应该能正常处理
        pool = self.strategy.get_symbol_pool(symbol)
        assert pool["count"] == 1

    def test_nan_price_data(self):
        """测试NaN价格数据"""
        symbol = "AAPL"
        ohlcv_row = np.array([np.nan, 105.0, 95.0, 102.0, 1000.0])

        self.strategy.push_price_data(symbol, ohlcv_row)

        # 应该能正常处理
        pool = self.strategy.get_symbol_pool(symbol)
        assert pool["count"] == 1

    def test_inf_price_data(self):
        """测试无穷大价格数据"""
        symbol = "AAPL"
        ohlcv_row = np.array([np.inf, 105.0, 95.0, 102.0, 1000.0])

        self.strategy.push_price_data(symbol, ohlcv_row)

        # 应该能正常处理
        pool = self.strategy.get_symbol_pool(symbol)
        assert pool["count"] == 1

    def test_multiple_symbols_isolation(self):
        """测试多个symbol的隔离性"""
        symbols = ["AAPL", "GOOGL", "MSFT"]

        # 为每个symbol推送不同的数据
        for i, symbol in enumerate(symbols):
            for j in range(10):
                price = 100.0 + i * 50 + j
                ohlcv_row = np.array([price, price + 5, price - 5, price + 2, 1000.0])
                self.strategy.push_price_data(symbol, ohlcv_row)

        # 验证每个symbol的数据是独立的
        for i, symbol in enumerate(symbols):
            pool = self.strategy.get_symbol_pool(symbol)
            assert pool["count"] == 10

            # 检查最后一个价格
            last_idx = (pool["idx"] - 1) % self.strategy.max_window_size
            expected_price = 100.0 + i * 50 + 9 + 2  # 收盘价
            assert abs(pool["window_data"][last_idx, 3] - expected_price) < 0.01

    def test_memory_efficiency_with_large_dataset(self):
        """测试大数据集的内存效率"""
        symbol = "AAPL"

        # 推送大量数据
        for i in range(1000):
            price = 100.0 + i * 0.1
            ohlcv_row = np.array([price, price + 5, price - 5, price + 2, 1000.0])
            self.strategy.push_price_data(symbol, ohlcv_row)

        pool = self.strategy.get_symbol_pool(symbol)

        # 验证环形缓冲区正常工作
        assert pool["count"] == self.strategy.max_window_size
        assert pool["idx"] == 1000

        # 验证内存使用效率
        assert self.strategy.stats["memory_saves"] == 1000
