#!/usr/bin/env python3
# improved_strategy.py - 改进策略模块

from typing import Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
import talib as ta


def simple_ma_cross(
    data: pd.DataFrame,
    short_window: int = 10,
    long_window: int = 50,
    column: str = "close",
) -> pd.DataFrame:
    """
    简单移动平均线交叉策略
    
    参数:
        data: 包含价格数据的DataFrame
        short_window: 短期移动平均窗口
        long_window: 长期移动平均窗口
        column: 用于计算移动平均的列名
    
    返回:
        包含信号的DataFrame
    """
    signals = pd.DataFrame(index=data.index)
    signals["signal"] = 0
    
    # 计算短期和长期移动平均线
    signals["short_ma"] = data[column].rolling(window=short_window).mean()
    signals["long_ma"] = data[column].rolling(window=long_window).mean()
    
    # 当短期移动平均线上穿长期移动平均线时买入
    signals.loc[
        (signals["short_ma"] > signals["long_ma"])
        & (signals["short_ma"].shift(1) <= signals["long_ma"].shift(1)),
        "signal",
    ] = 1
    
    # 当短期移动平均线下穿长期移动平均线时卖出
    signals.loc[
        (signals["short_ma"] < signals["long_ma"])
        & (signals["short_ma"].shift(1) >= signals["long_ma"].shift(1)),
        "signal",
    ] = -1
    
    return signals


def bollinger_breakout(
    data: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
    column: str = "close",
) -> pd.DataFrame:
    """
    布林带突破策略
    
    参数:
        data: 包含价格数据的DataFrame
        window: 移动平均窗口
        num_std: 标准差倍数
        column: 用于计算布林带的列名
    
    返回:
        包含信号的DataFrame
    """
    signals = pd.DataFrame(index=data.index)
    signals["signal"] = 0
    
    # 计算布林带
    signals["ma"] = data[column].rolling(window=window).mean()
    signals["std"] = data[column].rolling(window=window).std()
    signals["upper_band"] = signals["ma"] + (signals["std"] * num_std)
    signals["lower_band"] = signals["ma"] - (signals["std"] * num_std)
    
    # 当价格突破上轨时买入
    signals.loc[
        (data[column] > signals["upper_band"])
        & (data[column].shift(1) <= signals["upper_band"].shift(1)),
        "signal",
    ] = 1
    
    # 当价格跌破下轨时卖出
    signals.loc[
        (data[column] < signals["lower_band"])
        & (data[column].shift(1) >= signals["lower_band"].shift(1)),
        "signal",
    ] = -1
    
    return signals


def rsi_strategy(
    data: pd.DataFrame,
    window: int = 14,
    overbought: int = 70,
    oversold: int = 30,
    column: str = "close",
) -> pd.DataFrame:
    """
    RSI策略
    
    参数:
        data: 包含价格数据的DataFrame
        window: RSI计算窗口
        overbought: 超买阈值
        oversold: 超卖阈值
        column: 用于计算RSI的列名
    
    返回:
        包含信号的DataFrame
    """
    signals = pd.DataFrame(index=data.index)
    signals["signal"] = 0
    
    # 计算RSI
    signals["rsi"] = ta.RSI(data[column].values, timeperiod=window)
    
    # 当RSI从超卖区域上穿时买入
    signals.loc[
        (signals["rsi"] > oversold)
        & (signals["rsi"].shift(1) <= oversold),
        "signal",
    ] = 1
    
    # 当RSI从超买区域下穿时卖出
    signals.loc[
        (signals["rsi"] < overbought)
        & (signals["rsi"].shift(1) >= overbought),
        "signal",
    ] = -1
    
    return signals


