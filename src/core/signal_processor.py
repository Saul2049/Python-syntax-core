"""
信号处理模块 (Signal Processor Module)

提供交易信号生成和处理功能，包括：
- 移动平均线交叉信号
- 技术指标信号
- 信号过滤和验证
"""

import math
from typing import Any, Dict

import pandas as pd

from src.indicators import moving_average


def get_trading_signals(df: pd.DataFrame, fast_win: int = 7, slow_win: int = 25) -> Dict[str, Any]:
    """
    获取交易信号。
    Get trading signals.

    参数 (Parameters):
        df: 价格数据 (Price data)
        fast_win: 快线窗口 (Fast MA window)
        slow_win: 慢线窗口 (Slow MA window)

    返回 (Returns):
        Dict[str, Any]: 信号字典 (Signal dictionary)
    """
    # 计算移动平均线 (Calculate moving averages)
    df = df.copy()
    df["fast_ma"] = moving_average(df["close"], fast_win, kind="ema")
    df["slow_ma"] = moving_average(df["close"], slow_win, kind="ema")

    # 检查交叉 (Check crossover)
    df["prev_fast"] = df["fast_ma"].shift(1)
    df["prev_slow"] = df["slow_ma"].shift(1)

    # 金叉信号 (Golden cross signal)
    buy_signal = (df["prev_fast"] <= df["prev_slow"]) & (df["fast_ma"] > df["slow_ma"])

    # 死叉信号 (Death cross signal)
    sell_signal = (df["prev_fast"] >= df["prev_slow"]) & (df["fast_ma"] < df["slow_ma"])

    # 当前价格 (Current price)
    current_price = df["close"].iloc[-1]

    # 返回信号 (Return signals)
    return {
        "buy_signal": bool(buy_signal.iloc[-1]),
        "sell_signal": bool(sell_signal.iloc[-1]),
        "current_price": current_price,
        "fast_ma": df["fast_ma"].iloc[-1],
        "slow_ma": df["slow_ma"].iloc[-1],
        "last_timestamp": df.index[-1],
    }


def validate_signal(signal: Dict[str, Any], price_data: pd.DataFrame) -> bool:
    """
    验证交易信号的有效性。
    Validate trading signal.

    参数 (Parameters):
        signal: 交易信号字典 (Trading signal dictionary)
        price_data: 价格数据 (Price data)

    返回 (Returns):
        bool: 信号是否有效 (Whether signal is valid)
    """
    if not _validate_signal_basic_structure(signal):
        return False

    if not _validate_current_price(signal["current_price"]):
        return False

    if not _validate_moving_averages(signal):
        return False

    return True


def _validate_signal_basic_structure(signal: Dict[str, Any]) -> bool:
    """验证信号基础结构"""
    return bool(signal and "current_price" in signal)


def _validate_current_price(current_price: Any) -> bool:
    """验证当前价格的有效性"""
    try:
        if current_price <= 0 or not math.isfinite(current_price):
            return False
    except (TypeError, ValueError):
        # 处理复数、字符串等无法比较的类型
        return False
    return True


def _validate_moving_averages(signal: Dict[str, Any]) -> bool:
    """验证移动平均线的有效性"""
    if "fast_ma" not in signal or "slow_ma" not in signal:
        return True  # 如果没有MA数据，跳过验证

    fast_ma = signal["fast_ma"]
    slow_ma = signal["slow_ma"]
    current_price = signal["current_price"]

    try:
        if fast_ma <= 0 or slow_ma <= 0 or not math.isfinite(fast_ma) or not math.isfinite(slow_ma):
            return False

        # 检查价格与移动平均线的偏离度（不能偏离太大）
        price_deviation = abs(current_price - fast_ma) / fast_ma
        if price_deviation > 0.1:  # 10%偏离度限制
            return False
    except (TypeError, ValueError):
        # 处理无法计算的类型
        return False

    return True


def filter_signals(signals: Dict[str, Any], **filters) -> Dict[str, Any]:
    """
    过滤交易信号。
    Filter trading signals.

    参数 (Parameters):
        signals: 原始信号字典 (Original signal dictionary)
        **filters: 过滤条件 (Filter conditions)

    返回 (Returns):
        Dict[str, Any]: 过滤后的信号字典 (Filtered signal dictionary)
    """
    filtered_signals = signals.copy()

    # 最小价格过滤
    min_price = filters.get("min_price", 0)
    if signals.get("current_price", 0) < min_price:
        filtered_signals["buy_signal"] = False
        filtered_signals["sell_signal"] = False

    # 最大价格过滤
    max_price = filters.get("max_price", float("inf"))
    if signals.get("current_price", 0) > max_price:
        filtered_signals["buy_signal"] = False
        filtered_signals["sell_signal"] = False

    # 交易时间过滤
    trading_hours = filters.get("trading_hours")
    if trading_hours is not None and "last_timestamp" in signals:
        timestamp = signals["last_timestamp"]
        if timestamp is not None:
            hour = timestamp.hour
            if hour not in trading_hours:
                filtered_signals["buy_signal"] = False
                filtered_signals["sell_signal"] = False

    return filtered_signals
