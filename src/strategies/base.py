#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Strategy Classes (基础策略类)

Provides abstract base classes and common functionality for all trading strategies
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies (所有交易策略的抽象基类)

    This class defines the interface that all strategies must implement
    """

    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize base strategy

        Args:
            name: Strategy name
            parameters: Strategy parameters dictionary
        """
        self.name = name
        self.parameters = parameters or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from price data

        Args:
            data: Price data DataFrame with OHLCV columns

        Returns:
            DataFrame with signals column (-1, 0, 1 for sell, hold, buy)
        """

    @abstractmethod
    def get_required_columns(self) -> list:
        """
        Get list of required columns in input DataFrame

        Returns:
            List of required column names
        """

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data has required columns and format

        Args:
            data: Input DataFrame to validate

        Returns:
            True if data is valid

        Raises:
            ValueError: If data is invalid
        """
        required_columns = self.get_required_columns()
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if data.empty:
            raise ValueError("Input data is empty")

        return True

    def set_parameter(self, name: str, value: Any):
        """Set strategy parameter"""
        self.parameters[name] = value
        self.logger.debug(f"Set parameter {name} = {value}")

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get strategy parameter"""
        return self.parameters.get(name, default)

    def __str__(self) -> str:
        return f"{self.name}({self.parameters})"

    def __repr__(self) -> str:
        return self.__str__()


class TechnicalIndicatorStrategy(BaseStrategy):
    """
    Base class for strategies using technical indicators (技术指标策略基类)

    Provides common functionality for indicator-based strategies
    """

    def __init__(self, name: str = None, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize technical indicator strategy

        Args:
            name: Strategy name (auto-generated if None)
            parameters: Strategy parameters
        """
        if name is None:
            name = self.__class__.__name__
        super().__init__(name, parameters or {})

    def get_required_columns(self) -> list:
        """Most technical strategies need OHLCV data"""
        return ["open", "high", "low", "close", "volume"]

    def _safe_divide(
        self, numerator: Union[pd.Series, float], denominator: Union[pd.Series, float]
    ) -> pd.Series:
        """
        Safe division that handles zero denominators

        Args:
            numerator: Numerator values
            denominator: Denominator values

        Returns:
            Result of division with NaN for zero denominators
        """
        if isinstance(numerator, (int, float)) and isinstance(denominator, (int, float)):
            return numerator / denominator if denominator != 0 else float("nan")

        # For pandas Series
        result = numerator / denominator
        return result.fillna(0)  # or however you want to handle NaN values

    def _calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()

    def _calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period).mean()

    def _calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index

        Args:
            data: Price series
            period: RSI period

        Returns:
            RSI values
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = self._safe_divide(gain, loss)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_bollinger_bands(
        self, data: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands

        Args:
            data: Price series
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Dictionary with 'upper', 'middle', 'lower' bands
        """
        middle = self._calculate_sma(data, period)
        std = data.rolling(window=period).std()

        return {
            "upper": middle + (std * std_dev),
            "middle": middle,
            "lower": middle - (std * std_dev),
        }


class CrossoverStrategy(TechnicalIndicatorStrategy):
    """
    Base class for crossover-based strategies (交叉策略基类)

    Handles common crossover signal generation logic
    """

    def _generate_crossover_signals(self, fast_line: pd.Series, slow_line: pd.Series) -> pd.Series:
        """
        Generate signals based on line crossovers

        Args:
            fast_line: Fast moving line (e.g., short MA)
            slow_line: Slow moving line (e.g., long MA)

        Returns:
            Signal series: 1 for buy, -1 for sell, 0 for hold
        """
        signals = pd.Series(0, index=fast_line.index)

        # Buy signal: fast line crosses above slow line
        buy_condition = (fast_line > slow_line) & (fast_line.shift(1) <= slow_line.shift(1))
        signals.loc[buy_condition] = 1

        # Sell signal: fast line crosses below slow line
        sell_condition = (fast_line < slow_line) & (fast_line.shift(1) >= slow_line.shift(1))
        signals.loc[sell_condition] = -1

        return signals


class MeanReversionStrategy(TechnicalIndicatorStrategy):
    """
    Base class for mean reversion strategies (均值回归策略基类)

    Handles common mean reversion logic
    """

    def _generate_mean_reversion_signals(
        self,
        price: pd.Series,
        mean_line: pd.Series,
        upper_threshold: pd.Series,
        lower_threshold: pd.Series,
    ) -> pd.Series:
        """
        Generate mean reversion signals

        Args:
            price: Current price series
            mean_line: Mean/center line
            upper_threshold: Upper boundary for selling
            lower_threshold: Lower boundary for buying

        Returns:
            Signal series: 1 for buy, -1 for sell, 0 for hold
        """
        signals = pd.Series(0, index=price.index)

        # Buy signal: price touches lower threshold
        buy_condition = (price <= lower_threshold) & (price.shift(1) > lower_threshold.shift(1))
        signals.loc[buy_condition] = 1

        # Sell signal: price touches upper threshold
        sell_condition = (price >= upper_threshold) & (price.shift(1) < upper_threshold.shift(1))
        signals.loc[sell_condition] = -1

        return signals
