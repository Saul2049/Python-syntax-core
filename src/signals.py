#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号处理模块 (Signal Processing Module)

向后兼容的导入文件，将原有功能重定向到新的模块化实现
"""

import warnings

# 从新的模块化实现导入所有功能，保持向后兼容
from src.indicators.cross_signals import (
    bearish_cross_indices,
    bearish_cross_series,
    bullish_cross_indices,
    bullish_cross_series,
    crossover,
    crossunder,
    vectorized_cross,
)
from src.indicators.momentum_indicators import momentum, rate_of_change, zscore
from src.indicators.moving_averages import (
    moving_average,
)
from src.indicators.volatility_indicators import (
    bollinger_bands,
)

# 发出弃用警告
warnings.warn(
    "直接从 src.signals 导入已弃用。请使用 src.indicators 中的模块化导入。\n"
    "例如: from src.indicators import crossover, moving_average",
    DeprecationWarning,
    stacklevel=2,
)

# 为了完全兼容，保留所有原有的函数名
__all__ = [
    "crossover",
    "crossunder",
    "moving_average",
    "momentum",
    "rate_of_change",
    "zscore",
    "bollinger_bands",
    "vectorized_cross",
    "bullish_cross_indices",
    "bearish_cross_indices",
    "bullish_cross_series",
    "bearish_cross_series",
]
