#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标包 (Technical Indicators Package)

将信号处理功能模块化，提供更好的代码组织和复用性
"""

from .cross_signals import (
    bearish_cross_indices,
    bearish_cross_series,
    bullish_cross_indices,
    bullish_cross_series,
    crossover,
    crossunder,
    vectorized_cross,
)
from .momentum_indicators import momentum, rate_of_change, zscore
from .moving_averages import (
    exponential_moving_average,
    moving_average,
    simple_moving_average,
    weighted_moving_average,
)
from .volatility_indicators import average_true_range, bollinger_bands, standard_deviation

# 向后兼容 - 导出所有原始函数
__all__ = [
    # 交叉信号
    "crossover",
    "crossunder",
    "vectorized_cross",
    "bullish_cross_indices",
    "bearish_cross_indices",
    "bullish_cross_series",
    "bearish_cross_series",
    # 移动平均
    "moving_average",
    "simple_moving_average",
    "exponential_moving_average",
    "weighted_moving_average",
    # 动量指标
    "momentum",
    "rate_of_change",
    "zscore",
    # 波动率指标
    "bollinger_bands",
    "average_true_range",
    "standard_deviation",
]
