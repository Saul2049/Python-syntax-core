"""
技术分析模块综合测试 (Comprehensive Technical Analysis Module Tests)

测试覆盖所有技术指标计算功能，包括：
- TechnicalIndicators 类的所有方法
- VolatilityIndicators 类的所有方法
- ReturnAnalysis 类的所有方法
- 便捷函数
- 边界条件和错误处理
"""

import unittest
import warnings

import numpy as np
import pandas as pd

# 抑制pandas警告
warnings.filterwarnings("ignore", category=FutureWarning)


class TestTechnicalIndicators(unittest.TestCase):
    """测试 TechnicalIndicators 类"""

    def setUp(self):
        """设置测试数据"""
        # 创建模拟价格数据
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        base_price = 100
        price_changes = np.random.randn(100) * 0.02
        prices = [base_price]

        for change in price_changes[1:]:
            prices.append(prices[-1] * (1 + change))

        self.prices = pd.Series(prices, index=dates)

        # 创建OHLCV数据
        self.ohlcv_data = pd.DataFrame(
            {
                "open": self.prices * (1 + np.random.randn(100) * 0.005),
                "high": self.prices * (1 + abs(np.random.randn(100)) * 0.01),
                "low": self.prices * (1 - abs(np.random.randn(100)) * 0.01),
                "close": self.prices,
                "volume": np.random.randint(1000, 10000, 100),
            },
            index=dates,
        )

    def test_moving_average_simple(self):
        """测试简单移动平均"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        # 测试简单移动平均
        ma = TechnicalIndicators.moving_average(self.prices, window=10, ma_type="simple")

        self.assertIsInstance(ma, pd.Series)
        self.assertEqual(len(ma), len(self.prices))

        # 验证前9个值为NaN
        self.assertTrue(ma.iloc[:9].isna().all())

        # 验证第10个值是前10个价格的平均值
        expected_ma_10 = self.prices.iloc[:10].mean()
        self.assertAlmostEqual(ma.iloc[9], expected_ma_10, places=6)

    def test_moving_average_exponential(self):
        """测试指数移动平均"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        # 测试指数移动平均
        ema = TechnicalIndicators.moving_average(self.prices, window=10, ma_type="exponential")

        self.assertIsInstance(ema, pd.Series)
        self.assertEqual(len(ema), len(self.prices))

        # EMA不应该有NaN值（除了第一个可能的值）
        non_nan_count = ema.notna().sum()
        self.assertGreater(non_nan_count, 90)

    def test_moving_average_invalid_type(self):
        """测试无效的移动平均类型"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        with self.assertRaises(ValueError) as context:
            TechnicalIndicators.moving_average(self.prices, window=10, ma_type="invalid")

        self.assertIn("不支持的移动平均类型", str(context.exception))

    def test_add_moving_averages_success(self):
        """测试添加多个移动平均线"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        result = TechnicalIndicators.add_moving_averages(
            self.ohlcv_data, price_column="close", windows=[5, 10, 20]
        )

        self.assertIsInstance(result, pd.DataFrame)

        # 检查是否添加了所有移动平均线
        expected_columns = ["MA_5", "MA_10", "MA_20", "EMA_5", "EMA_10", "EMA_20"]
        for col in expected_columns:
            self.assertIn(col, result.columns)

    def test_add_moving_averages_invalid_column(self):
        """测试无效的价格列"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        with self.assertRaises(ValueError) as context:
            TechnicalIndicators.add_moving_averages(self.ohlcv_data, price_column="invalid_column")

        self.assertIn("不存在于DataFrame中", str(context.exception))

    def test_rsi_calculation(self):
        """测试RSI计算"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        rsi = TechnicalIndicators.rsi(self.prices, window=14)

        self.assertIsInstance(rsi, pd.Series)
        self.assertEqual(len(rsi), len(self.prices))

        # RSI值应该在0-100之间
        valid_rsi = rsi.dropna()
        self.assertTrue(all(0 <= val <= 100 for val in valid_rsi))

        # 验证RSI计算逻辑
        self.assertTrue(rsi.iloc[:13].isna().all())  # 前13个值应该是NaN

    def test_bollinger_bands_calculation(self):
        """测试布林带计算"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        bb = TechnicalIndicators.bollinger_bands(self.prices, window=20, std_dev=2.0)

        self.assertIsInstance(bb, dict)
        self.assertIn("BB_middle", bb)
        self.assertIn("BB_upper", bb)
        self.assertIn("BB_lower", bb)

        # 验证布林带关系：下轨 < 中轨 < 上轨
        valid_data = pd.DataFrame(bb).dropna()
        if len(valid_data) > 0:
            self.assertTrue(all(valid_data["BB_lower"] <= valid_data["BB_middle"]))
            self.assertTrue(all(valid_data["BB_middle"] <= valid_data["BB_upper"]))

    def test_macd_calculation(self):
        """测试MACD计算"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        macd = TechnicalIndicators.macd(
            self.prices, fast_period=12, slow_period=26, signal_period=9
        )

        self.assertIsInstance(macd, dict)
        self.assertIn("MACD_line", macd)
        self.assertIn("MACD_signal", macd)
        self.assertIn("MACD_histogram", macd)

        # 验证MACD柱状图 = MACD线 - 信号线
        valid_data = pd.DataFrame(macd).dropna()
        if len(valid_data) > 0:
            calculated_histogram = valid_data["MACD_line"] - valid_data["MACD_signal"]
            pd.testing.assert_series_equal(
                calculated_histogram, valid_data["MACD_histogram"], check_names=False
            )

    def test_stochastic_oscillator_calculation(self):
        """测试随机震荡指标计算"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        stoch = TechnicalIndicators.stochastic_oscillator(
            self.ohlcv_data["high"],
            self.ohlcv_data["low"],
            self.ohlcv_data["close"],
            k_period=14,
            d_period=3,
        )

        self.assertIsInstance(stoch, dict)
        self.assertIn("Stoch_K", stoch)
        self.assertIn("Stoch_D", stoch)

        # %K和%D值应该在0-100之间
        valid_k = stoch["Stoch_K"].dropna()
        valid_d = stoch["Stoch_D"].dropna()

        if len(valid_k) > 0:
            self.assertTrue(all(0 <= val <= 100 for val in valid_k))
        if len(valid_d) > 0:
            self.assertTrue(all(0 <= val <= 100 for val in valid_d))

    def test_add_all_indicators_complete_data(self):
        """测试添加所有指标（完整OHLCV数据）"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        result = TechnicalIndicators.add_all_indicators(self.ohlcv_data, price_column="close")

        self.assertIsInstance(result, pd.DataFrame)

        # 检查是否添加了所有指标
        expected_indicators = [
            "MA_5",
            "MA_10",
            "MA_20",
            "MA_50",
            "MA_200",
            "EMA_5",
            "EMA_10",
            "EMA_20",
            "EMA_50",
            "EMA_200",
            "RSI_14",
            "BB_middle",
            "BB_upper",
            "BB_lower",
            "MACD_line",
            "MACD_signal",
            "MACD_histogram",
            "Stoch_K",
            "Stoch_D",
        ]

        for indicator in expected_indicators:
            self.assertIn(indicator, result.columns)

    def test_add_all_indicators_missing_ohlc(self):
        """测试添加所有指标（缺少OHLC数据）"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        # 只有close价格的数据
        simple_data = pd.DataFrame({"close": self.prices})

        result = TechnicalIndicators.add_all_indicators(simple_data, price_column="close")

        self.assertIsInstance(result, pd.DataFrame)

        # 应该包含基本指标但不包含随机震荡指标
        basic_indicators = [
            "MA_5",
            "MA_10",
            "MA_20",
            "MA_50",
            "MA_200",
            "EMA_5",
            "EMA_10",
            "EMA_20",
            "EMA_50",
            "EMA_200",
            "RSI_14",
            "BB_middle",
            "BB_upper",
            "BB_lower",
            "MACD_line",
            "MACD_signal",
            "MACD_histogram",
        ]

        for indicator in basic_indicators:
            self.assertIn(indicator, result.columns)

        # 不应该包含随机震荡指标
        self.assertNotIn("Stoch_K", result.columns)
        self.assertNotIn("Stoch_D", result.columns)

    def test_add_all_indicators_invalid_column(self):
        """测试添加所有指标时的无效列"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        with self.assertRaises(ValueError) as context:
            TechnicalIndicators.add_all_indicators(self.ohlcv_data, price_column="invalid")

        self.assertIn("不存在于DataFrame中", str(context.exception))