def macd_strategy(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    column: str = "close",
) -> pd.DataFrame:
    """
    MACD策略
    
    参数:
        data: 包含价格数据的DataFrame
        fast_period: 快速EMA周期
        slow_period: 慢速EMA周期
        signal_period: 信号线周期
        column: 用于计算MACD的列名
    
    返回:
        包含信号的DataFrame
    """
    signals = pd.DataFrame(index=data.index)
    signals["signal"] = 0
    
    # 计算MACD
    macd, signal, hist = ta.MACD(
        data[column].values,
        fastperiod=fast_period,
        slowperiod=slow_period,
        signalperiod=signal_period,
    )
    
    signals["macd"] = macd
    signals["macd_signal"] = signal
    signals["macd_hist"] = hist
    
    # 当MACD线上穿信号线时买入
    signals.loc[
        (signals["macd"] > signals["macd_signal"])
        & (signals["macd"].shift(1) <= signals["macd_signal"].shift(1)),
        "signal",
    ] = 1
    
    # 当MACD线下穿信号线时卖出
    signals.loc[
        (signals["macd"] < signals["macd_signal"])
        & (signals["macd"].shift(1) >= signals["macd_signal"].shift(1)),
        "signal",
    ] = -1
    
    return signals


def improved_ma_cross(
    data: pd.DataFrame,
    short_window: int = 10,
    long_window: int = 50,
    rsi_window: int = 14,
    rsi_threshold: int = 50,
    volume_factor: float = 1.5,
    column: str = "close",
) -> pd.DataFrame:
    """
    改进版移动平均线交叉策略，结合RSI和成交量确认
    
    参数:
        data: 包含价格数据的DataFrame
        short_window: 短期移动平均窗口
        long_window: 长期移动平均窗口
        rsi_window: RSI计算窗口
        rsi_threshold: RSI确认阈值
        volume_factor: 成交量确认因子
        column: 用于计算移动平均的列名
    
    返回:
        包含信号的DataFrame
    """
    signals = pd.DataFrame(index=data.index)
    signals["signal"] = 0
    
    # 基础MA交叉策略
    signals["short_ma"] = data[column].rolling(window=short_window).mean()
    signals["long_ma"] = data[column].rolling(window=long_window).mean()
    
    # 计算RSI
    signals["rsi"] = ta.RSI(data[column].values, timeperiod=rsi_window)
    
    # 计算成交量移动平均
    if "volume" in data.columns:
        signals["volume_ma"] = data["volume"].rolling(
            window=short_window
        ).mean()
    else:
        # 如果没有成交量数据，将其设置为1，不影响信号
        data["volume"] = 1
        signals["volume_ma"] = 1
    
    # 买入条件：
    # 1. 短期MA上穿长期MA
    # 2. RSI > rsi_threshold (趋势确认)
    # 3. 成交量 > 成交量移动平均 * volume_factor (成交量确认)
    buy_condition = (
        (signals["short_ma"] > signals["long_ma"])
        & (signals["short_ma"].shift(1) <= signals["long_ma"].shift(1))
        & (signals["rsi"] > rsi_threshold)
        & (data["volume"] > signals["volume_ma"] * volume_factor)
    )
    
    signals.loc[buy_condition, "signal"] = 1
    
    # 卖出条件：
    # 1. 短期MA下穿长期MA
    # 2. RSI < rsi_threshold (趋势确认)
    sell_condition = (
        (signals["short_ma"] < signals["long_ma"])
        & (signals["short_ma"].shift(1) >= signals["long_ma"].shift(1))
        & (signals["rsi"] < rsi_threshold)
    )
    
    # 额外卖出条件：价格跌破长期MA (不需要RSI确认)
    additional_sell_condition = (
        (data[column] < signals["long_ma"]) &
        (data[column].shift(1) >= signals["long_ma"].shift(1))
    )
    
    signals.loc[sell_condition | additional_sell_condition, "signal"] = -1
    
    return signals


def trend_following_strategy(
    data: pd.DataFrame,
    ma_window: int = 20,
    atr_window: int = 14,
    atr_multiplier: float = 2.0,
    column: str = "close",
) -> pd.DataFrame:
    """
    趋势跟踪策略，基于ATR通道
    
    参数:
        data: 包含价格数据的DataFrame
        ma_window: 移动平均窗口
        atr_window: ATR计算窗口
        atr_multiplier: ATR乘数
        column: 用于计算的价格列名
    
    返回:
        包含信号的DataFrame
    """
    signals = pd.DataFrame(index=data.index)
    signals["signal"] = 0
    
    # 计算移动平均和ATR
    signals["ma"] = data[column].rolling(window=ma_window).mean()
    signals["atr"] = ta.ATR(
        data["high"].values,
        data["low"].values,
        data[column].values,
        timeperiod=atr_window,
    )
    
    # 计算上下通道
    signals["upper_band"] = signals["ma"] + (signals["atr"] * atr_multiplier)
    signals["lower_band"] = signals["ma"] - (signals["atr"] * atr_multiplier)
    
    # 上升趋势：价格突破上轨
    signals.loc[
        (data[column] > signals["upper_band"])
        & (data[column].shift(1) <= signals["upper_band"].shift(1)),
        "signal",
    ] = 1
    
    # 下降趋势：价格跌破下轨
    signals.loc[
        (data[column] < signals["lower_band"])
        & (data[column].shift(1) >= signals["lower_band"].shift(1)),
        "signal",
    ] = -1
    
    return signals


