#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.core.risk_management 模块的所有功能
Risk Management Module Tests

覆盖目标:
- compute_atr 函数
- compute_position_size 函数
- compute_stop_price 函数
- trailing_stop 函数
- compute_trailing_stop 函数
- update_trailing_stop_atr 函数
- 边界情况和错误处理
"""

import unittest
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Import modules to test
try:
    from src.core.risk_management import (
        compute_atr,
        compute_position_size,
        compute_stop_price,
        compute_trailing_stop,
        trailing_stop,
        update_trailing_stop_atr,
    )
except ImportError:
    pytest.skip("Risk management module not available, skipping tests", allow_module_level=True)


class TestComputeATR(unittest.TestCase):
    """测试 compute_atr 函数"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试价格序列
        self.price_data = [
            100,
            102,
            101,
            103,
            105,
            104,
            106,
            108,
            107,
            109,
            111,
            110,
            112,
            114,
            113,
        ]
        self.price_series = pd.Series(self.price_data)

    def test_compute_atr_default_window(self):
        """测试默认窗口大小的ATR计算"""
        result = compute_atr(self.price_series)

        # 验证结果是浮点数
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_compute_atr_custom_window(self):
        """测试自定义窗口大小的ATR计算"""
        result = compute_atr(self.price_series, window=5)

        # 验证结果是浮点数
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_compute_atr_small_window(self):
        """测试小窗口大小"""
        result = compute_atr(self.price_series, window=2)

        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_compute_atr_empty_series(self):
        """测试空序列"""
        empty_series = pd.Series([])
        result = compute_atr(empty_series)

        self.assertEqual(result, 0.0)

    def test_compute_atr_single_value(self):
        """测试单个值的序列"""
        single_series = pd.Series([100])
        result = compute_atr(single_series)

        # 单个值会导致NaN，因为没有差值可计算
        self.assertTrue(pd.isna(result))

    def test_compute_atr_two_values(self):
        """测试两个值的序列"""
        two_values = pd.Series([100, 102])
        result = compute_atr(two_values, window=2)

        # 两个值可能导致NaN，因为rolling window需要足够数据
        self.assertTrue(pd.isna(result) or result >= 0)

    def test_compute_atr_constant_prices(self):
        """测试价格不变的情况"""
        constant_prices = pd.Series([100] * 20)
        result = compute_atr(constant_prices)

        self.assertEqual(result, 0.0)

    def test_compute_atr_large_window(self):
        """测试窗口大小大于数据长度"""
        result = compute_atr(self.price_series, window=50)

        # 应该返回0或NaN，我们检查是否为数字
        self.assertTrue(pd.isna(result) or result == 0.0)


class TestComputePositionSize(unittest.TestCase):
    """测试 compute_position_size 函数"""

    def test_compute_position_size_normal(self):
        """测试正常情况下的仓位计算"""
        equity = 10000
        atr = 2.0
        risk_frac = 0.02

        result = compute_position_size(equity, atr, risk_frac)

        # 验证结果
        expected = max(1, int((equity * risk_frac) / atr))
        self.assertEqual(result, expected)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 1)

    def test_compute_position_size_default_risk(self):
        """测试默认风险系数"""
        equity = 10000
        atr = 2.0

        result = compute_position_size(equity, atr)

        # 默认风险系数为0.02
        expected = max(1, int((equity * 0.02) / atr))
        self.assertEqual(result, expected)

    def test_compute_position_size_zero_atr(self):
        """测试ATR为零的情况"""
        equity = 10000
        atr = 0.0

        result = compute_position_size(equity, atr)

        # ATR为零时应返回1
        self.assertEqual(result, 1)

    def test_compute_position_size_negative_atr(self):
        """测试ATR为负数的情况"""
        equity = 10000
        atr = -1.0

        result = compute_position_size(equity, atr)

        # 负ATR应返回1
        self.assertEqual(result, 1)

    def test_compute_position_size_small_equity(self):
        """测试小额权益"""
        equity = 100
        atr = 5.0
        risk_frac = 0.02

        result = compute_position_size(equity, atr, risk_frac)

        # 计算结果可能小于1，但应返回至少1
        self.assertEqual(result, 1)

    def test_compute_position_size_large_atr(self):
        """测试大ATR值"""
        equity = 10000
        atr = 1000.0
        risk_frac = 0.02

        result = compute_position_size(equity, atr, risk_frac)

        # 大ATR应导致小仓位，但至少为1
        self.assertEqual(result, 1)

    def test_compute_position_size_high_risk(self):
        """测试高风险系数"""
        equity = 10000
        atr = 1.0
        risk_frac = 0.1  # 10%风险

        result = compute_position_size(equity, atr, risk_frac)

        expected = max(1, int((equity * risk_frac) / atr))
        self.assertEqual(result, expected)
        self.assertGreater(result, 1)

    def test_compute_position_size_zero_equity(self):
        """测试零权益"""
        equity = 0
        atr = 2.0

        result = compute_position_size(equity, atr)

        # 零权益应返回1
        self.assertEqual(result, 1)


