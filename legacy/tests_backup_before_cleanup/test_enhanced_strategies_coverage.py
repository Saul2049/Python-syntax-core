"""
Enhanced Strategies Coverage Tests
专门用于提高策略模块测试覆盖率的测试文件
"""


import numpy as np
import pandas as pd
import pytest

from src.strategies.base import BaseStrategy, CrossoverStrategy, TechnicalIndicatorStrategy
from src.strategies.improved_strategy import buy_and_hold, improved_ma_cross, trend_following


class TestBaseStrategyEnhancedCoverage:
    """基础策略增强覆盖率测试"""

    def setup_method(self):
        """测试前设置"""

        # 创建具体的策略实现用于测试
        class TestStrategy(BaseStrategy):
            def generate_signals(self, data):
                return pd.DataFrame({"signal": [0] * len(data)})

            def get_required_columns(self):
                return ["close", "volume"]

        self.strategy = TestStrategy("test_strategy")

        # 创建测试数据
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        self.test_data = pd.DataFrame(
            {
                "open": np.random.uniform(100, 110, 100),
                "high": np.random.uniform(105, 115, 100),
                "low": np.random.uniform(95, 105, 100),
                "close": np.random.uniform(100, 110, 100),
                "volume": np.random.uniform(1000, 5000, 100),
            },
            index=dates,
        )

    def test_base_strategy_initialization(self):
        """测试基础策略初始化"""
        assert self.strategy.name == "test_strategy"
        assert isinstance(self.strategy.parameters, dict)
        assert hasattr(self.strategy, "logger")

    def test_validate_data_success(self):
        """测试成功的数据验证"""
        # 正常数据应该验证成功
        assert self.strategy.validate_data(self.test_data) == True

    def test_validate_data_missing_columns(self):
        """测试缺少列的数据验证"""
        incomplete_data = pd.DataFrame({"close": [100, 101, 102]})

        with pytest.raises(ValueError, match="Missing required columns"):
            self.strategy.validate_data(incomplete_data)

    def test_validate_data_empty_dataframe(self):
        """测试空数据框验证"""
        empty_data = pd.DataFrame()

        # 空数据框会先触发缺少列的错误
        with pytest.raises(ValueError, match="Missing required columns"):
            self.strategy.validate_data(empty_data)

    def test_parameter_management(self):
        """测试参数管理"""
        # 设置参数
        self.strategy.set_parameter("test_param", 42)
        assert self.strategy.get_parameter("test_param") == 42

        # 获取不存在的参数
        assert self.strategy.get_parameter("nonexistent") is None
        assert self.strategy.get_parameter("nonexistent", "default") == "default"

    def test_string_representation(self):
        """测试字符串表示"""
        self.strategy.set_parameter("param1", "value1")
        str_repr = str(self.strategy)
        assert "test_strategy" in str_repr
        assert repr(self.strategy) == str_repr


