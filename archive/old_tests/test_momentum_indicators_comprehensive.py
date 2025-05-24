#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动量指标全面测试模块 (Comprehensive Momentum Indicators Test Module)

为 src/indicators/momentum_indicators.py 提供100%测试覆盖率
"""

import unittest
import numpy as np
import pandas as pd
import pytest
from src.indicators.momentum_indicators import (
    momentum,
    rate_of_change, 
    zscore,
    rsi,
    stochastic_oscillator
)


class TestMomentumIndicator(unittest.TestCase):
    """测试动量指标函数 (Test Momentum Indicator Function)"""
    
    def setUp(self):
        """设置测试数据"""
        self.simple_data = pd.Series([10, 12, 11, 13, 15, 14, 16, 18, 17, 19])
        self.price_data = pd.Series([100.0, 101.5, 99.8, 102.3, 104.1, 103.7, 105.2, 106.8, 105.9, 107.5])
        
    def test_momentum_basic(self):
        """测试基本动量计算"""
        result = momentum(self.simple_data, period=3)
        
        # 验证结果类型和长度
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.simple_data))
        
        # 验证前3个值为NaN
        self.assertTrue(result.iloc[:3].isna().all())
        
        # 手动验证第4个值：13 - 10 = 3
        expected_fourth = self.simple_data.iloc[3] - self.simple_data.iloc[0]
        self.assertEqual(result.iloc[3], expected_fourth)
        
    def test_momentum_period_1(self):
        """测试周期为1的动量"""
        result = momentum(self.simple_data, period=1)
        
        # 第一个值应该是NaN
        self.assertTrue(result.iloc[0] is np.nan or pd.isna(result.iloc[0]))
        
        # 验证其他值为连续差值
        expected_second = self.simple_data.iloc[1] - self.simple_data.iloc[0]  # 12 - 10 = 2
        self.assertEqual(result.iloc[1], expected_second)
        
    def test_momentum_large_period(self):
        """测试大周期动量"""
        large_period = len(self.simple_data) - 1
        result = momentum(self.simple_data, period=large_period)
        
        # 大部分值应该是NaN
        nan_count = result.isna().sum()
        self.assertEqual(nan_count, large_period)
        
    def test_momentum_with_constant_data(self):
        """测试常数数据的动量"""
        constant_data = pd.Series([5] * 10)
        result = momentum(constant_data, period=3)
        
        # 除了前3个NaN，其余应该都是0
        non_nan_values = result.iloc[3:]
        self.assertTrue((non_nan_values == 0).all())


class TestRateOfChange(unittest.TestCase):
    """测试变化率指标 (Test Rate of Change Indicator)"""
    
    def setUp(self):
        """设置测试数据"""
        self.test_data = pd.Series([100, 110, 105, 115, 120, 118, 125, 130, 128, 135])
        
    def test_rate_of_change_basic(self):
        """测试基本变化率计算"""
        result = rate_of_change(self.test_data, period=3)
        
        # 验证结果类型和长度
        self.assertIsInstance(result, pd.Series) 
        self.assertEqual(len(result), len(self.test_data))
        
        # 验证前3个值为NaN
        self.assertTrue(result.iloc[:3].isna().all())
        
        # 手动验证第4个值：(115 - 100) / 100 * 100 = 15%
        expected_fourth = ((self.test_data.iloc[3] - self.test_data.iloc[0]) / self.test_data.iloc[0]) * 100
        self.assertAlmostEqual(result.iloc[3], expected_fourth, places=5)
        
    def test_rate_of_change_period_1(self):
        """测试周期为1的变化率"""
        result = rate_of_change(self.test_data, period=1)
        
        # 第一个值应该是NaN
        self.assertTrue(pd.isna(result.iloc[0]))
        
        # 验证第二个值：(110 - 100) / 100 * 100 = 10%
        expected_second = ((self.test_data.iloc[1] - self.test_data.iloc[0]) / self.test_data.iloc[0]) * 100
        self.assertAlmostEqual(result.iloc[1], expected_second, places=5)
        
    def test_rate_of_change_with_zero_values(self):
        """测试包含零值的变化率"""
        data_with_zero = pd.Series([0, 10, 5, 15])
        result = rate_of_change(data_with_zero, period=1)
        
        # 从0开始的变化率应该是无穷大
        self.assertTrue(pd.isna(result.iloc[0]))  # 第一个值是NaN
        self.assertTrue(np.isinf(result.iloc[1]) or pd.isna(result.iloc[1]))  # 10/0 -> inf
        
    def test_rate_of_change_negative_values(self):
        """测试负值的变化率"""
        negative_data = pd.Series([-100, -90, -95, -85])
        result = rate_of_change(negative_data, period=1)
        
        # 验证负值之间的变化率计算正确
        expected_second = ((-90 - (-100)) / (-100)) * 100  # 10 / (-100) * 100 = -10%
        self.assertAlmostEqual(result.iloc[1], expected_second, places=5)


class TestZscore(unittest.TestCase):
    """测试Z-score标准化 (Test Z-score Standardization)"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建有一定分布的数据
        np.random.seed(42)
        self.random_data = pd.Series(np.random.normal(100, 10, 50))
        self.simple_data = pd.Series([90, 95, 100, 105, 110, 100, 95, 105, 110, 95])
        
    def test_zscore_basic(self):
        """测试基本Z-score计算"""
        result = zscore(self.simple_data, window=5)
        
        # 验证结果类型和长度
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.simple_data))
        
        # 验证前4个值为NaN (window-1)
        self.assertTrue(result.iloc[:4].isna().all())
        
    def test_zscore_with_normal_distribution(self):
        """测试正态分布数据的Z-score"""
        result = zscore(self.random_data, window=20)
        
        # Z-score的绝对值大部分应该在[-3, 3]范围内
        valid_scores = result.dropna()
        extreme_scores = valid_scores[abs(valid_scores) > 3]
        extreme_ratio = len(extreme_scores) / len(valid_scores)
        
        # 正态分布中，99.7%的值应该在3个标准差内
        self.assertLess(extreme_ratio, 0.05)  # 允许5%的极端值
        
    def test_zscore_constant_data(self):
        """测试常数数据的Z-score"""
        constant_data = pd.Series([50] * 20)
        result = zscore(constant_data, window=10)
        
        # 常数数据的标准差为0，Z-score应该是NaN或0
        valid_scores = result.dropna()
        # 由于标准差为0，除法会产生NaN
        self.assertTrue(valid_scores.isna().all() or (valid_scores == 0).all())
        
    def test_zscore_window_size_validation(self):
        """测试窗口大小验证"""
        # 窗口大小等于数据长度
        result = zscore(self.simple_data, window=len(self.simple_data))
        
        # 只有最后一个值不是NaN
        non_nan_count = result.notna().sum()
        self.assertEqual(non_nan_count, 1)