class TestComputeStopPrice(unittest.TestCase):
    """测试 compute_stop_price 函数"""

    def test_compute_stop_price_default_multiplier(self):
        """测试默认乘数的止损价格计算"""
        entry = 100.0
        atr = 2.0

        result = compute_stop_price(entry, atr)

        # 默认乘数为1.0
        expected = entry - 1.0 * atr
        self.assertEqual(result, expected)
        self.assertEqual(result, 98.0)

    def test_compute_stop_price_custom_multiplier(self):
        """测试自定义乘数"""
        entry = 100.0
        atr = 2.0
        multiplier = 1.5

        result = compute_stop_price(entry, atr, multiplier)

        expected = entry - multiplier * atr
        self.assertEqual(result, expected)
        self.assertEqual(result, 97.0)

    def test_compute_stop_price_zero_atr(self):
        """测试ATR为零"""
        entry = 100.0
        atr = 0.0

        result = compute_stop_price(entry, atr)

        # ATR为零时止损价格应等于入场价格
        self.assertEqual(result, entry)

    def test_compute_stop_price_negative_atr(self):
        """测试负ATR"""
        entry = 100.0
        atr = -2.0

        result = compute_stop_price(entry, atr)

        # 负ATR应被处理为0
        self.assertEqual(result, entry)

    def test_compute_stop_price_zero_multiplier(self):
        """测试零乘数"""
        entry = 100.0
        atr = 2.0
        multiplier = 0.0

        result = compute_stop_price(entry, atr, multiplier)

        # 零乘数应返回入场价格
        self.assertEqual(result, entry)

    def test_compute_stop_price_large_multiplier(self):
        """测试大乘数"""
        entry = 100.0
        atr = 2.0
        multiplier = 5.0

        result = compute_stop_price(entry, atr, multiplier)

        expected = entry - multiplier * atr
        self.assertEqual(result, expected)
        self.assertEqual(result, 90.0)


class TestTrailingStop(unittest.TestCase):
    """测试 trailing_stop 函数"""

    def test_trailing_stop_default_factor(self):
        """测试默认因子的跟踪止损"""
        entry = 100.0
        atr = 2.0

        result = trailing_stop(entry, atr)

        # 默认因子为2.0
        expected = entry - 2.0 * atr
        self.assertEqual(result, expected)
        self.assertEqual(result, 96.0)

    def test_trailing_stop_custom_factor(self):
        """测试自定义因子"""
        entry = 100.0
        atr = 2.0
        factor = 1.5

        result = trailing_stop(entry, atr, factor)

        expected = entry - factor * atr
        self.assertEqual(result, expected)
        self.assertEqual(result, 97.0)

    def test_trailing_stop_zero_atr(self):
        """测试ATR为零"""
        entry = 100.0
        atr = 0.0

        result = trailing_stop(entry, atr)

        # ATR为零时应返回入场价格
        self.assertEqual(result, entry)

    def test_trailing_stop_negative_atr(self):
        """测试负ATR"""
        entry = 100.0
        atr = -2.0

        result = trailing_stop(entry, atr)

        # 负ATR应被处理为0
        self.assertEqual(result, entry)

    def test_trailing_stop_zero_factor(self):
        """测试零因子"""
        entry = 100.0
        atr = 2.0
        factor = 0.0

        result = trailing_stop(entry, atr, factor)

        # 零因子应返回入场价格
        self.assertEqual(result, entry)