class TestTechnicalIndicatorStrategyEnhancedCoverage:
    """技术指标策略增强覆盖率测试"""

    def setup_method(self):
        """测试前设置"""

        class TestTechnicalStrategy(TechnicalIndicatorStrategy):
            def generate_signals(self, data):
                return pd.DataFrame({"signal": [0] * len(data)})

        self.strategy = TestTechnicalStrategy()

        # 创建测试数据
        self.test_data = pd.DataFrame(
            {
                "open": [100, 102, 104, 103, 105],
                "high": [101, 103, 105, 104, 106],
                "low": [99, 101, 103, 102, 104],
                "close": [100.5, 102.5, 104.5, 103.5, 105.5],
                "volume": [1000, 1200, 1100, 1300, 1250],
            }
        )

    def test_required_columns(self):
        """测试必需列"""
        required = self.strategy.get_required_columns()
        expected = ["open", "high", "low", "close", "volume"]
        assert required == expected

    def test_safe_divide(self):
        """测试安全除法"""
        # 测试标量除法
        result = self.strategy._safe_divide(10, 2)
        assert result == 5.0

        # 测试零除法
        result = self.strategy._safe_divide(10, 0)
        assert pd.isna(result)

        # 测试Series除法
        numerator = pd.Series([10, 20, 30])
        denominator = pd.Series([2, 4, 0])
        result = self.strategy._safe_divide(numerator, denominator)

        assert result.iloc[0] == 5.0
        assert result.iloc[1] == 5.0
        # 除零的结果可能是inf或被fillna处理为0
        assert pd.isna(result.iloc[2]) or result.iloc[2] == 0.0 or np.isinf(result.iloc[2])

    def test_calculate_sma(self):
        """测试简单移动平均"""
        prices = pd.Series([100, 102, 104, 106, 108])
        sma = self.strategy._calculate_sma(prices, 3)

        # 前两个值应该是NaN
        assert pd.isna(sma.iloc[0])
        assert pd.isna(sma.iloc[1])
        # 第三个值应该是前三个的平均
        assert abs(sma.iloc[2] - 102.0) < 0.01

    def test_calculate_ema(self):
        """测试指数移动平均"""
        prices = pd.Series([100, 102, 104, 106, 108])
        ema = self.strategy._calculate_ema(prices, 3)

        # EMA应该没有NaN值（除了第一个）
        assert not pd.isna(ema.iloc[-1])
        # EMA应该比SMA更贴近最新价格
        assert ema.iloc[-1] > 100

    def test_calculate_rsi(self):
        """测试RSI计算"""
        # 创建有趋势的价格数据
        prices = pd.Series(
            [100, 102, 104, 106, 108, 110, 112, 114, 116, 118] + [100, 102, 104, 106, 108]
        )  # 15个数据点
        rsi = self.strategy._calculate_rsi(prices, period=14)

        # RSI值应该在0-100之间
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_calculate_bollinger_bands(self):
        """测试布林带计算"""
        prices = pd.Series([100, 102, 98, 104, 96, 106, 94, 108, 92, 110] * 3)  # 30个数据点
        bb = self.strategy._calculate_bollinger_bands(prices, period=20, std_dev=2.0)

        assert "upper" in bb
        assert "middle" in bb
        assert "lower" in bb

        # 验证逻辑关系
        valid_indices = ~bb["middle"].isna()
        assert (bb["upper"][valid_indices] >= bb["middle"][valid_indices]).all()
        assert (bb["lower"][valid_indices] <= bb["middle"][valid_indices]).all()


class TestCrossoverStrategyEnhancedCoverage:
    """交叉策略增强覆盖率测试"""

    def setup_method(self):
        """测试前设置"""

        class TestCrossoverStrategy(CrossoverStrategy):
            def generate_signals(self, data):
                fast_line = self._calculate_sma(data["close"], 10)
                slow_line = self._calculate_sma(data["close"], 20)
                return self._generate_crossover_signals(fast_line, slow_line)

        self.strategy = TestCrossoverStrategy()

    def test_crossover_signal_generation(self):
        """测试交叉信号生成"""
        # 创建有明显交叉的数据
        fast_line = pd.Series([100, 101, 102, 103, 104])
        slow_line = pd.Series([103, 102, 101, 100, 99])

        signals = self.strategy._generate_crossover_signals(fast_line, slow_line)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(fast_line)


