"""
测试技术指标模块 (Test Technical Indicators Module)
"""

import unittest

import numpy as np
import pandas as pd

from src.indicators.atr import (
    calculate_atr,
    calculate_atr_from_ohlc,
    calculate_atr_single_value,
    calculate_true_range,
    compute_atr,
)


class TestATRCalculation(unittest.TestCase):
    """测试ATR计算功能"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试OHLC数据
        dates = pd.date_range("2023-01-01", periods=30, freq="D")
        np.random.seed(42)  # 确保测试的可重复性

        # 生成模拟价格数据
        base_price = 100.0
        prices = []
        for i in range(30):
            daily_change = np.random.normal(0, 2)  # 每日变化
            base_price += daily_change
            high = base_price + abs(np.random.normal(0, 1))
            low = base_price - abs(np.random.normal(0, 1))
            close = base_price + np.random.normal(0, 0.5)
            prices.append([high, low, close])

        self.test_data = pd.DataFrame(prices, index=dates, columns=["high", "low", "close"])

    def test_calculate_true_range(self):
        """测试真实波幅计算"""
        tr = calculate_true_range(
            self.test_data["high"], self.test_data["low"], self.test_data["close"]
        )

        # 检查结果类型和长度
        self.assertIsInstance(tr, pd.Series)
        self.assertEqual(len(tr), len(self.test_data))

        # TR应该都是正数或零
        self.assertTrue((tr >= 0).all())

        # 第一个值应该是NaN或等于high-low（因为没有前一日收盘价）
        self.assertTrue(
            pd.isna(tr.iloc[0])
            or tr.iloc[0] == self.test_data["high"].iloc[0] - self.test_data["low"].iloc[0]
        )

    def test_calculate_atr(self):
        """测试ATR计算"""
        window = 14
        atr = calculate_atr(
            self.test_data["high"], self.test_data["low"], self.test_data["close"], window
        )

        # 检查结果
        self.assertIsInstance(atr, pd.Series)
        self.assertEqual(len(atr), len(self.test_data))
        self.assertTrue((atr >= 0).all())

        # 检查前几个值（应该有一些NaN）
        self.assertFalse(pd.isna(atr.iloc[-1]))  # 最后的值不应该是NaN

    def test_calculate_atr_from_ohlc(self):
        """测试从OHLC数据框计算ATR"""
        atr = calculate_atr_from_ohlc(self.test_data)

        self.assertIsInstance(atr, pd.Series)
        self.assertEqual(len(atr), len(self.test_data))

    def test_calculate_atr_from_ohlc_missing_columns(self):
        """测试缺少必要列时的错误处理"""
        incomplete_data = self.test_data[["high", "low"]].copy()  # 缺少close列

        with self.assertRaises(ValueError):
            calculate_atr_from_ohlc(incomplete_data)

    def test_calculate_atr_single_value(self):
        """测试获取单一ATR值"""
        atr_value = calculate_atr_single_value(
            self.test_data["high"], self.test_data["low"], self.test_data["close"]
        )

        self.assertIsInstance(atr_value, float)
        self.assertGreaterEqual(atr_value, 0.0)

    def test_calculate_atr_invalid_window(self):
        """测试无效窗口大小"""
        with self.assertRaises(ValueError):
            calculate_atr(
                self.test_data["high"], self.test_data["low"], self.test_data["close"], window=0
            )

    def test_compute_atr_compatibility(self):
        """测试兼容性函数"""
        # 使用收盘价序列
        atr_value = compute_atr(self.test_data["close"])

        self.assertIsInstance(atr_value, float)
        self.assertGreaterEqual(atr_value, 0.0)

    def test_atr_consistency(self):
        """测试ATR计算的一致性"""
        # 两种方法应该产生相同的结果
        atr1 = calculate_atr(self.test_data["high"], self.test_data["low"], self.test_data["close"])

        atr2 = calculate_atr_from_ohlc(self.test_data)

        # 结果应该相同
        pd.testing.assert_series_equal(atr1, atr2)

    def test_empty_data(self):
        """测试空数据的处理"""
        empty_series = pd.Series(dtype=float)

        atr_value = compute_atr(empty_series)
        self.assertEqual(atr_value, 0.0)

    def test_atr_mathematical_properties(self):
        """测试ATR的数学特性"""
        atr = calculate_atr(
            self.test_data["high"], self.test_data["low"], self.test_data["close"], window=5
        )

        # ATR应该都是非负数
        self.assertTrue((atr >= 0).all(), "ATR值应该都是非负数")

        # ATR的最后几个值应该不是NaN
        self.assertFalse(pd.isna(atr.iloc[-1]), "最新的ATR值不应该是NaN")
        self.assertFalse(pd.isna(atr.iloc[-5:]).all(), "最近5个ATR值不应该全是NaN")

        # ATR应该反映价格的波动性：当价格变化大时，ATR通常也较大
        # 但这种关系可能不是严格的线性关系，所以我们只测试基本的数学性质

        # 检查ATR的平滑性：ATR序列的波动应该比真实波幅更平滑
        tr = calculate_true_range(
            self.test_data["high"], self.test_data["low"], self.test_data["close"]
        )

        # 在有效数据范围内，ATR的标准差应该小于等于TR的标准差
        valid_atr = atr.dropna()
        valid_tr = tr.dropna()

        if len(valid_atr) > 5 and len(valid_tr) > 5:
            atr_std = valid_atr.std()
            tr_std = valid_tr.std()

            # ATR作为移动平均，其波动性通常小于原始TR
            self.assertLessEqual(
                atr_std,
                tr_std * 1.1,  # 允许10%的误差
                "ATR的波动性应该小于或接近原始真实波幅的波动性",
            )


if __name__ == "__main__":
    unittest.main()
