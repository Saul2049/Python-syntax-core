#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略包 (Strategies Package)

交易策略的模块化实现，包含各种技术指标策略和交易逻辑
"""

# 基础策略类
from .base import BaseStrategy, CrossoverStrategy, MeanReversionStrategy, TechnicalIndicatorStrategy

# 突破策略
from .breakout import (
    ATRBreakoutStrategy,
    BollingerBreakoutStrategy,
    BollingerMeanReversionStrategy,
    ChannelBreakoutStrategy,
    DonchianChannelStrategy,
)

# 移动平均策略
from .moving_average import (
    ExponentialMAStrategy,
    ImprovedMAStrategy,
    SimpleMAStrategy,
    TripleMAStrategy,
)

# 振荡器策略
from .oscillator import MACDStrategy, RSIStrategy, StochasticStrategy, WilliamsRStrategy

# 趋势跟踪策略
from .trend_following import (
    AdaptiveMovingAverageStrategy,
    MultiTimeframeStrategy,
    SupertrendStrategy,
    TrendFollowingStrategy,
)

# 所有可用策略的列表
ALL_STRATEGIES = [
    # 移动平均策略
    SimpleMAStrategy,
    ExponentialMAStrategy,
    TripleMAStrategy,
    ImprovedMAStrategy,
    # 振荡器策略
    RSIStrategy,
    MACDStrategy,
    StochasticStrategy,
    WilliamsRStrategy,
    # 突破策略
    BollingerBreakoutStrategy,
    BollingerMeanReversionStrategy,
    ChannelBreakoutStrategy,
    DonchianChannelStrategy,
    ATRBreakoutStrategy,
    # 趋势跟踪策略
    TrendFollowingStrategy,
    MultiTimeframeStrategy,
    AdaptiveMovingAverageStrategy,
    SupertrendStrategy,
]

# 按类型分组的策略
STRATEGY_GROUPS = {
    "moving_average": [
        SimpleMAStrategy,
        ExponentialMAStrategy,
        TripleMAStrategy,
        ImprovedMAStrategy,
    ],
    "oscillator": [RSIStrategy, MACDStrategy, StochasticStrategy, WilliamsRStrategy],
    "breakout": [
        BollingerBreakoutStrategy,
        BollingerMeanReversionStrategy,
        ChannelBreakoutStrategy,
        DonchianChannelStrategy,
        ATRBreakoutStrategy,
    ],
    "trend_following": [
        TrendFollowingStrategy,
        MultiTimeframeStrategy,
        AdaptiveMovingAverageStrategy,
        SupertrendStrategy,
    ],
}

# 导出所有策略
__all__ = [
    # 基础类
    "BaseStrategy",
    "TechnicalIndicatorStrategy",
    "CrossoverStrategy",
    "MeanReversionStrategy",
    # 移动平均策略
    "SimpleMAStrategy",
    "ExponentialMAStrategy",
    "TripleMAStrategy",
    "ImprovedMAStrategy",
    # 振荡器策略
    "RSIStrategy",
    "MACDStrategy",
    "StochasticStrategy",
    "WilliamsRStrategy",
    # 突破策略
    "BollingerBreakoutStrategy",
    "BollingerMeanReversionStrategy",
    "ChannelBreakoutStrategy",
    "DonchianChannelStrategy",
    "ATRBreakoutStrategy",
    # 趋势跟踪策略
    "TrendFollowingStrategy",
    "MultiTimeframeStrategy",
    "AdaptiveMovingAverageStrategy",
    "SupertrendStrategy",
    # 策略列表
    "ALL_STRATEGIES",
    "STRATEGY_GROUPS",
]


def get_strategy_by_name(name: str):
    """
    根据名称获取策略类

    参数:
        name: 策略名称

    返回:
        策略类，如果未找到则返回None
    """
    strategy_map = {cls.__name__: cls for cls in ALL_STRATEGIES}
    return strategy_map.get(name)


def list_strategies_by_type(strategy_type: str = None):
    """
    列出指定类型的策略

    参数:
        strategy_type: 策略类型 ('moving_average', 'oscillator', 'breakout', 'trend_following')
                      如果为None，返回所有策略

    返回:
        策略类列表
    """
    if strategy_type is None:
        return ALL_STRATEGIES
    return STRATEGY_GROUPS.get(strategy_type, [])