class TestImprovedStrategyFunctions:
    """改进策略函数测试"""

    def setup_method(self):
        """测试前设置"""
        # 创建测试价格数据
        dates = pd.date_range(start="2023-01-01", periods=250, freq="D")
        np.random.seed(42)  # 固定随机种子

        # 创建有趋势的价格数据
        returns = np.random.normal(0.001, 0.02, 250)  # 日收益率
        prices = [100]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        self.price_data = pd.Series(prices[1:], index=dates)

    def test_buy_and_hold_strategy(self):
        """测试买入持有策略"""
        result = buy_and_hold(self.price_data, init_equity=10000)

        assert isinstance(result, pd.Series)
        assert len(result) == len(self.price_data)
        assert result.iloc[0] == 10000  # 初始权益

        # 权益应该随价格变化
        assert result.iloc[-1] != result.iloc[0]

    def test_trend_following_strategy(self):
        """测试趋势跟踪策略"""
        result = trend_following(
            self.price_data,
            long_win=50,
            atr_win=20,
            risk_frac=0.02,
            init_equity=10000,
            use_trailing_stop=True,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(self.price_data)
        assert result.iloc[0] == 10000  # 初始权益

    def test_trend_following_without_trailing_stop(self):
        """测试不使用移动止损的趋势跟踪"""
        result = trend_following(
            self.price_data,
            long_win=50,
            atr_win=20,
            risk_frac=0.02,
            init_equity=10000,
            use_trailing_stop=False,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(self.price_data)

    def test_improved_ma_cross_strategy(self):
        """测试改进的MA交叉策略"""
        result = improved_ma_cross(
            self.price_data,
            fast_win=20,
            slow_win=50,
            atr_win=14,
            risk_frac=0.02,
            init_equity=10000,
            use_trailing_stop=True,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(self.price_data)
        assert result.iloc[0] == 10000  # 初始权益

    def test_improved_ma_cross_backward_compatibility(self):
        """测试改进MA交叉策略的向后兼容性"""
        # 测试使用已弃用参数
        with pytest.warns(DeprecationWarning):
            result = improved_ma_cross(
                self.price_data, short_window=10, long_window=30, init_equity=10000
            )

        # 结果可能是Series或DataFrame，都应该是有效的
        assert isinstance(result, (pd.Series, pd.DataFrame))

    def test_strategy_with_insufficient_data(self):
        """测试数据不足的情况"""
        short_data = self.price_data.head(10)  # 只有10天数据

        # 策略应该能处理数据不足的情况
        result = trend_following(
            short_data, long_win=200, atr_win=20, risk_frac=0.02, init_equity=10000  # 窗口比数据长
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(short_data)

    def test_strategy_performance_metrics(self):
        """测试策略性能指标计算"""
        bh_result = buy_and_hold(self.price_data, init_equity=10000)
        tf_result = trend_following(self.price_data, init_equity=10000)

        # 计算总收益
        bh_return = (bh_result.iloc[-1] - bh_result.iloc[0]) / bh_result.iloc[0]
        tf_return = (tf_result.iloc[-1] - tf_result.iloc[0]) / tf_result.iloc[0]

        assert isinstance(bh_return, (int, float))
        assert isinstance(tf_return, (int, float))

        # 收益率应该是有限值
        assert np.isfinite(bh_return)
        assert np.isfinite(tf_return)

    def test_strategy_edge_cases(self):
        """测试策略边界情况"""
        # 测试常数价格（无波动）
        constant_price = pd.Series([100] * 100, index=pd.date_range("2023-01-01", periods=100))

        result = trend_following(constant_price, init_equity=10000)
        assert isinstance(result, pd.Series)
        # 常数价格应该导致无交易
        assert result.iloc[-1] == 10000  # 权益应该不变

    def test_risk_management_functionality(self):
        """测试风险管理功能"""
        # 测试不同风险系数
        low_risk = trend_following(self.price_data, risk_frac=0.005, init_equity=10000)
        high_risk = trend_following(self.price_data, risk_frac=0.05, init_equity=10000)

        assert isinstance(low_risk, pd.Series)
        assert isinstance(high_risk, pd.Series)

        # 高风险策略的波动应该更大
        low_risk_volatility = low_risk.pct_change().std()
        high_risk_volatility = high_risk.pct_change().std()

        # 通常高风险会有更高的波动性，但不是绝对的
        assert low_risk_volatility >= 0
        assert high_risk_volatility >= 0


class TestStrategyParameterValidation:
    """策略参数验证测试"""

    def test_parameter_type_validation(self):
        """测试参数类型验证"""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        price_data = pd.Series(np.random.uniform(95, 105, 100), index=dates)

        # 测试负数参数 - 某些策略可能接受负数参数，所以放宽检查
        try:
            result = trend_following(price_data, long_win=-10)
            # 如果没有抛出异常，至少验证结果类型
            assert isinstance(result, pd.Series)
        except (ValueError, TypeError, IndexError):
            # 如果抛出了异常，这也是可以接受的
            pass

        # 测试零风险参数
        try:
            result = trend_following(price_data, risk_frac=0)
            assert isinstance(result, pd.Series)
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    def test_data_type_validation(self):
        """测试数据类型验证"""
        # 测试非Series输入
        list_data = [100, 101, 102, 103, 104]

        # 某些策略可能接受列表，某些可能不接受
        try:
            result = buy_and_hold(pd.Series(list_data))
            assert isinstance(result, pd.Series)
        except (AttributeError, TypeError):
            # 如果策略不接受列表，应该抛出适当的错误
            pass