class TestVolatilityIndicators(unittest.TestCase):
    """测试 VolatilityIndicators 类"""

    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        base_price = 100
        price_changes = np.random.randn(100) * 0.02
        prices = [base_price]

        for change in price_changes[1:]:
            prices.append(prices[-1] * (1 + change))

        self.prices = pd.Series(prices, index=dates)

        # 创建OHLC数据
        self.ohlc_data = pd.DataFrame(
            {
                "high": self.prices * (1 + abs(np.random.randn(100)) * 0.01),
                "low": self.prices * (1 - abs(np.random.randn(100)) * 0.01),
                "close": self.prices,
            },
            index=dates,
        )

    def test_historical_volatility_calculation(self):
        """测试历史波动率计算"""
        from src.data.indicators.technical_analysis import VolatilityIndicators

        vol = VolatilityIndicators.historical_volatility(self.prices, window=20, trading_days=252)

        self.assertIsInstance(vol, pd.Series)
        self.assertEqual(len(vol), len(self.prices))

        # 波动率应该为正值
        valid_vol = vol.dropna()
        if len(valid_vol) > 0:
            self.assertTrue(all(val >= 0 for val in valid_vol))

    def test_atr_calculation(self):
        """测试ATR计算"""
        from src.data.indicators.technical_analysis import VolatilityIndicators

        atr = VolatilityIndicators.atr(
            self.ohlc_data["high"], self.ohlc_data["low"], self.ohlc_data["close"], window=14
        )

        self.assertIsInstance(atr, pd.Series)
        self.assertEqual(len(atr), len(self.ohlc_data))

        # ATR应该为正值
        valid_atr = atr.dropna()
        if len(valid_atr) > 0:
            self.assertTrue(all(val >= 0 for val in valid_atr))

    def test_vix_like_indicator_calculation(self):
        """测试VIX类似指标计算"""
        from src.data.indicators.technical_analysis import VolatilityIndicators

        vix = VolatilityIndicators.vix_like_indicator(self.prices, window=30)

        self.assertIsInstance(vix, pd.Series)
        self.assertEqual(len(vix), len(self.prices))

        # VIX指标应该为正值
        valid_vix = vix.dropna()
        if len(valid_vix) > 0:
            self.assertTrue(all(val >= 0 for val in valid_vix))


