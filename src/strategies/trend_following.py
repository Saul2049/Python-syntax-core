#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势跟踪策略模块 (Trend Following Strategies Module)

实现基于趋势跟踪的交易策略，包括Supertrend、多时间框架等
"""

import pandas as pd

from .base import TechnicalIndicatorStrategy


class TrendFollowingStrategy(TechnicalIndicatorStrategy):
    """基础趋势跟踪策略 - 基于移动平均和ATR的趋势跟踪"""

    def __init__(self, ma_window: int = 20, atr_window: int = 14, multiplier: float = 2.0):
        super().__init__()
        self.ma_window = ma_window
        self.atr_window = atr_window
        self.multiplier = multiplier

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算趋势跟踪指标"""
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 计算移动平均
        ma = close.rolling(window=self.ma_window).mean()

        # 计算ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.atr_window).mean()

        # 计算趋势带
        upper_trend = ma + (atr * self.multiplier)
        lower_trend = ma - (atr * self.multiplier)

        result = data.copy()
        result["ma"] = ma
        result["atr"] = atr
        result["upper_trend"] = upper_trend
        result["lower_trend"] = lower_trend
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成趋势跟踪交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        close = data_with_indicators["close"]
        ma = data_with_indicators["ma"]
        upper_trend = data_with_indicators["upper_trend"]
        lower_trend = data_with_indicators["lower_trend"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 趋势确认：价格在MA之上且突破上趋势带
        uptrend = (close > ma) & (close > upper_trend)
        signals[uptrend] = 1

        # 趋势反转：价格在MA之下且跌破下趋势带
        downtrend = (close < ma) & (close < lower_trend)
        signals[downtrend] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class SupertrendStrategy(TechnicalIndicatorStrategy):
    """Supertrend策略 - 基于Supertrend指标的趋势跟踪策略"""

    def __init__(self, atr_period: int = 10, multiplier: float = 3.0):
        super().__init__()
        self.atr_period = atr_period
        self.multiplier = multiplier

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算Supertrend指标"""
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 计算ATR和基础轨道
        atr, basic_upper, basic_lower = self._calculate_atr_and_basic_bands(high, low, close)

        # 计算最终上下轨
        final_upper, final_lower = self._calculate_final_bands(basic_upper, basic_lower, close)

        # 计算Supertrend和趋势
        supertrend, trend = self._calculate_supertrend(final_upper, final_lower, close)

        # 组装结果
        return self._build_result_dataframe(
            data, atr, basic_upper, basic_lower, final_upper, final_lower, supertrend, trend
        )

    def _calculate_atr_and_basic_bands(self, high: pd.Series, low: pd.Series, close: pd.Series):
        """计算ATR和基础上下轨"""
        # 计算ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.atr_period).mean()

        # 计算基础上下轨
        hl2 = (high + low) / 2
        basic_upper = hl2 + (self.multiplier * atr)
        basic_lower = hl2 - (self.multiplier * atr)

        return atr, basic_upper, basic_lower

    def _calculate_final_bands(
        self, basic_upper: pd.Series, basic_lower: pd.Series, close: pd.Series
    ):
        """计算最终上下轨"""
        final_upper = pd.Series(index=basic_upper.index, dtype=float)
        final_lower = pd.Series(index=basic_lower.index, dtype=float)

        for i in range(len(basic_upper)):
            if i == 0:
                final_upper.iloc[i] = basic_upper.iloc[i]
                final_lower.iloc[i] = basic_lower.iloc[i]
            else:
                final_upper.iloc[i] = self._calculate_final_upper_band(
                    basic_upper, final_upper, close, i
                )
                final_lower.iloc[i] = self._calculate_final_lower_band(
                    basic_lower, final_lower, close, i
                )

        return final_upper, final_lower

    def _calculate_final_upper_band(
        self, basic_upper: pd.Series, final_upper: pd.Series, close: pd.Series, i: int
    ) -> float:
        """计算单个时点的最终上轨"""
        if (
            basic_upper.iloc[i] < final_upper.iloc[i - 1]
            or close.iloc[i - 1] > final_upper.iloc[i - 1]
        ):
            return basic_upper.iloc[i]
        else:
            return final_upper.iloc[i - 1]

    def _calculate_final_lower_band(
        self, basic_lower: pd.Series, final_lower: pd.Series, close: pd.Series, i: int
    ) -> float:
        """计算单个时点的最终下轨"""
        if (
            basic_lower.iloc[i] > final_lower.iloc[i - 1]
            or close.iloc[i - 1] < final_lower.iloc[i - 1]
        ):
            return basic_lower.iloc[i]
        else:
            return final_lower.iloc[i - 1]

    def _calculate_supertrend(
        self, final_upper: pd.Series, final_lower: pd.Series, close: pd.Series
    ):
        """计算Supertrend指标和趋势"""
        supertrend = pd.Series(index=close.index, dtype=float)
        trend = pd.Series(index=close.index, dtype=int)

        for i in range(len(close)):
            if i == 0:
                supertrend.iloc[i] = final_upper.iloc[i]
                trend.iloc[i] = -1
            else:
                supertrend_value, trend_value = self._calculate_supertrend_point(
                    final_upper, final_lower, close, supertrend, trend, i
                )
                supertrend.iloc[i] = supertrend_value
                trend.iloc[i] = trend_value

        return supertrend, trend

    def _calculate_supertrend_point(
        self,
        final_upper: pd.Series,
        final_lower: pd.Series,
        close: pd.Series,
        supertrend: pd.Series,
        trend: pd.Series,
        i: int,
    ):
        """计算单个时点的Supertrend值和趋势"""
        if close.iloc[i] <= final_lower.iloc[i]:
            return final_lower.iloc[i], -1
        elif close.iloc[i] >= final_upper.iloc[i]:
            return final_upper.iloc[i], 1
        else:
            return supertrend.iloc[i - 1], trend.iloc[i - 1]

    def _build_result_dataframe(
        self,
        data: pd.DataFrame,
        atr: pd.Series,
        basic_upper: pd.Series,
        basic_lower: pd.Series,
        final_upper: pd.Series,
        final_lower: pd.Series,
        supertrend: pd.Series,
        trend: pd.Series,
    ) -> pd.DataFrame:
        """构建包含所有指标的结果DataFrame"""
        result = data.copy()
        result["atr"] = atr
        result["basic_upper"] = basic_upper
        result["basic_lower"] = basic_lower
        result["final_upper"] = final_upper
        result["final_lower"] = final_lower
        result["supertrend"] = supertrend
        result["trend"] = trend
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成Supertrend交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        data_with_indicators["close"]
        data_with_indicators["supertrend"]
        trend = data_with_indicators["trend"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 趋势变化信号
        trend_change = trend.diff()

        # 从下跌转为上涨
        signals[trend_change == 2] = 1

        # 从上涨转为下跌
        signals[trend_change == -2] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class MultiTimeframeStrategy(TechnicalIndicatorStrategy):
    """多时间框架策略 - 结合多个时间框架的趋势分析"""

    def __init__(self, short_window: int = 10, medium_window: int = 20, long_window: int = 50):
        super().__init__()
        self.short_window = short_window
        self.medium_window = medium_window
        self.long_window = long_window

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算多时间框架指标"""
        close = data["close"]

        # 计算不同周期的移动平均
        ma_short = close.rolling(window=self.short_window).mean()
        ma_medium = close.rolling(window=self.medium_window).mean()
        ma_long = close.rolling(window=self.long_window).mean()

        result = data.copy()
        result["ma_short"] = ma_short
        result["ma_medium"] = ma_medium
        result["ma_long"] = ma_long
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成多时间框架交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        close = data_with_indicators["close"]
        ma_short = data_with_indicators["ma_short"]
        ma_medium = data_with_indicators["ma_medium"]
        ma_long = data_with_indicators["ma_long"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 多重确认的买入信号
        bullish_alignment = (ma_short > ma_medium) & (ma_medium > ma_long) & (close > ma_short)
        signals[bullish_alignment] = 1

        # 多重确认的卖出信号
        bearish_alignment = (ma_short < ma_medium) & (ma_medium < ma_long) & (close < ma_short)
        signals[bearish_alignment] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class AdaptiveMovingAverageStrategy(TechnicalIndicatorStrategy):
    """自适应移动平均策略 - 基于波动率自适应调整的移动平均策略"""

    def __init__(self, window: int = 20, volatility_window: int = 10):
        super().__init__()
        self.window = window
        self.volatility_window = volatility_window

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算自适应移动平均指标"""
        close = data["close"]

        # 计算波动率
        returns = close.pct_change()
        volatility = returns.rolling(window=self.volatility_window).std()

        # 标准化波动率作为调整因子
        volatility_normalized = (volatility - volatility.rolling(window=50).min()) / (
            volatility.rolling(window=50).max() - volatility.rolling(window=50).min()
        )

        # 自适应窗口：高波动率时使用短窗口，低波动率时使用长窗口
        adaptive_window = self.window * (1 - volatility_normalized * 0.5)
        adaptive_window = adaptive_window.fillna(self.window).clip(lower=5, upper=self.window * 2)

        # 计算自适应移动平均
        adaptive_ma = pd.Series(index=data.index, dtype=float)
        for i in range(len(data)):
            if i >= self.window:
                window_size = int(adaptive_window.iloc[i])
                start_idx = max(0, i - window_size + 1)
                adaptive_ma.iloc[i] = close.iloc[start_idx:(i + 1)].mean()
            else:
                adaptive_ma.iloc[i] = close.iloc[: i + 1].mean()

        result = data.copy()
        result["volatility"] = volatility
        result["adaptive_window"] = adaptive_window
        result["adaptive_ma"] = adaptive_ma
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成自适应移动平均交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        close = data_with_indicators["close"]
        adaptive_ma = data_with_indicators["adaptive_ma"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 价格上穿自适应MA买入
        bullish_cross = (close > adaptive_ma) & (close.shift(1) <= adaptive_ma.shift(1))
        signals[bullish_cross] = 1

        # 价格下穿自适应MA卖出
        bearish_cross = (close < adaptive_ma) & (close.shift(1) >= adaptive_ma.shift(1))
        signals[bearish_cross] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result