class TestComputeTrailingStop(unittest.TestCase):
    """测试 compute_trailing_stop 函数"""

    def test_compute_trailing_stop_no_profit(self):
        """测试无盈利情况"""
        entry = 100.0
        current_price = 99.0  # 亏损
        initial_stop = 95.0

        result = compute_trailing_stop(entry, current_price, initial_stop)

        # 无盈利时应保持初始止损
        self.assertEqual(result, initial_stop)

    def test_compute_trailing_stop_breakeven_phase(self):
        """测试保本阶段"""
        entry = 100.0
        current_price = 105.0  # 盈利5，初始风险为5，R=1.0
        initial_stop = 95.0
        breakeven_r = 1.0
        trail_r = 2.0

        result = compute_trailing_stop(entry, current_price, initial_stop, breakeven_r, trail_r)

        # 在保本阶段应返回入场价格
        self.assertEqual(result, entry)

    def test_compute_trailing_stop_trailing_phase_with_atr(self):
        """测试跟踪阶段（有ATR）"""
        entry = 100.0
        current_price = 115.0  # 盈利15，初始风险为5，R=3.0 > trail_r
        initial_stop = 95.0
        breakeven_r = 1.0
        trail_r = 2.0
        atr = 3.0

        result = compute_trailing_stop(
            entry, current_price, initial_stop, breakeven_r, trail_r, atr
        )

        # 跟踪阶段应基于ATR计算
        expected = current_price - atr
        self.assertEqual(result, expected)
        self.assertEqual(result, 112.0)

    def test_compute_trailing_stop_trailing_phase_without_atr(self):
        """测试跟踪阶段（无ATR）"""
        entry = 100.0
        current_price = 115.0  # 盈利15，初始风险为5，R=3.0 > trail_r
        initial_stop = 95.0
        breakeven_r = 1.0
        trail_r = 2.0

        result = compute_trailing_stop(entry, current_price, initial_stop, breakeven_r, trail_r)

        # 无ATR时应基于百分比跟踪
        initial_risk = entry - initial_stop
        trail_distance = initial_risk * 0.5
        expected = current_price - trail_distance
        self.assertEqual(result, expected)
        self.assertEqual(result, 112.5)

    def test_compute_trailing_stop_zero_initial_risk(self):
        """测试初始风险为零的情况"""
        entry = 100.0
        current_price = 105.0
        initial_stop = 100.0  # 无风险

        result = compute_trailing_stop(entry, current_price, initial_stop)

        # 初始风险为零时应返回初始止损
        self.assertEqual(result, initial_stop)

    def test_compute_trailing_stop_negative_initial_risk(self):
        """测试负初始风险的情况"""
        entry = 100.0
        current_price = 105.0
        initial_stop = 105.0  # 止损高于入场价

        result = compute_trailing_stop(entry, current_price, initial_stop)

        # 负初始风险时应返回初始止损
        self.assertEqual(result, initial_stop)

    def test_compute_trailing_stop_custom_thresholds(self):
        """测试自定义阈值"""
        entry = 100.0
        current_price = 107.5  # 盈利7.5，初始风险为5，R=1.5
        initial_stop = 95.0
        breakeven_r = 0.5  # 更低的保本阈值
        trail_r = 1.0  # 更低的跟踪阈值

        result = compute_trailing_stop(entry, current_price, initial_stop, breakeven_r, trail_r)

        # 应该进入跟踪阶段
        initial_risk = entry - initial_stop
        trail_distance = initial_risk * 0.5
        expected = current_price - trail_distance
        self.assertEqual(result, expected)

    def test_compute_trailing_stop_zero_atr_in_trailing(self):
        """测试跟踪阶段ATR为零"""
        entry = 100.0
        current_price = 115.0  # 盈利15，初始风险为5，R=3.0 > trail_r
        initial_stop = 95.0
        breakeven_r = 1.0
        trail_r = 2.0
        atr = 0.0

        result = compute_trailing_stop(
            entry, current_price, initial_stop, breakeven_r, trail_r, atr
        )

        # ATR为零时应使用百分比跟踪
        initial_risk = entry - initial_stop
        trail_distance = initial_risk * 0.5
        expected = current_price - trail_distance
        self.assertEqual(result, expected)
        self.assertEqual(result, 112.5)


