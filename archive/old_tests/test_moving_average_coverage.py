#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动平均线指标测试模块
Moving Average Indicators Test Module

专门针对 src/indicators/moving_average.py 的全面测试覆盖
"""

import unittest
import numpy as np
import pandas as pd
from src.indicators.moving_average import (
    simple_moving_average,
    exponential_moving_average,
    weighted_moving_average,
    moving_average,
)


class TestSimpleMovingAverage(unittest.TestCase):
    """测试简单移动平均线 (Test Simple Moving Average)"""

    def setUp(self):
        """设置测试数据"""
        self.test_data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.price_data = pd.Series([100, 102, 98, 105, 103, 107, 109, 106, 108, 110])

    def test_simple_moving_average_basic(self):
        """测试基本SMA计算"""
        result = simple_moving_average(self.test_data, window=3)

        # 验证结果类型
        self.assertIsInstance(result, pd.Series)

        # 验证长度
        self.assertEqual(len(result), len(self.test_data))

        # 验证具体值
        expected_last_value = (8 + 9 + 10) / 3  # 最后3个数的平均
        self.assertAlmostEqual(result.iloc[-1], expected_last_value, places=6)

    def test_simple_moving_average_window_1(self):
        """测试窗口为1的SMA"""
        result = simple_moving_average(self.test_data, window=1)

        # 窗口为1时，SMA应该等于原数据
        pd.testing.assert_series_equal(result, self.test_data, check_dtype=False)

    def test_simple_moving_average_large_window(self):
        """测试大窗口SMA"""
        result = simple_moving_average(self.test_data, window=len(self.test_data))

        # 大窗口时，最后的值应该是所有数据的平均
        expected_final = self.test_data.mean()
        self.assertAlmostEqual(result.iloc[-1], expected_final, places=6)

    def test_simple_moving_average_invalid_window(self):
        """测试无效窗口参数"""
        with self.assertRaises(ValueError):
            simple_moving_average(self.test_data, window=0)

        with self.assertRaises(ValueError):
            simple_moving_average(self.test_data, window=-1)

    def test_simple_moving_average_with_nan(self):
        """测试包含NaN的数据"""
        data_with_nan = pd.Series([1, 2, np.nan, 4, 5])
        result = simple_moving_average(data_with_nan, window=3)

        # 验证结果不全是NaN
        self.assertFalse(result.isna().all())


class TestExponentialMovingAverage(unittest.TestCase):
    """测试指数移动平均线 (Test Exponential Moving Average)"""

    def setUp(self):
        """设置测试数据"""
        self.test_data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.price_data = pd.Series([100, 102, 98, 105, 103, 107, 109, 106, 108, 110])

    def test_exponential_moving_average_basic(self):
        """测试基本EMA计算"""
        result = exponential_moving_average(self.test_data, window=5)

        # 验证结果类型
        self.assertIsInstance(result, pd.Series)

        # 验证长度
        self.assertEqual(len(result), len(self.test_data))

        # EMA的最后值应该大于前面的值（递增数据）
        self.assertGreater(result.iloc[-1], result.iloc[-2])

    def test_exponential_moving_average_with_alpha(self):
        """测试指定alpha的EMA"""
        alpha = 0.3
        result = exponential_moving_average(self.test_data, window=5, alpha=alpha)

        # 验证结果
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.test_data))

    def test_exponential_moving_average_invalid_window(self):
        """测试无效窗口参数"""
        with self.assertRaises(ValueError):
            exponential_moving_average(self.test_data, window=0)

        with self.assertRaises(ValueError):
            exponential_moving_average(self.test_data, window=-1)

    def test_exponential_moving_average_invalid_alpha(self):
        """测试无效alpha参数"""
        with self.assertRaises(ValueError):
            exponential_moving_average(self.test_data, window=5, alpha=0)

        with self.assertRaises(ValueError):
            exponential_moving_average(self.test_data, window=5, alpha=1.5)

        with self.assertRaises(ValueError):
            exponential_moving_average(self.test_data, window=5, alpha=-0.1)

    def test_exponential_moving_average_alpha_boundary(self):
        """测试alpha边界值"""
        # alpha = 1 应该有效
        result = exponential_moving_average(self.test_data, window=5, alpha=1.0)
        self.assertIsInstance(result, pd.Series)

        # alpha接近0但大于0应该有效
        result = exponential_moving_average(self.test_data, window=5, alpha=0.0001)
        self.assertIsInstance(result, pd.Series)

    def test_exponential_moving_average_default_alpha(self):
        """测试默认alpha计算"""
        window = 5
        result1 = exponential_moving_average(self.test_data, window=window)

        # 手动计算默认alpha
        default_alpha = 2.0 / (window + 1)
        result2 = exponential_moving_average(self.test_data, window=window, alpha=default_alpha)

        # 两个结果应该相等
        pd.testing.assert_series_equal(result1, result2)


class TestWeightedMovingAverage(unittest.TestCase):
    """测试加权移动平均线 (Test Weighted Moving Average)"""

    def setUp(self):
        """设置测试数据"""
        self.test_data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.simple_data = pd.Series([1, 2, 3, 4, 5])

    def test_weighted_moving_average_basic(self):
        """测试基本WMA计算"""
        result = weighted_moving_average(self.test_data, window=3)

        # 验证结果类型
        self.assertIsInstance(result, pd.Series)

        # 验证长度
        self.assertEqual(len(result), len(self.test_data))

        # 验证WMA给最近数据更高权重
        # 对于递增数据，WMA应该大于SMA
        sma_result = simple_moving_average(self.test_data, window=3)
        self.assertGreater(result.iloc[-1], sma_result.iloc[-1])

    def test_weighted_moving_average_window_1(self):
        """测试窗口为1的WMA"""
        result = weighted_moving_average(self.test_data, window=1)

        # 窗口为1时，WMA应该等于原数据
        pd.testing.assert_series_equal(result, self.test_data, check_dtype=False)

    def test_weighted_moving_average_manual_calculation(self):
        """测试手动计算验证"""
        data = pd.Series([1, 2, 3])
        result = weighted_moving_average(data, window=3)

        # 手动计算最后一个值: (1*1 + 2*2 + 3*3) / (1+2+3) = 14/6
        expected_last = (1 * 1 + 2 * 2 + 3 * 3) / (1 + 2 + 3)
        self.assertAlmostEqual(result.iloc[-1], expected_last, places=6)

    def test_weighted_moving_average_invalid_window(self):
        """测试无效窗口参数"""
        with self.assertRaises(ValueError):
            weighted_moving_average(self.test_data, window=0)

        with self.assertRaises(ValueError):
            weighted_moving_average(self.test_data, window=-1)

    def test_weighted_moving_average_insufficient_data(self):
        """测试数据不足的情况"""
        short_data = pd.Series([1, 2])
        result = weighted_moving_average(short_data, window=5)

        # 应该能处理数据不足的情况
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(short_data))


class TestMovingAverageCompatibility(unittest.TestCase):
    """测试兼容性函数 (Test Compatibility Function)"""

    def setUp(self):
        """设置测试数据"""
        self.test_data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    def test_moving_average_compatibility(self):
        """测试兼容性函数"""
        result1 = moving_average(self.test_data, window=5)
        result2 = simple_moving_average(self.test_data, window=5)

        # 兼容性函数应该与SMA相同
        pd.testing.assert_series_equal(result1, result2)

    def test_moving_average_all_parameters(self):
        """测试兼容性函数的所有参数"""
        windows_to_test = [1, 3, 5, 10]

        for window in windows_to_test:
            with self.subTest(window=window):
                result1 = moving_average(self.test_data, window=window)
                result2 = simple_moving_average(self.test_data, window=window)
                pd.testing.assert_series_equal(result1, result2)


class TestMovingAverageIntegration(unittest.TestCase):
    """移动平均线集成测试 (Moving Average Integration Tests)"""

    def setUp(self):
        """设置测试数据"""
        # 创建更真实的价格数据
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        self.price_series = pd.Series(prices, index=dates)

    def test_all_moving_averages_comparison(self):
        """测试所有移动平均线的比较"""
        window = 10

        sma = simple_moving_average(self.price_series, window)
        ema = exponential_moving_average(self.price_series, window)
        wma = weighted_moving_average(self.price_series, window)

        # 所有结果应该有相同的长度
        self.assertEqual(len(sma), len(ema))
        self.assertEqual(len(ema), len(wma))

        # 对于趋势数据，EMA和WMA应该更接近当前价格
        current_price = self.price_series.iloc[-1]
        sma_last = sma.iloc[-1]
        ema_last = ema.iloc[-1]
        wma_last = wma.iloc[-1]

        # 验证所有移动平均线都是合理的数值
        self.assertFalse(np.isnan(sma_last))
        self.assertFalse(np.isnan(ema_last))
        self.assertFalse(np.isnan(wma_last))

    def test_moving_averages_with_different_windows(self):
        """测试不同窗口的移动平均线"""
        windows = [5, 10, 20, 50]

        for window in windows:
            with self.subTest(window=window):
                if window <= len(self.price_series):
                    sma = simple_moving_average(self.price_series, window)
                    ema = exponential_moving_average(self.price_series, window)
                    wma = weighted_moving_average(self.price_series, window)

                    # 验证结果
                    self.assertEqual(len(sma), len(self.price_series))
                    self.assertEqual(len(ema), len(self.price_series))
                    self.assertEqual(len(wma), len(self.price_series))

    def test_moving_averages_edge_cases(self):
        """测试边界情况"""
        # 单个数据点
        single_point = pd.Series([100])

        sma = simple_moving_average(single_point, 1)
        ema = exponential_moving_average(single_point, 1)
        wma = weighted_moving_average(single_point, 1)

        # 所有结果应该等于原始值
        self.assertEqual(sma.iloc[0], 100)
        self.assertEqual(ema.iloc[0], 100)
        self.assertEqual(wma.iloc[0], 100)

    def test_moving_averages_with_constant_data(self):
        """测试常数数据"""
        constant_data = pd.Series([50] * 20)

        sma = simple_moving_average(constant_data, 5)
        ema = exponential_moving_average(constant_data, 5)
        wma = weighted_moving_average(constant_data, 5)

        # 对于常数数据，所有移动平均线应该等于常数值
        self.assertTrue(np.allclose(sma.dropna(), 50))
        self.assertTrue(np.allclose(ema.dropna(), 50))
        self.assertTrue(np.allclose(wma.dropna(), 50))


if __name__ == "__main__":
    unittest.main()