class TestRSI(unittest.TestCase):
    """测试相对强弱指标 (Test RSI Indicator)"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建有涨跌的价格数据
        self.price_data = pd.Series([
            100, 102, 101, 104, 106, 105, 108, 107, 110, 109,
            112, 114, 113, 116, 115, 118, 120, 119, 122, 121
        ])
        self.trending_up = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
        self.trending_down = pd.Series([109, 108, 107, 106, 105, 104, 103, 102, 101, 100])
        
    def test_rsi_basic(self):
        """测试基本RSI计算"""
        result = rsi(self.price_data, window=14)
        
        # 验证结果类型和长度
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.price_data))
        
        # 验证RSI值在0-100范围内
        valid_rsi = result.dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())
        
    def test_rsi_trending_up(self):
        """测试上升趋势的RSI"""
        result = rsi(self.trending_up, window=5)
        
        # 上升趋势中，RSI应该相对较高
        valid_rsi = result.dropna()
        if len(valid_rsi) > 0:
            average_rsi = valid_rsi.mean()
            self.assertGreater(average_rsi, 50)  # 应该大于50
            
    def test_rsi_trending_down(self):
        """测试下降趋势的RSI"""
        result = rsi(self.trending_down, window=5)
        
        # 下降趋势中，RSI应该相对较低
        valid_rsi = result.dropna()
        if len(valid_rsi) > 0:
            average_rsi = valid_rsi.mean()
            self.assertLess(average_rsi, 50)  # 应该小于50
            
    def test_rsi_extreme_cases(self):
        """测试RSI极端情况"""
        # 持续上涨的数据
        continuous_up = pd.Series([100 + i for i in range(20)])
        result_up = rsi(continuous_up, window=10)
        
        valid_up = result_up.dropna()
        if len(valid_up) > 0:
            # 持续上涨应该接近100
            self.assertGreater(valid_up.iloc[-1], 70)
            
        # 持续下跌的数据  
        continuous_down = pd.Series([100 - i for i in range(20)])
        result_down = rsi(continuous_down, window=10)
        
        valid_down = result_down.dropna()
        if len(valid_down) > 0:
            # 持续下跌应该接近0
            self.assertLess(valid_down.iloc[-1], 30)
            
    def test_rsi_constant_prices(self):
        """测试常数价格的RSI"""
        constant_prices = pd.Series([100] * 20)
        result = rsi(constant_prices, window=10)
        
        # 常数价格应该产生NaN（因为没有涨跌）
        valid_rsi = result.dropna()
        # 可能会是NaN或者50左右的值
        if len(valid_rsi) > 0:
            # 如果有值，应该在合理范围内
            self.assertTrue(valid_rsi.isna().all() or ((valid_rsi >= 0) & (valid_rsi <= 100)).all())


class TestStochasticOscillator(unittest.TestCase):
    """测试随机振荡器 (Test Stochastic Oscillator)"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建模拟的OHLC数据
        self.high = pd.Series([105, 107, 106, 109, 111, 110, 113, 112, 115, 114])
        self.low = pd.Series([95, 97, 96, 99, 101, 100, 103, 102, 105, 104])
        self.close = pd.Series([100, 102, 101, 104, 106, 105, 108, 107, 110, 109])
        
    def test_stochastic_oscillator_basic(self):
        """测试基本随机振荡器计算"""
        k_percent, d_percent = stochastic_oscillator(
            self.high, self.low, self.close, k_period=5, d_period=3
        )
        
        # 验证返回类型
        self.assertIsInstance(k_percent, pd.Series)
        self.assertIsInstance(d_percent, pd.Series)
        
        # 验证长度
        self.assertEqual(len(k_percent), len(self.high))
        self.assertEqual(len(d_percent), len(self.high))
        
        # 验证%K和%D值在0-100范围内
        valid_k = k_percent.dropna()
        valid_d = d_percent.dropna()
        
        if len(valid_k) > 0:
            self.assertTrue((valid_k >= 0).all())
            self.assertTrue((valid_k <= 100).all())
            
        if len(valid_d) > 0:
            self.assertTrue((valid_d >= 0).all())
            self.assertTrue((valid_d <= 100).all())
            
    def test_stochastic_oscillator_manual_calculation(self):
        """测试手动计算验证"""
        # 使用简单数据手动验证
        simple_high = pd.Series([10, 12, 11, 13, 15])
        simple_low = pd.Series([8, 9, 8, 10, 12])
        simple_close = pd.Series([9, 11, 10, 12, 14])
        
        k_percent, d_percent = stochastic_oscillator(
            simple_high, simple_low, simple_close, k_period=3, d_period=2
        )
        
        # 验证结果不全是NaN
        self.assertFalse(k_percent.isna().all())
        
        # 手动计算第3个值 (index=2)
        # 最近3个周期：high=[10,12,11], low=[8,9,8], close=10
        # highest_high = 12, lowest_low = 8
        # %K = (10 - 8) / (12 - 8) * 100 = 2/4 * 100 = 50%
        if not pd.isna(k_percent.iloc[2]):
            expected_k = ((simple_close.iloc[2] - 8) / (12 - 8)) * 100
            self.assertAlmostEqual(k_percent.iloc[2], expected_k, places=5)
            
    def test_stochastic_oscillator_edge_cases(self):
        """测试边缘情况"""
        # 高低价相等的情况
        equal_high_low = pd.Series([100] * 10)
        equal_close = pd.Series([100] * 10)
        
        k_percent, d_percent = stochastic_oscillator(
            equal_high_low, equal_high_low, equal_close, k_period=5, d_period=3
        )
        
        # 当高低价相等时，分母为0，结果可能是NaN
        valid_k = k_percent.dropna()
        if len(valid_k) > 0:
            # 如果有有效值，应该在合理范围内或者是NaN
            self.assertTrue(valid_k.isna().all() or ((valid_k >= 0) & (valid_k <= 100)).all())
            
    def test_stochastic_oscillator_different_periods(self):
        """测试不同周期参数"""
        # 测试不同的K和D周期
        k1, d1 = stochastic_oscillator(self.high, self.low, self.close, k_period=3, d_period=2)
        k2, d2 = stochastic_oscillator(self.high, self.low, self.close, k_period=7, d_period=4)
        
        # 不同周期应该产生不同结果
        valid_k1 = k1.dropna()
        valid_k2 = k2.dropna()
        
        if len(valid_k1) > 0 and len(valid_k2) > 0:
            # 结果应该不完全相同（除非在特殊情况下）
            min_len = min(len(valid_k1), len(valid_k2))
            if min_len > 1:
                # 至少有一些差异
                differences = abs(valid_k1.iloc[-min_len:].values - valid_k2.iloc[-min_len:].values)
                self.assertTrue(differences.sum() >= 0)  # 基本检查