def multi_timeframe_strategy(
    data: pd.DataFrame,
    short_window: int = 10,
    long_window: int = 50,
    rsi_window: int = 14,
    column: str = "close",
    resample_rule: str = "4H",
) -> pd.DataFrame:
    """
    多时间框架策略，结合更高时间框架的趋势判断
    
    参数:
        data: 包含价格数据的DataFrame
        short_window: 短期移动平均窗口
        long_window: 长期移动平均窗口
        rsi_window: RSI计算窗口
        column: 用于计算的价格列名
        resample_rule: 高时间框架的重采样规则 (如 '4H', '1D')
    
    返回:
        包含信号的DataFrame
    """
    signals = pd.DataFrame(index=data.index)
    signals["signal"] = 0
    
    # 原始时间框架的指标
    signals["short_ma"] = data[column].rolling(window=short_window).mean()
    signals["long_ma"] = data[column].rolling(window=long_window).mean()
    signals["rsi"] = ta.RSI(data[column].values, timeperiod=rsi_window)
    
    # 更高时间框架的指标
    if isinstance(data.index, pd.DatetimeIndex):
        # 确保数据有正确的日期索引
        higher_frame = data.resample(resample_rule).agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        
        # 计算高时间框架趋势指标
        higher_frame["trend_ma"] = higher_frame[column].rolling(
            window=long_window // 4
        ).mean()
        higher_frame["trend"] = np.where(
            higher_frame[column] > higher_frame["trend_ma"], 1, -1
        )
        
        # 将高时间框架趋势映射回原始时间框架
        higher_trend = higher_frame["trend"].reindex(
            data.index, method="ffill"
        )
        signals["higher_trend"] = higher_trend
    else:
        # 如果索引不是时间索引，则简单地使用原始数据作为近似
        signals["higher_trend"] = np.where(
            data[column] > signals["long_ma"], 1, -1
        )
    
    # 生成买入信号：短期MA上穿长期MA，且更高时间框架趋势向上
    signals.loc[
        (signals["short_ma"] > signals["long_ma"])
        & (signals["short_ma"].shift(1) <= signals["long_ma"].shift(1))
        & (signals["higher_trend"] == 1),
        "signal",
    ] = 1
    
    # 生成卖出信号：短期MA下穿长期MA，且更高时间框架趋势向下
    signals.loc[
        (signals["short_ma"] < signals["long_ma"])
        & (signals["short_ma"].shift(1) >= signals["long_ma"].shift(1))
        & (signals["higher_trend"] == -1),
        "signal",
    ] = -1
    
    return signals


if __name__ == "__main__":
    # 加载数据
    try:
        data = pd.read_csv(
            "data/btc_eth.csv",
            index_col=0,
            parse_dates=True,
        )
    except FileNotFoundError:
        print("数据文件不存在，请确保 'data/btc_eth.csv' 文件存在")
        exit(1)
    
    # 计算指标和信号
    signals = improved_ma_cross(
        data,
        short_window=20,
        long_window=50,
        rsi_window=14,
        rsi_threshold=50,
        volume_factor=1.2,
    )
    
    # 展示最后20条信号
    print(signals.tail(20))
    
    # 统计买卖信号
    buy_signals = signals[signals["signal"] == 1].shape[0]
    sell_signals = signals[signals["signal"] == -1].shape[0]
    
    print(f"生成买入信号: {buy_signals}个")
    print(f"生成卖出信号: {sell_signals}个") 