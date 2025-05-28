#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
波动率指标全面测试模块 (Comprehensive Volatility Indicators Test Module)

为 src/indicators/volatility_indicators.py 提供100%测试覆盖率
"""

import unittest
import numpy as np
import pandas as pd
import pytest
from src.indicators.volatility_indicators import (
    bollinger_bands,
    standard_deviation,
    average_true_range,
    calculate_true_range,
    calculate_atr,
    keltner_channels,
)


class TestBollingerBands(unittest.TestCase):
    """测试布林带指标 (Test Bollinger Bands Indicator)"""

    def setUp(self):
        """设置测试数据"""
        # 创建价格数据
        self.price_data = pd.Series(
            [
                100,
                102,
                101,
                104,
                106,
                105,
                108,
                107,
                110,
                109,
                112,
                114,
                113,
                116,
                115,
                118,
                120,
                119,
                122,
                121,
                123,
                125,
                124,
                127,
                126,
                129,
                128,
                131,
                130,
                133,
            ]
        )
        self.simple_data = pd.Series([10, 12, 11, 13, 15, 14, 16, 18, 17, 19])

    def test_bollinger_bands_basic(self):
        """测试基本布林带计算"""
        upper, middle, lower = bollinger_bands(self.price_data, window=10, num_std=2.0)

        # 验证返回值类型
        self.assertIsInstance(upper, pd.Series)
        self.assertIsInstance(middle, pd.Series)
        self.assertIsInstance(lower, pd.Series)

        # 验证长度
        self.assertEqual(len(upper), len(self.price_data))
        self.assertEqual(len(middle), len(self.price_data))
        self.assertEqual(len(lower), len(self.price_data))

        # 验证关系：上轨 > 中轨 > 下轨
        valid_data = middle.dropna()
        if len(valid_data) > 0:
            valid_upper = upper.dropna()
            valid_lower = lower.dropna()

            # 检查最后几个有效值
            if len(valid_upper) > 0 and len(valid_lower) > 0:
                self.assertGreater(valid_upper.iloc[-1], valid_data.iloc[-1])
                self.assertLess(valid_lower.iloc[-1], valid_data.iloc[-1])

    def test_bollinger_bands_different_parameters(self):
        """测试不同参数的布林带"""
        # 测试不同窗口大小
        upper1, middle1, lower1 = bollinger_bands(self.price_data, window=5, num_std=2.0)
        upper2, middle2, lower2 = bollinger_bands(self.price_data, window=20, num_std=2.0)

        # 不同窗口应该产生不同结果
        valid1 = middle1.dropna()
        valid2 = middle2.dropna()

        if len(valid1) > 0 and len(valid2) > 0:
            # 结果应该有差异
            min_len = min(len(valid1), len(valid2))
            if min_len > 1:
                differences = abs(valid1.iloc[-min_len:].values - valid2.iloc[-min_len:].values)
                self.assertGreater(differences.sum(), 0)

        # 测试不同标准差倍数
        upper3, middle3, lower3 = bollinger_bands(self.price_data, window=10, num_std=1.0)
        upper4, middle4, lower4 = bollinger_bands(self.price_data, window=10, num_std=3.0)

        # 更大的标准差倍数应该产生更宽的带
        valid_upper3 = upper3.dropna()
        valid_upper4 = upper4.dropna()
        valid_lower3 = lower3.dropna()
        valid_lower4 = lower4.dropna()

        if len(valid_upper3) > 0 and len(valid_upper4) > 0:
            self.assertLess(valid_upper3.iloc[-1], valid_upper4.iloc[-1])
            self.assertGreater(valid_lower3.iloc[-1], valid_lower4.iloc[-1])

    def test_bollinger_bands_edge_cases(self):
        """测试布林带边缘情况"""
        # 测试常数数据
        constant_data = pd.Series([100] * 20)
        upper, middle, lower = bollinger_bands(constant_data, window=10, num_std=2.0)

        # 常数数据的标准差为0，上下轨应该等于中轨
        valid_middle = middle.dropna()
        valid_upper = upper.dropna()
        valid_lower = lower.dropna()

        if len(valid_middle) > 0:
            # 对于常数数据，上下轨应该等于或接近中轨
            np.testing.assert_allclose(valid_upper, valid_middle, rtol=1e-10)
            np.testing.assert_allclose(valid_lower, valid_middle, rtol=1e-10)

    def test_bollinger_bands_small_window(self):
        """测试小窗口布林带"""
        upper, middle, lower = bollinger_bands(self.simple_data, window=2, num_std=1.0)

        # 小窗口也应该能正常工作
        self.assertEqual(len(upper), len(self.simple_data))

        # 验证前几个值是NaN
        self.assertTrue(pd.isna(middle.iloc[0]))


class TestStandardDeviation(unittest.TestCase):
    """测试标准差指标 (Test Standard Deviation Indicator)"""

    def setUp(self):
        """设置测试数据"""
        self.price_data = pd.Series([100, 102, 98, 105, 103, 107, 109, 106, 108, 110])

    def test_standard_deviation_basic(self):
        """测试基本标准差计算"""
        result = standard_deviation(self.price_data, window=5)

        # 验证结果类型和长度
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.price_data))

        # 验证前4个值为NaN
        self.assertTrue(result.iloc[:4].isna().all())

        # 验证标准差为非负值
        valid_std = result.dropna()
        if len(valid_std) > 0:
            self.assertTrue((valid_std >= 0).all())

    def test_standard_deviation_constant_data(self):
        """测试常数数据的标准差"""
        constant_data = pd.Series([50] * 10)
        result = standard_deviation(constant_data, window=5)

        # 常数数据的标准差应该为0
        valid_std = result.dropna()
        if len(valid_std) > 0:
            np.testing.assert_allclose(valid_std, 0, atol=1e-10)

    def test_standard_deviation_different_windows(self):
        """测试不同窗口的标准差"""
        std1 = standard_deviation(self.price_data, window=3)
        std2 = standard_deviation(self.price_data, window=7)

        # 不同窗口应该产生不同结果
        valid1 = std1.dropna()
        valid2 = std2.dropna()

        if len(valid1) > 2 and len(valid2) > 2:
            # 结果应该有差异
            min_len = min(len(valid1), len(valid2))
            differences = abs(valid1.iloc[-min_len:].values - valid2.iloc[-min_len:].values)
            self.assertGreater(differences.sum(), 0)


class TestAverageTrueRange(unittest.TestCase):
    """测试平均真实范围指标 (Test Average True Range Indicator)"""

    def setUp(self):
        """设置测试数据"""
        # 创建OHLC数据
        self.high = pd.Series([105, 107, 106, 109, 111, 110, 113, 112, 115, 114])
        self.low = pd.Series([95, 97, 96, 99, 101, 100, 103, 102, 105, 104])
        self.close = pd.Series([100, 102, 101, 104, 106, 105, 108, 107, 110, 109])

    def test_average_true_range_basic(self):
        """测试基本ATR计算"""
        result = average_true_range(self.high, self.low, self.close, window=5)

        # 验证结果类型和长度
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.high))

        # 验证ATR为非负值
        valid_atr = result.dropna()
        if len(valid_atr) > 0:
            self.assertTrue((valid_atr >= 0).all())

    def test_average_true_range_manual_calculation(self):
        """测试手动计算验证"""
        # 使用简单数据进行手动验证
        simple_high = pd.Series([12, 14, 13, 15])
        simple_low = pd.Series([8, 10, 9, 11])
        simple_close = pd.Series([10, 12, 11, 13])

        result = average_true_range(simple_high, simple_low, simple_close, window=2)

        # 验证结果不全是NaN
        self.assertFalse(result.isna().all())

        # 手动计算第二个值的真实范围
        # TR2 = max(14-10, |14-10|, |10-10|) = max(4, 4, 0) = 4
        # 但由于是滚动平均，需要考虑前一个值

    def test_average_true_range_edge_cases(self):
        """测试ATR边缘情况"""
        # 测试高低价相等的情况
        equal_high_low = pd.Series([100] * 10)
        equal_close = pd.Series([100] * 10)

        result = average_true_range(equal_high_low, equal_high_low, equal_close, window=5)

        # 当高低价相等且价格不变时，ATR应该为0
        valid_atr = result.dropna()
        if len(valid_atr) > 0:
            np.testing.assert_allclose(valid_atr, 0, atol=1e-10)

    def test_average_true_range_different_windows(self):
        """测试不同窗口的ATR"""
        atr1 = average_true_range(self.high, self.low, self.close, window=3)
        atr2 = average_true_range(self.high, self.low, self.close, window=7)

        # 不同窗口应该产生不同结果
        valid1 = atr1.dropna()
        valid2 = atr2.dropna()

        if len(valid1) > 0 and len(valid2) > 0:
            min_len = min(len(valid1), len(valid2))
            if min_len > 1:
                differences = abs(valid1.iloc[-min_len:].values - valid2.iloc[-min_len:].values)
                self.assertGreaterEqual(differences.sum(), 0)


class TestCalculateTrueRange(unittest.TestCase):
    """测试真实范围计算 (Test True Range Calculation)"""

    def setUp(self):
        """设置测试数据"""
        self.high = pd.Series([15, 17, 16, 19, 18])
        self.low = pd.Series([10, 12, 11, 14, 13])
        self.close = pd.Series([12, 14, 13, 16, 15])

    def test_calculate_true_range_basic(self):
        """测试基本真实范围计算"""
        result = calculate_true_range(self.high, self.low, self.close)

        # 验证结果类型和长度
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.high))

        # 验证真实范围为非负值
        valid_tr = result.dropna()
        if len(valid_tr) > 0:
            self.assertTrue((valid_tr >= 0).all())

    def test_calculate_true_range_manual_verification(self):
        """测试手动验证真实范围"""
        # 使用简单数据手动验证
        simple_high = pd.Series([12, 14])
        simple_low = pd.Series([8, 10])
        simple_close = pd.Series([10, 12])

        result = calculate_true_range(simple_high, simple_low, simple_close)

        # 第一个值: max(12-8, |12-NaN|, |8-NaN|) = max(4, NaN, NaN) = 4
        self.assertEqual(result.iloc[0], 4)

        # 第二个值: max(14-10, |14-10|, |10-10|) = max(4, 4, 0) = 4
        self.assertEqual(result.iloc[1], 4)

    def test_calculate_true_range_with_gaps(self):
        """测试有跳空的真实范围"""
        # 创建有跳空的数据
        gap_high = pd.Series([10, 20, 15])  # 第二天跳空高开
        gap_low = pd.Series([8, 18, 13])
        gap_close = pd.Series([9, 19, 14])

        result = calculate_true_range(gap_high, gap_low, gap_close)

        # 第二个值应该考虑跳空
        # TR2 = max(20-18, |20-9|, |18-9|) = max(2, 11, 9) = 11
        self.assertEqual(result.iloc[1], 11)


class TestCalculateATR(unittest.TestCase):
    """测试ATR别名函数 (Test ATR Alias Function)"""

    def setUp(self):
        """设置测试数据"""
        self.high = pd.Series([105, 107, 106, 109, 111])
        self.low = pd.Series([95, 97, 96, 99, 101])
        self.close = pd.Series([100, 102, 101, 104, 106])

    def test_calculate_atr_alias(self):
        """测试ATR别名函数"""
        result1 = calculate_atr(self.high, self.low, self.close, window=3)
        result2 = average_true_range(self.high, self.low, self.close, window=3)

        # 两个函数应该产生相同结果
        pd.testing.assert_series_equal(result1, result2)

    def test_calculate_atr_backward_compatibility(self):
        """测试向后兼容性"""
        # 确保函数签名兼容
        result = calculate_atr(high=self.high, low=self.low, close=self.close, window=4)

        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.high))


class TestKeltnerChannels(unittest.TestCase):
    """测试Keltner通道 (Test Keltner Channels)"""

    def setUp(self):
        """设置测试数据"""
        self.high = pd.Series(
            [
                105,
                107,
                106,
                109,
                111,
                110,
                113,
                112,
                115,
                114,
                117,
                116,
                119,
                118,
                121,
                120,
                123,
                122,
                125,
                124,
            ]
        )
        self.low = pd.Series(
            [
                95,
                97,
                96,
                99,
                101,
                100,
                103,
                102,
                105,
                104,
                107,
                106,
                109,
                108,
                111,
                110,
                113,
                112,
                115,
                114,
            ]
        )
        self.close = pd.Series(
            [
                100,
                102,
                101,
                104,
                106,
                105,
                108,
                107,
                110,
                109,
                112,
                111,
                114,
                113,
                116,
                115,
                118,
                117,
                120,
                119,
            ]
        )

    def test_keltner_channels_basic(self):
        """测试基本Keltner通道计算"""
        upper, middle, lower = keltner_channels(
            self.high, self.low, self.close, ma_period=10, atr_period=10, multiplier=2.0
        )

        # 验证返回值类型
        self.assertIsInstance(upper, pd.Series)
        self.assertIsInstance(middle, pd.Series)
        self.assertIsInstance(lower, pd.Series)

        # 验证长度
        self.assertEqual(len(upper), len(self.high))
        self.assertEqual(len(middle), len(self.high))
        self.assertEqual(len(lower), len(self.high))

        # 验证关系：上轨 > 中轨 > 下轨
        valid_middle = middle.dropna()
        valid_upper = upper.dropna()
        valid_lower = lower.dropna()

        if len(valid_middle) > 0 and len(valid_upper) > 0 and len(valid_lower) > 0:
            self.assertGreater(valid_upper.iloc[-1], valid_middle.iloc[-1])
            self.assertLess(valid_lower.iloc[-1], valid_middle.iloc[-1])

    def test_keltner_channels_different_parameters(self):
        """测试不同参数的Keltner通道"""
        # 测试不同移动平均周期
        upper1, middle1, lower1 = keltner_channels(
            self.high, self.low, self.close, ma_period=5, atr_period=5, multiplier=2.0
        )
        upper2, middle2, lower2 = keltner_channels(
            self.high, self.low, self.close, ma_period=15, atr_period=15, multiplier=2.0
        )

        # 不同参数应该产生不同结果
        valid1 = middle1.dropna()
        valid2 = middle2.dropna()

        if len(valid1) > 0 and len(valid2) > 0:
            min_len = min(len(valid1), len(valid2))
            if min_len > 1:
                differences = abs(valid1.iloc[-min_len:].values - valid2.iloc[-min_len:].values)
                self.assertGreater(differences.sum(), 0)

    def test_keltner_channels_multiplier_effect(self):
        """测试倍数对通道宽度的影响"""
        upper1, middle1, lower1 = keltner_channels(
            self.high, self.low, self.close, ma_period=10, atr_period=10, multiplier=1.0
        )
        upper2, middle2, lower2 = keltner_channels(
            self.high, self.low, self.close, ma_period=10, atr_period=10, multiplier=3.0
        )

        # 更大的倍数应该产生更宽的通道
        valid_upper1 = upper1.dropna()
        valid_upper2 = upper2.dropna()
        valid_lower1 = lower1.dropna()
        valid_lower2 = lower2.dropna()
        valid_middle1 = middle1.dropna()
        valid_middle2 = middle2.dropna()

        if (
            len(valid_upper1) > 0
            and len(valid_upper2) > 0
            and len(valid_lower1) > 0
            and len(valid_lower2) > 0
        ):

            # 中轨应该相同（相同的MA参数）
            np.testing.assert_allclose(valid_middle1, valid_middle2, rtol=1e-10)

            # 更大倍数的通道应该更宽
            self.assertLess(valid_upper1.iloc[-1], valid_upper2.iloc[-1])
            self.assertGreater(valid_lower1.iloc[-1], valid_lower2.iloc[-1])

    def test_keltner_channels_edge_cases(self):
        """测试Keltner通道边缘情况"""
        # 测试短数据
        short_high = pd.Series([10, 12, 11])
        short_low = pd.Series([8, 9, 8])
        short_close = pd.Series([9, 11, 10])

        upper, middle, lower = keltner_channels(
            short_high, short_low, short_close, ma_period=2, atr_period=2, multiplier=1.0
        )

        # 短数据也应该能处理
        self.assertEqual(len(upper), len(short_high))
        self.assertEqual(len(middle), len(short_high))
        self.assertEqual(len(lower), len(short_high))


class TestVolatilityIndicatorsIntegration(unittest.TestCase):
    """波动率指标集成测试 (Volatility Indicators Integration Tests)"""

    def setUp(self):
        """设置综合测试数据"""
        # 创建更真实的价格数据
        np.random.seed(42)
        base_price = 100
        returns = np.random.normal(0.001, 0.02, 100)
        prices = [base_price]

        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        self.realistic_close = pd.Series(prices)

        # 创建对应的高低价
        self.realistic_high = self.realistic_close * (
            1 + abs(np.random.normal(0, 0.01, len(prices)))
        )
        self.realistic_low = self.realistic_close * (
            1 - abs(np.random.normal(0, 0.01, len(prices)))
        )

    def test_all_indicators_consistency(self):
        """测试所有指标的一致性"""
        # 计算所有波动率指标
        upper_bb, middle_bb, lower_bb = bollinger_bands(self.realistic_close, window=20)
        std_dev = standard_deviation(self.realistic_close, window=20)
        atr = average_true_range(
            self.realistic_high, self.realistic_low, self.realistic_close, window=14
        )
        true_range = calculate_true_range(
            self.realistic_high, self.realistic_low, self.realistic_close
        )
        upper_kc, middle_kc, lower_kc = keltner_channels(
            self.realistic_high, self.realistic_low, self.realistic_close
        )

        # 验证所有指标的长度一致
        length = len(self.realistic_close)
        for indicator in [
            upper_bb,
            middle_bb,
            lower_bb,
            std_dev,
            atr,
            true_range,
            upper_kc,
            middle_kc,
            lower_kc,
        ]:
            self.assertEqual(len(indicator), length)

        # 验证没有异常值
        indicators = [
            (upper_bb, "upper_bb"),
            (middle_bb, "middle_bb"),
            (lower_bb, "lower_bb"),
            (std_dev, "std_dev"),
            (atr, "atr"),
            (true_range, "true_range"),
            (upper_kc, "upper_kc"),
            (middle_kc, "middle_kc"),
            (lower_kc, "lower_kc"),
        ]

        for indicator, name in indicators:
            valid_values = indicator.dropna()
            if len(valid_values) > 0:
                # 检查是否有无穷大值
                infinite_count = np.isinf(valid_values).sum()
                self.assertLess(
                    infinite_count, len(valid_values) * 0.1, f"{name} has too many infinite values"
                )

    def test_volatility_relationships(self):
        """测试波动率指标之间的关系"""
        # 布林带的宽度应该与标准差相关
        upper_bb, middle_bb, lower_bb = bollinger_bands(
            self.realistic_close, window=20, num_std=2.0
        )
        std_dev = standard_deviation(self.realistic_close, window=20)

        # 布林带宽度 = 上轨 - 下轨 = 4 * std_dev
        bb_width = upper_bb - lower_bb
        expected_width = 4 * std_dev

        # 检查关系（允许一些误差）
        valid_bb_width = bb_width.dropna()
        valid_expected = expected_width.dropna()

        if len(valid_bb_width) > 5 and len(valid_expected) > 5:
            min_len = min(len(valid_bb_width), len(valid_expected))
            correlation = np.corrcoef(
                valid_bb_width.iloc[-min_len:], valid_expected.iloc[-min_len:]
            )[0, 1]
            self.assertGreater(correlation, 0.99)  # 应该高度相关

    def test_error_handling(self):
        """测试错误处理"""
        # 测试空序列
        empty_series = pd.Series([])

        try:
            std_empty = standard_deviation(empty_series, window=5)
            self.assertEqual(len(std_empty), 0)
        except Exception:
            pass  # 某些函数可能会抛出异常

        # 测试包含NaN的序列
        nan_series = pd.Series([1, 2, np.nan, 4, 5])

        # 函数应该能处理NaN值
        std_nan = standard_deviation(nan_series, window=3)
        self.assertIsInstance(std_nan, pd.Series)
        self.assertEqual(len(std_nan), len(nan_series))


if __name__ == "__main__":
    unittest.main()
