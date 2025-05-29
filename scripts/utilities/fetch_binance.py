#!/usr/bin/env python3
# fetch_binance.py
# 获取更长期(2年)的BTC和ETH历史价格数据

import time
from datetime import datetime, timedelta

import pandas as pd
import requests


def fetch_klines(
    symbol: str,
    interval: str = "1d",
    limit: int = 1000,
    start_time: int = None,
    end_time: int = None,
) -> pd.DataFrame:
    """
    从Binance API获取特定交易对的K线数据。

    支持开始时间和结束时间参数，便于分批获取长期数据。
    返回一个以open_time为索引、symbol为列名的DataFrame。
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}

    # 添加开始和结束时间参数（如果提供）
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time

    # 发送API请求
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # 如果没有数据返回空DataFrame
    if not data:
        return pd.DataFrame()

    # 解析API返回的数据
    df = pd.DataFrame(
        data,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "num_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ],
    )

    # 将时间戳转换为日期时间格式
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    df.set_index("open_time", inplace=True)

    # 仅保留收盘价并重命名为交易对的基础资产名称
    base = symbol.upper().replace("USDT", "").lower()
    df = df[["close"]].astype(float).rename(columns={"close": base})

    return df


def fetch_historical_data(symbol: str, interval: str = "1d", years: int = 2) -> pd.DataFrame:
    """
    获取多年的历史数据，通过多次API调用分批获取。

    参数:
        symbol: 交易对符号，如'BTCUSDT'
        interval: K线间隔，默认为'1d'（日线）
        years: 需要获取的历史数据年数，默认为2年

    返回:
        包含历史价格数据的DataFrame
    """
    # 计算开始和结束时间
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=365 * years)).timestamp() * 1000)

    # 存储所有数据的列表
    all_data = []

    # 每次请求最多获取1000条数据，循环获取所有需要的数据
    current_start = start_time

    print(f"开始获取 {symbol} 的历史数据...")

    while current_start < end_time:
        # 获取当前批次的数据
        df = fetch_klines(
            symbol,
            interval,
            limit=1000,
            start_time=current_start,
            end_time=end_time,
        )

        # 如果没有获取到数据，退出循环
        if df.empty:
            break

        # 将获取到的数据添加到列表
        all_data.append(df)

        # 更新下一批次的开始时间 (最后一条数据的收盘时间+1毫秒)
        current_start = int(df.index[-1].timestamp() * 1000) + 1

        # 显示进度
        date_str = df.index[-1].strftime("%Y-%m-%d")
        print(f"已获取到 {symbol} 截至 {date_str} 的数据")

        # 避免触发API限流
        time.sleep(1)

    # 如果没有获取到任何数据，返回空DataFrame
    if not all_data:
        return pd.DataFrame()

    # 合并所有批次的数据
    result = pd.concat(all_data)

    # 去重 (以防万一有重叠)
    result = result[~result.index.duplicated(keep="first")]

    # 按时间排序
    result.sort_index(inplace=True)

    print(f"完成 {symbol} 数据获取，共 {len(result)} 条记录")

    return result


if __name__ == "__main__":
    # 获取BTC和ETH的长期历史数据 (2年)
    btc = fetch_historical_data("BTCUSDT", years=2)
    eth = fetch_historical_data("ETHUSDT", years=2)

    # 合并数据
    df = pd.concat([btc, eth], axis=1)
    df.index.name = "date"  # 重命名索引以保持兼容性

    # 检查是否有缺失值，如有必要进行填充
    missing_btc = df["btc"].isna().sum()
    missing_eth = df["eth"].isna().sum()

    if missing_btc > 0 or missing_eth > 0:
        print(f"发现缺失值：BTC缺失{missing_btc}条，ETH缺失{missing_eth}条")
        # 使用前向填充处理缺失值
        df.ffill(inplace=True)

    # 保存到CSV文件
    filename = f"btc_eth_2yr_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename)
    print(f"已将{len(df)}天的BTC和ETH数据保存至 {filename}")

    # 同时保存一份基础文件名，便于代码使用
    df.to_csv("btc_eth.csv")
    print("同时已更新标准文件名 btc_eth.csv")