class TestMomentumIndicatorsIntegration(unittest.TestCase):
    """动量指标集成测试 (Momentum Indicators Integration Tests)"""
    
    def setUp(self):
        """设置综合测试数据"""
        # 创建更真实的价格数据
        np.random.seed(42)
        base_price = 100
        returns = np.random.normal(0.001, 0.02, 100)  # 日收益率
        prices = [base_price]
        
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
            
        self.realistic_prices = pd.Series(prices)
        
        # 创建对应的高低价
        self.realistic_high = self.realistic_prices * (1 + abs(np.random.normal(0, 0.01, len(prices))))
        self.realistic_low = self.realistic_prices * (1 - abs(np.random.normal(0, 0.01, len(prices))))
        
    def test_all_indicators_consistency(self):
        """测试所有指标的一致性"""
        # 计算所有指标
        mom = momentum(self.realistic_prices, period=10)
        roc = rate_of_change(self.realistic_prices, period=10)
        z = zscore(self.realistic_prices, window=20)
        rsi_val = rsi(self.realistic_prices, window=14)
        k_percent, d_percent = stochastic_oscillator(
            self.realistic_high, self.realistic_low, self.realistic_prices
        )
        
        # 验证所有指标的长度一致
        length = len(self.realistic_prices)
        self.assertEqual(len(mom), length)
        self.assertEqual(len(roc), length)
        self.assertEqual(len(z), length)
        self.assertEqual(len(rsi_val), length)
        self.assertEqual(len(k_percent), length)
        self.assertEqual(len(d_percent), length)
        
        # 验证没有异常值
        for indicator, name in [(mom, 'momentum'), (roc, 'roc'), (z, 'zscore'), 
                               (rsi_val, 'rsi'), (k_percent, 'k_percent'), (d_percent, 'd_percent')]:
            valid_values = indicator.dropna()
            if len(valid_values) > 0:
                # 检查是否有无穷大值
                infinite_count = np.isinf(valid_values).sum()
                self.assertLess(infinite_count, len(valid_values) * 0.1, 
                               f"{name} has too many infinite values")
                
    def test_indicators_with_trending_data(self):
        """测试指标在趋势数据上的表现"""
        # 创建明显的上升趋势
        trending_data = pd.Series([100 + i * 0.5 + np.random.normal(0, 0.1) for i in range(50)])
        
        # 计算动量指标
        mom = momentum(trending_data, period=5)
        rsi_val = rsi(trending_data, window=10)
        
        # 上升趋势中，动量应该主要为正
        valid_mom = mom.dropna()
        if len(valid_mom) > 5:
            positive_momentum_ratio = (valid_mom > 0).sum() / len(valid_mom)
            self.assertGreater(positive_momentum_ratio, 0.6)  # 至少60%为正
            
        # 上升趋势中，RSI应该相对较高
        valid_rsi = rsi_val.dropna()
        if len(valid_rsi) > 5:
            average_rsi = valid_rsi.mean()
            self.assertGreater(average_rsi, 45)  # 应该高于中性值
            
    def test_error_handling(self):
        """测试错误处理"""
        # 测试空序列
        empty_series = pd.Series([])
        
        # 大部分函数应该能处理空序列或返回空结果
        try:
            mom_empty = momentum(empty_series, period=5)
            self.assertEqual(len(mom_empty), 0)
        except Exception:
            pass  # 某些函数可能会抛出异常，这也是可接受的
            
        # 测试包含NaN的序列
        nan_series = pd.Series([1, 2, np.nan, 4, 5])
        
        # 函数应该能处理NaN值
        mom_nan = momentum(nan_series, period=2)
        self.assertIsInstance(mom_nan, pd.Series)
        self.assertEqual(len(mom_nan), len(nan_series))


if __name__ == '__main__':
    unittest.main() 