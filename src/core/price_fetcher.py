"""
价格数据获取模块 (Price Data Fetcher Module)

提供从不同数据源获取价格数据的功能，包括：
- 实时市场数据获取
- 备用数据生成
- 数据格式化处理
"""

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.brokers.exchange import ExchangeClient


def fetch_price_data(symbol: str, exchange_client: Optional[ExchangeClient] = None) -> pd.DataFrame:
    """
    获取价格数据。
    Fetch price data.

    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        exchange_client: 交易所客户端实例 (Exchange client instance)

    返回 (Returns):
        pd.DataFrame: 价格数据 (Price data)
    """
    try:
        if exchange_client is None:
            # 创建默认的交易所客户端
            from src.brokers.binance import BinanceClient

            exchange_client = BinanceClient()

        # 获取最近的K线数据(例如最近100个1小时K线)
        klines = exchange_client.get_klines(symbol, interval="1h", limit=100)

        if not klines:
            raise Exception("无法获取K线数据")

        # 转换为DataFrame
        df = pd.DataFrame(
            klines,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "count",
                "taker_buy_volume",
                "taker_buy_quote_volume",
                "ignore",
            ],
        )

        # 转换数据类型
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df[["open", "high", "low", "close", "volume"]] = df[
            ["open", "high", "low", "close", "volume"]
        ].astype(float)

        # 设置时间戳为索引
        df.set_index("timestamp", inplace=True)

        # 只保留需要的列
        return df[["open", "high", "low", "close", "volume"]]

    except Exception as e:
        print(f"获取真实数据失败: {e}, 使用模拟数据")
        # 如果获取真实数据失败，则使用模拟数据作为备用
        return generate_fallback_data(symbol)


def generate_fallback_data(symbol: str) -> pd.DataFrame:
    """
    生成备用的模拟数据。
    Generate fallback mock data.

    参数 (Parameters):
        symbol: 交易对 (Trading pair)

    返回 (Returns):
        pd.DataFrame: 模拟价格数据 (Mock price data)
    """
    # 根据不同交易对设置不同的基准价格
    base_prices = {"BTCUSDT": 30000, "ETHUSDT": 2000, "BNBUSDT": 300, "ADAUSDT": 0.5, "SOLUSDT": 20}

    base_price = base_prices.get(symbol, 100)  # 默认价格

    # 生成模拟K线数据
    periods = 100
    timestamps = pd.date_range(end=datetime.now(), periods=periods, freq="1h")

    # 使用随机游走生成更真实的价格数据
    price_changes = np.random.normal(0, 0.01, periods)  # 1%的随机变动
    prices = [base_price]

    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, base_price * 0.5))  # 防止价格过低

    # 生成OHLC数据
    data = []
    for i, price in enumerate(prices):
        variation = abs(np.random.normal(0, 0.005))  # 0.5%的波动范围
        high = price * (1 + variation)
        low = price * (1 - variation)
        open_price = prices[i - 1] if i > 0 else price
        close_price = price
        volume = abs(np.random.normal(100, 20))

        data.append(
            {"open": open_price, "high": high, "low": low, "close": close_price, "volume": volume}
        )

    df = pd.DataFrame(data, index=timestamps)
    return df


def calculate_atr(df: pd.DataFrame, window: int = 14) -> float:
    """
    计算ATR值。
    Calculate ATR value.

    参数 (Parameters):
        df: 价格数据 (Price data)
        window: 计算窗口 (Calculation window)

    返回 (Returns):
        float: ATR值 (ATR value)
    """
    # 计算真实波幅 (Calculate true range)
    df = df.copy()
    df["tr0"] = abs(df["high"] - df["low"])
    df["tr1"] = abs(df["high"] - df["close"].shift())
    df["tr2"] = abs(df["low"] - df["close"].shift())
    df["tr"] = df[["tr0", "tr1", "tr2"]].max(axis=1)

    # 计算ATR (Calculate ATR)
    df["atr"] = df["tr"].rolling(window).mean()

    # 返回最新的ATR值 (Return latest ATR value)
    return df["atr"].iloc[-1]
