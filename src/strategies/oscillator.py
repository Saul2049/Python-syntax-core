#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
振荡器策略模块 (Oscillator Strategies Module)

实现基于各种振荡器指标的交易策略
"""

import pandas as pd

from .base import TechnicalIndicatorStrategy


class RSIStrategy(TechnicalIndicatorStrategy):
    """RSI策略 - 基于相对强弱指标的交易策略"""

    def __init__(
        self, window: int = 14, overbought: float = 70, oversold: float = 30, column: str = "close"
    ):
        super().__init__()
        self.window = window
        self.overbought = overbought
        self.oversold = oversold
        self.column = column

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算RSI指标"""
        close = data[self.column]
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.window).mean()

        # 处理除零问题
        rs = gain / loss.replace(0, float("inf"))
        rsi = 100 - (100 / (1 + rs))

        # 处理特殊情况
        rsi = rsi.fillna(50)  # 当没有足够数据时，RSI设为中性值50
        rsi = rsi.clip(0, 100)  # 确保RSI在0-100范围内

        result = data.copy()
        result["rsi"] = rsi
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成RSI交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        rsi = data_with_indicators["rsi"]

        # 生成信号
        signals = pd.Series(0, index=data.index)
        signals[rsi < self.oversold] = 1  # 超卖买入
        signals[rsi > self.overbought] = -1  # 超买卖出

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class MACDStrategy(TechnicalIndicatorStrategy):
    """MACD策略 - 基于MACD指标的交易策略"""

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        close = data["close"]

        # 计算快速和慢速EMA
        ema_fast = close.ewm(span=self.fast_period).mean()
        ema_slow = close.ewm(span=self.slow_period).mean()

        # 计算MACD线和信号线
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=self.signal_period).mean()
        macd_histogram = macd - macd_signal

        result = data.copy()
        result["macd"] = macd
        result["macd_signal"] = macd_signal
        result["macd_histogram"] = macd_histogram
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成MACD交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        macd = data_with_indicators["macd"]
        macd_signal = data_with_indicators["macd_signal"]

        # 生成信号：MACD线上穿信号线买入，下穿卖出
        signals = pd.Series(0, index=data.index)

        # 上穿买入
        bullish_cross = (macd > macd_signal) & (macd.shift(1) <= macd_signal.shift(1))
        signals[bullish_cross] = 1

        # 下穿卖出
        bearish_cross = (macd < macd_signal) & (macd.shift(1) >= macd_signal.shift(1))
        signals[bearish_cross] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class StochasticStrategy(TechnicalIndicatorStrategy):
    """随机指标策略 - 基于Stochastic振荡器的交易策略"""

    def __init__(
        self, k_period: int = 14, d_period: int = 3, overbought: float = 80, oversold: float = 20
    ):
        super().__init__()
        self.k_period = k_period
        self.d_period = d_period
        self.overbought = overbought
        self.oversold = oversold

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算Stochastic指标"""
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 计算%K
        lowest_low = low.rolling(window=self.k_period).min()
        highest_high = high.rolling(window=self.k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))

        # 计算%D
        d_percent = k_percent.rolling(window=self.d_period).mean()

        result = data.copy()
        result["stoch_k"] = k_percent
        result["stoch_d"] = d_percent
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成Stochastic交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        stoch_k = data_with_indicators["stoch_k"]
        stoch_d = data_with_indicators["stoch_d"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # %K上穿%D且在超卖区域时买入
        bullish_cross = (stoch_k > stoch_d) & (stoch_k.shift(1) <= stoch_d.shift(1))
        oversold_condition = (stoch_k < self.oversold) | (stoch_d < self.oversold)
        signals[bullish_cross & oversold_condition] = 1

        # %K下穿%D且在超买区域时卖出
        bearish_cross = (stoch_k < stoch_d) & (stoch_k.shift(1) >= stoch_d.shift(1))
        overbought_condition = (stoch_k > self.overbought) | (stoch_d > self.overbought)
        signals[bearish_cross & overbought_condition] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class WilliamsRStrategy(TechnicalIndicatorStrategy):
    """Williams %R策略 - 基于Williams %R指标的交易策略"""

    def __init__(self, period: int = 14, overbought: float = -20, oversold: float = -80):
        super().__init__()
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算Williams %R指标"""
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 计算Williams %R
        highest_high = high.rolling(window=self.period).max()
        lowest_low = low.rolling(window=self.period).min()
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))

        result = data.copy()
        result["williams_r"] = williams_r
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成Williams %R交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        williams_r = data_with_indicators["williams_r"]

        # 生成信号
        signals = pd.Series(0, index=data.index)
        signals[williams_r < self.oversold] = 1  # 超卖买入
        signals[williams_r > self.overbought] = -1  # 超买卖出

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result