class TestReturnAnalysis(unittest.TestCase):
    """测试 ReturnAnalysis 类"""

    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        base_price = 100
        price_changes = np.random.randn(100) * 0.02
        prices = [base_price]

        for change in price_changes[1:]:
            prices.append(prices[-1] * (1 + change))

        self.prices = pd.Series(prices, index=dates)

    def test_calculate_returns_simple(self):
        """测试简单收益率计算"""
        from src.data.indicators.technical_analysis import ReturnAnalysis

        returns = ReturnAnalysis.calculate_returns(self.prices, periods=1, method="simple")

        self.assertIsInstance(returns, pd.Series)
        self.assertEqual(len(returns), len(self.prices))

        # 验证第一个值为NaN
        self.assertTrue(pd.isna(returns.iloc[0]))

        # 验证计算逻辑
        expected_return = (self.prices.iloc[1] / self.prices.iloc[0]) - 1
        self.assertAlmostEqual(returns.iloc[1], expected_return, places=10)

    def test_calculate_returns_log(self):
        """测试对数收益率计算"""
        from src.data.indicators.technical_analysis import ReturnAnalysis

        returns = ReturnAnalysis.calculate_returns(self.prices, periods=1, method="log")

        self.assertIsInstance(returns, pd.Series)
        self.assertEqual(len(returns), len(self.prices))

        # 验证第一个值为NaN
        self.assertTrue(pd.isna(returns.iloc[0]))

        # 验证计算逻辑
        expected_return = np.log(self.prices.iloc[1] / self.prices.iloc[0])
        self.assertAlmostEqual(returns.iloc[1], expected_return, places=10)

    def test_calculate_returns_invalid_method(self):
        """测试无效的收益率计算方法"""
        from src.data.indicators.technical_analysis import ReturnAnalysis

        with self.assertRaises(ValueError) as context:
            ReturnAnalysis.calculate_returns(self.prices, periods=1, method="invalid")

        self.assertIn("不支持的收益率计算方法", str(context.exception))

    def test_rolling_returns_simple(self):
        """测试滚动收益率计算（简单）"""
        from src.data.indicators.technical_analysis import ReturnAnalysis

        rolling_returns = ReturnAnalysis.rolling_returns(self.prices, window=5, method="simple")

        self.assertIsInstance(rolling_returns, pd.Series)
        self.assertEqual(len(rolling_returns), len(self.prices))

        # 验证前5个值为NaN
        self.assertTrue(rolling_returns.iloc[:5].isna().all())

    def test_rolling_returns_log(self):
        """测试滚动收益率计算（对数）"""
        from src.data.indicators.technical_analysis import ReturnAnalysis

        rolling_returns = ReturnAnalysis.rolling_returns(self.prices, window=5, method="log")

        self.assertIsInstance(rolling_returns, pd.Series)
        self.assertEqual(len(rolling_returns), len(self.prices))

        # 验证前5个值为NaN
        self.assertTrue(rolling_returns.iloc[:5].isna().all())

    def test_rolling_returns_invalid_method(self):
        """测试无效的滚动收益率计算方法"""
        from src.data.indicators.technical_analysis import ReturnAnalysis

        with self.assertRaises(ValueError) as context:
            ReturnAnalysis.rolling_returns(self.prices, window=5, method="invalid")

        self.assertIn("不支持的收益率计算方法", str(context.exception))

    def test_sharpe_ratio_calculation(self):
        """测试夏普比率计算"""
        from src.data.indicators.technical_analysis import ReturnAnalysis

        # 先计算收益率
        returns = ReturnAnalysis.calculate_returns(self.prices, periods=1, method="simple")

        sharpe = ReturnAnalysis.sharpe_ratio(returns, risk_free_rate=0.02, window=30)

        self.assertIsInstance(sharpe, pd.Series)
        self.assertEqual(len(sharpe), len(returns))

        # 验证前30个值为NaN
        self.assertTrue(sharpe.iloc[:30].isna().all())


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=50, freq="D")
        base_price = 100
        price_changes = np.random.randn(50) * 0.02
        prices = [base_price]

        for change in price_changes[1:]:
            prices.append(prices[-1] * (1 + change))

        self.prices = pd.Series(prices, index=dates)

        self.ohlcv_data = pd.DataFrame(
            {
                "open": self.prices * (1 + np.random.randn(50) * 0.005),
                "high": self.prices * (1 + abs(np.random.randn(50)) * 0.01),
                "low": self.prices * (1 - abs(np.random.randn(50)) * 0.01),
                "close": self.prices,
                "volume": np.random.randint(1000, 10000, 50),
            },
            index=dates,
        )

    def test_add_technical_indicators_function(self):
        """测试便捷函数：add_technical_indicators"""
        from src.data.indicators.technical_analysis import add_technical_indicators

        result = add_technical_indicators(self.ohlcv_data, price_column="close")

        self.assertIsInstance(result, pd.DataFrame)

        # 应该包含技术指标
        expected_indicators = ["MA_5", "EMA_5", "RSI_14", "BB_middle"]
        for indicator in expected_indicators:
            self.assertIn(indicator, result.columns)

    def test_calculate_volatility_function(self):
        """测试便捷函数：calculate_volatility"""
        from src.data.indicators.technical_analysis import calculate_volatility

        vol = calculate_volatility(self.prices, window=20, trading_days=252)

        self.assertIsInstance(vol, pd.Series)
        self.assertEqual(len(vol), len(self.prices))

    def test_calculate_returns_function_simple(self):
        """测试便捷函数：calculate_returns（简单收益率）"""
        from src.data.indicators.technical_analysis import calculate_returns

        returns = calculate_returns(self.prices, periods=1, log_returns=False)

        self.assertIsInstance(returns, pd.Series)
        self.assertEqual(len(returns), len(self.prices))

    def test_calculate_returns_function_log(self):
        """测试便捷函数：calculate_returns（对数收益率）"""
        from src.data.indicators.technical_analysis import calculate_returns

        returns = calculate_returns(self.prices, periods=1, log_returns=True)

        self.assertIsInstance(returns, pd.Series)
        self.assertEqual(len(returns), len(self.prices))


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """测试边界条件和错误处理"""

    def test_empty_series(self):
        """测试空序列"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        empty_series = pd.Series([], dtype=float)

        # 移动平均应该返回空序列
        ma = TechnicalIndicators.moving_average(empty_series, window=10)
        self.assertEqual(len(ma), 0)

    def test_short_series(self):
        """测试短序列"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        short_series = pd.Series([100, 101, 102])

        # 窗口大小大于序列长度
        ma = TechnicalIndicators.moving_average(short_series, window=10)
        self.assertTrue(ma.isna().all())

    def test_series_with_nan(self):
        """测试包含NaN的序列"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        series_with_nan = pd.Series([100, np.nan, 102, 103, 104])

        ma = TechnicalIndicators.moving_average(series_with_nan, window=3)
        self.assertIsInstance(ma, pd.Series)

    def test_zero_division_protection_rsi(self):
        """测试RSI中的零除保护"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        # 创建没有变化的价格序列（会导致零除问题）
        constant_prices = pd.Series([100] * 20)

        rsi = TechnicalIndicators.rsi(constant_prices, window=14)

        # RSI应该能处理这种情况而不抛出异常
        self.assertIsInstance(rsi, pd.Series)

    def test_bollinger_bands_edge_cases(self):
        """测试布林带边界条件"""
        from src.data.indicators.technical_analysis import TechnicalIndicators

        # 测试标准差为0的情况
        constant_prices = pd.Series([100] * 25)

        bb = TechnicalIndicators.bollinger_bands(constant_prices, window=20, std_dev=2.0)

        self.assertIsInstance(bb, dict)
        self.assertIn("BB_middle", bb)
        self.assertIn("BB_upper", bb)
        self.assertIn("BB_lower", bb)


if __name__ == "__main__":
    unittest.main()