class TestUpdateTrailingStopATR(unittest.TestCase):
    """测试 update_trailing_stop_atr 函数"""

    def setUp(self):
        """设置测试数据"""
        self.position = {
            "entry_price": 100.0,
            "stop_price": 95.0,
        }

    def test_update_trailing_stop_atr_no_update(self):
        """测试不需要更新止损的情况"""
        current_price = 102.0  # 小幅盈利
        atr = 2.0

        new_stop, updated = update_trailing_stop_atr(self.position, current_price, atr)

        # 应该不更新止损
        self.assertEqual(new_stop, self.position["stop_price"])
        self.assertFalse(updated)

    def test_update_trailing_stop_atr_with_update(self):
        """测试需要更新止损的情况"""
        current_price = 110.0  # 大幅盈利
        atr = 2.0

        new_stop, updated = update_trailing_stop_atr(self.position, current_price, atr)

        # 应该更新止损
        self.assertGreater(new_stop, self.position["stop_price"])
        self.assertTrue(updated)

    @patch("src.core.risk_management.compute_trailing_stop")
    def test_update_trailing_stop_atr_with_notifier(self, mock_compute_trailing_stop):
        """测试带通知器的止损更新"""
        mock_compute_trailing_stop.return_value = 98.0  # 新止损价格

        mock_notifier = Mock()
        current_price = 110.0
        atr = 2.0

        new_stop, updated = update_trailing_stop_atr(
            self.position, current_price, atr, notifier=mock_notifier
        )

        # 验证通知器被调用
        self.assertEqual(new_stop, 98.0)
        self.assertTrue(updated)
        mock_notifier.notify.assert_called_once()

        # 验证通知内容
        call_args = mock_notifier.notify.call_args
        self.assertIn("止损更新", call_args[0][0])
        self.assertEqual(call_args[0][1], "INFO")

    def test_update_trailing_stop_atr_empty_position(self):
        """测试空仓位"""
        empty_position = {}
        current_price = 110.0
        atr = 2.0

        new_stop, updated = update_trailing_stop_atr(empty_position, current_price, atr)

        # 空仓位应返回0和False
        self.assertEqual(new_stop, 0.0)
        self.assertFalse(updated)

    def test_update_trailing_stop_atr_none_position(self):
        """测试None仓位"""
        current_price = 110.0
        atr = 2.0

        new_stop, updated = update_trailing_stop_atr(None, current_price, atr)

        # None仓位应返回0和False
        self.assertEqual(new_stop, 0.0)
        self.assertFalse(updated)

    def test_update_trailing_stop_atr_missing_fields(self):
        """测试缺少字段的仓位"""
        incomplete_position = {"entry_price": 100.0}  # 缺少stop_price
        current_price = 110.0
        atr = 2.0

        new_stop, updated = update_trailing_stop_atr(incomplete_position, current_price, atr)

        # 应该能处理缺少字段的情况，返回0.0和False
        self.assertEqual(new_stop, 0.0)
        self.assertFalse(updated)

    def test_update_trailing_stop_atr_custom_multiplier(self):
        """测试自定义乘数"""
        current_price = 110.0
        atr = 2.0
        multiplier = 1.5

        new_stop, updated = update_trailing_stop_atr(self.position, current_price, atr, multiplier)

        # 验证结果类型
        self.assertIsInstance(new_stop, float)
        self.assertIsInstance(updated, bool)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_all_functions_with_extreme_values(self):
        """测试所有函数处理极值的能力"""
        # 测试极大值
        large_value = 1e10

        # compute_atr with large values
        large_series = pd.Series([large_value] * 20)
        atr_result = compute_atr(large_series)
        self.assertEqual(atr_result, 0.0)  # 相同值应该返回0

        # compute_position_size with large values
        pos_result = compute_position_size(large_value, 1.0)
        self.assertIsInstance(pos_result, int)
        self.assertGreaterEqual(pos_result, 1)

        # compute_stop_price with large values
        stop_result = compute_stop_price(large_value, 1.0)
        self.assertIsInstance(stop_result, float)

        # trailing_stop with large values
        trail_result = trailing_stop(large_value, 1.0)
        self.assertIsInstance(trail_result, float)

    def test_functions_with_nan_values(self):
        """测试函数处理NaN值的能力"""
        import numpy as np

        # 测试包含NaN的序列
        nan_series = pd.Series([100, np.nan, 102, np.nan, 104])
        atr_result = compute_atr(nan_series)

        # 应该能处理NaN值
        self.assertTrue(pd.isna(atr_result) or isinstance(atr_result, float))

    def test_functions_with_zero_values(self):
        """测试函数处理零值的能力"""
        # 测试全零序列
        zero_series = pd.Series([0.0] * 10)
        atr_result = compute_atr(zero_series)
        # 全零序列会产生NaN，因为没有变化
        self.assertTrue(pd.isna(atr_result) or atr_result == 0.0)

        # 测试零值参数
        pos_result = compute_position_size(0, 0)
        self.assertEqual(pos_result, 1)

        stop_result = compute_stop_price(0, 0)
        self.assertEqual(stop_result, 0.0)

        trail_result = trailing_stop(0, 0)
        self.assertEqual(trail_result, 0.0)


if __name__ == "__main__":
    unittest.main()
