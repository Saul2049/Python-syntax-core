#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
突破策略模块 (Breakout Strategies Module)

实现基于价格突破的交易策略，包括布林带突破、通道突破等
"""

import pandas as pd

from .base import TechnicalIndicatorStrategy


class BollingerBreakoutStrategy(TechnicalIndicatorStrategy):
    """布林带突破策略 - 基于价格突破布林带上下轨的交易策略"""

    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__()
        self.window = window
        self.num_std = num_std

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算布林带指标"""
        close = data["close"]

        # 计算布林带
        middle_band = close.rolling(window=self.window).mean()
        std_dev = close.rolling(window=self.window).std()
        upper_band = middle_band + (std_dev * self.num_std)
        lower_band = middle_band - (std_dev * self.num_std)

        result = data.copy()
        result["upper_band"] = upper_band
        result["middle_band"] = middle_band
        result["lower_band"] = lower_band
        result["bb_width"] = (upper_band - lower_band) / middle_band
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成布林带突破交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        close = data_with_indicators["close"]
        upper_band = data_with_indicators["upper_band"]
        lower_band = data_with_indicators["lower_band"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 突破上轨买入
        upper_breakout = close > upper_band
        signals[upper_breakout] = 1

        # 跌破下轨卖出
        lower_breakdown = close < lower_band
        signals[lower_breakdown] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class BollingerMeanReversionStrategy(TechnicalIndicatorStrategy):
    """布林带均值回归策略 - 基于价格回归到均线的交易策略"""

    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__()
        self.window = window
        self.num_std = num_std

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算布林带指标"""
        close = data["close"]

        # 计算布林带
        middle_band = close.rolling(window=self.window).mean()
        std_dev = close.rolling(window=self.window).std()
        upper_band = middle_band + (std_dev * self.num_std)
        lower_band = middle_band - (std_dev * self.num_std)

        result = data.copy()
        result["upper_band"] = upper_band
        result["middle_band"] = middle_band
        result["lower_band"] = lower_band
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成布林带均值回归交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        close = data_with_indicators["close"]
        upper_band = data_with_indicators["upper_band"]
        lower_band = data_with_indicators["lower_band"]
        data_with_indicators["middle_band"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 触及下轨买入（预期反弹）
        oversold = close <= lower_band
        signals[oversold] = 1

        # 触及上轨卖出（预期回调）
        overbought = close >= upper_band
        signals[overbought] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class ChannelBreakoutStrategy(TechnicalIndicatorStrategy):
    """通道突破策略 - 基于价格突破通道的交易策略"""

    def __init__(self, channel_period: int = 20):
        super().__init__()
        self.channel_period = channel_period

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算通道指标"""
        high = data["high"]
        low = data["low"]

        # 计算通道上下轨
        channel_high = high.rolling(window=self.channel_period).max()
        channel_low = low.rolling(window=self.channel_period).min()

        result = data.copy()
        result["channel_high"] = channel_high
        result["channel_low"] = channel_low
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成通道突破交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        close = data_with_indicators["close"]
        channel_high = data_with_indicators["channel_high"]
        channel_low = data_with_indicators["channel_low"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 突破通道上轨买入
        upper_breakout = close > channel_high.shift(1)
        signals[upper_breakout] = 1

        # 跌破通道下轨卖出
        lower_breakdown = close < channel_low.shift(1)
        signals[lower_breakdown] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class DonchianChannelStrategy(TechnicalIndicatorStrategy):
    """唐奇安通道策略 - 基于Donchian Channel的突破策略"""

    def __init__(self, entry_period: int = 20, exit_period: int = 10):
        super().__init__()
        self.entry_period = entry_period
        self.exit_period = exit_period

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算唐奇安通道指标"""
        high = data["high"]
        low = data["low"]

        # 入场通道
        entry_high = high.rolling(window=self.entry_period).max()
        entry_low = low.rolling(window=self.entry_period).min()

        # 出场通道
        exit_high = high.rolling(window=self.exit_period).max()
        exit_low = low.rolling(window=self.exit_period).min()

        result = data.copy()
        result["entry_high"] = entry_high
        result["entry_low"] = entry_low
        result["exit_high"] = exit_high
        result["exit_low"] = exit_low
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成唐奇安通道交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        close = data_with_indicators["close"]
        entry_high = data_with_indicators["entry_high"]
        entry_low = data_with_indicators["entry_low"]
        data_with_indicators["exit_high"]
        data_with_indicators["exit_low"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 突破入场高点买入
        long_entry = close > entry_high.shift(1)
        signals[long_entry] = 1

        # 跌破入场低点卖出
        short_entry = close < entry_low.shift(1)
        signals[short_entry] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result


class ATRBreakoutStrategy(TechnicalIndicatorStrategy):
    """ATR突破策略 - 基于ATR动态调整的突破策略"""

    def __init__(self, atr_period: int = 14, ma_period: int = 20, multiplier: float = 2.0):
        super().__init__()
        self.atr_period = atr_period
        self.ma_period = ma_period
        self.multiplier = multiplier

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算ATR相关指标"""
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 计算ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.atr_period).mean()

        # 计算移动平均
        ma = close.rolling(window=self.ma_period).mean()

        # 计算ATR带
        upper_atr = ma + (atr * self.multiplier)
        lower_atr = ma - (atr * self.multiplier)

        result = data.copy()
        result["atr"] = atr
        result["ma"] = ma
        result["upper_atr"] = upper_atr
        result["lower_atr"] = lower_atr
        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成ATR突破交易信号"""
        data_with_indicators = self.calculate_indicators(data)
        close = data_with_indicators["close"]
        upper_atr = data_with_indicators["upper_atr"]
        lower_atr = data_with_indicators["lower_atr"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 突破ATR上轨买入
        upper_breakout = close > upper_atr
        signals[upper_breakout] = 1

        # 跌破ATR下轨卖出
        lower_breakdown = close < lower_atr
        signals[lower_breakdown] = -1

        result = data_with_indicators.copy()
        result["signal"] = signals
        return result
