#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moving Average Strategies (移动平均策略)

Implementation of various moving average based trading strategies
"""


import pandas as pd

from .base import CrossoverStrategy, TechnicalIndicatorStrategy


class SimpleMAStrategy(CrossoverStrategy):
    """
    Simple Moving Average Crossover Strategy (简单移动平均交叉策略)

    Generates buy signals when short MA crosses above long MA,
    sell signals when short MA crosses below long MA
    """

    def __init__(self, short_window: int = 10, long_window: int = 50, column: str = "close"):
        """
        Initialize SMA strategy

        Args:
            short_window: Short MA period
            long_window: Long MA period
            column: Price column to use
        """
        parameters = {"short_window": short_window, "long_window": long_window, "column": column}
        super().__init__("SimpleMA", parameters)

        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals using SMA crossover"""
        self.validate_data(data)

        short_window = self.get_parameter("short_window")
        long_window = self.get_parameter("long_window")
        column = self.get_parameter("column")

        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0

        # Calculate moving averages
        signals["short_ma"] = self._calculate_sma(data[column], short_window)
        signals["long_ma"] = self._calculate_sma(data[column], long_window)

        # Generate crossover signals
        signals["signal"] = self._generate_crossover_signals(
            signals["short_ma"], signals["long_ma"]
        )

        return signals


class ExponentialMAStrategy(CrossoverStrategy):
    """
    Exponential Moving Average Crossover Strategy (指数移动平均交叉策略)

    Similar to SMA but uses exponential moving averages for faster response
    """

    def __init__(self, short_window: int = 12, long_window: int = 26, column: str = "close"):
        """
        Initialize EMA strategy

        Args:
            short_window: Short EMA period
            long_window: Long EMA period
            column: Price column to use
        """
        parameters = {"short_window": short_window, "long_window": long_window, "column": column}
        super().__init__("ExponentialMA", parameters)

        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals using EMA crossover"""
        self.validate_data(data)

        short_window = self.get_parameter("short_window")
        long_window = self.get_parameter("long_window")
        column = self.get_parameter("column")

        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0

        # Calculate exponential moving averages
        signals["short_ema"] = self._calculate_ema(data[column], short_window)
        signals["long_ema"] = self._calculate_ema(data[column], long_window)

        # Generate crossover signals
        signals["signal"] = self._generate_crossover_signals(
            signals["short_ema"], signals["long_ema"]
        )

        return signals


class TripleMAStrategy(TechnicalIndicatorStrategy):
    """
    Triple Moving Average Strategy (三重移动平均策略)

    Uses three MAs: fast, medium, slow for more robust signals
    """

    def __init__(
        self,
        fast_window: int = 5,
        medium_window: int = 20,
        slow_window: int = 50,
        column: str = "close",
    ):
        """
        Initialize Triple MA strategy

        Args:
            fast_window: Fast MA period
            medium_window: Medium MA period
            slow_window: Slow MA period
            column: Price column to use
        """
        parameters = {
            "fast_window": fast_window,
            "medium_window": medium_window,
            "slow_window": slow_window,
            "column": column,
        }
        super().__init__("TripleMA", parameters)

        if not (fast_window < medium_window < slow_window):
            raise ValueError("Windows must be in ascending order: fast < medium < slow")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate signals using triple MA alignment"""
        self.validate_data(data)

        fast_window = self.get_parameter("fast_window")
        medium_window = self.get_parameter("medium_window")
        slow_window = self.get_parameter("slow_window")
        column = self.get_parameter("column")

        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0

        # Calculate all three MAs
        signals["fast_ma"] = self._calculate_sma(data[column], fast_window)
        signals["medium_ma"] = self._calculate_sma(data[column], medium_window)
        signals["slow_ma"] = self._calculate_sma(data[column], slow_window)

        # Bull alignment: fast > medium > slow
        bull_alignment = (signals["fast_ma"] > signals["medium_ma"]) & (
            signals["medium_ma"] > signals["slow_ma"]
        )

        # Bear alignment: fast < medium < slow
        bear_alignment = (signals["fast_ma"] < signals["medium_ma"]) & (
            signals["medium_ma"] < signals["slow_ma"]
        )

        # Signal when alignment changes - 修复：处理NaN值
        # 填充NaN值为False，避免布尔运算错误
        bull_alignment = bull_alignment.fillna(False)
        bear_alignment = bear_alignment.fillna(False)

        bull_entry = bull_alignment & ~bull_alignment.shift(1).fillna(False)
        bear_entry = bear_alignment & ~bear_alignment.shift(1).fillna(False)

        signals.loc[bull_entry, "signal"] = 1
        signals.loc[bear_entry, "signal"] = -1

        return signals


class ImprovedMAStrategy(CrossoverStrategy):
    """
    Improved Moving Average Strategy (改进移动平均策略)

    Enhanced MA strategy with RSI confirmation and volume filter
    """

    def __init__(
        self,
        short_window: int = 10,
        long_window: int = 30,
        rsi_window: int = 14,
        rsi_threshold: int = 50,
        volume_factor: float = 1.5,
        column: str = "close",
    ):
        """
        Initialize improved MA strategy

        Args:
            short_window: Short MA period
            long_window: Long MA period
            rsi_window: RSI calculation period
            rsi_threshold: RSI threshold for confirmation
            volume_factor: Volume multiplier for confirmation
            column: Price column to use
        """
        parameters = {
            "short_window": short_window,
            "long_window": long_window,
            "rsi_window": rsi_window,
            "rsi_threshold": rsi_threshold,
            "volume_factor": volume_factor,
            "column": column,
        }
        super().__init__("ImprovedMA", parameters)

        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate signals with MA crossover + RSI + volume confirmation"""
        self.validate_data(data)

        short_window = self.get_parameter("short_window")
        long_window = self.get_parameter("long_window")
        rsi_window = self.get_parameter("rsi_window")
        rsi_threshold = self.get_parameter("rsi_threshold")
        volume_factor = self.get_parameter("volume_factor")
        column = self.get_parameter("column")

        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0

        # Calculate indicators
        signals["short_ma"] = self._calculate_sma(data[column], short_window)
        signals["long_ma"] = self._calculate_sma(data[column], long_window)
        signals["rsi"] = self._calculate_rsi(data[column], rsi_window)
        signals["volume_ma"] = self._calculate_sma(data["volume"], 20)

        # Basic MA crossover signals
        basic_signals = self._generate_crossover_signals(signals["short_ma"], signals["long_ma"])

        # Enhanced signal logic with confirmations
        for i in range(len(signals)):
            basic_signal = basic_signals.iloc[i]

            if basic_signal == 0:
                continue

            # Get current values
            current_rsi = signals["rsi"].iloc[i]
            current_volume = data["volume"].iloc[i]
            avg_volume = signals["volume_ma"].iloc[i]

            # Skip if not enough data
            if pd.isna(current_rsi) or pd.isna(avg_volume):
                continue

            # Apply filters
            rsi_confirm = True
            volume_confirm = current_volume > (avg_volume * volume_factor)

            if basic_signal == 1:  # Buy signal
                rsi_confirm = current_rsi < rsi_threshold  # Not overbought
            elif basic_signal == -1:  # Sell signal
                rsi_confirm = current_rsi > rsi_threshold  # Not oversold

            # Only generate signal if all confirmations pass
            if rsi_confirm and volume_confirm:
                signals.iloc[i, signals.columns.get_loc("signal")] = basic_signal

        return signals
