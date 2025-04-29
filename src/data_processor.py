#!/usr/bin/env python3
# data_processor.py - 数据处理模块

import os
from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def load_data(file_path: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    从CSV文件加载数据

    参数:
        file_path: CSV文件路径
        columns: 要加载的列名列表（可选）

    返回:
        pandas DataFrame
    """
    try:
        if columns:
            df = pd.read_csv(file_path, usecols=columns)
        else:
            df = pd.read_csv(file_path)

        return df
    except FileNotFoundError:
        print(f"错误: 文件 '{file_path}' 不存在")
        return pd.DataFrame()
    except Exception as e:
        print(f"加载数据时出错: {str(e)}")
        return pd.DataFrame()


def process_ohlcv_data(df: pd.DataFrame, date_column: str = "date", fill_missing: bool = True) -> pd.DataFrame:
    """
    处理OHLCV (Open, High, Low, Close, Volume) 数据

    参数:
        df: 包含OHLCV数据的DataFrame
        date_column: 日期列名
        fill_missing: 是否填充缺失值

    返回:
        处理后的DataFrame
    """
    # 复制DataFrame以避免修改原始数据
    df_processed = df.copy()

    # 将日期列转换为datetime格式
    if date_column in df_processed.columns:
        df_processed[date_column] = pd.to_datetime(df_processed[date_column])

        # 设置日期列为索引
        df_processed.set_index(date_column, inplace=True)

        # 按日期排序
        df_processed.sort_index(inplace=True)

    # 填充缺失值
    if fill_missing:
        # 对于价格数据，使用前向填充
        price_columns = [
            col for col in df_processed.columns if any(x in col.lower() for x in ["open", "high", "low", "close"])
        ]
        if price_columns:
            df_processed[price_columns] = df_processed[price_columns].fillna(method="ffill")

        # 对于交易量数据，使用0填充
        volume_columns = [col for col in df_processed.columns if "volume" in col.lower()]
        if volume_columns:
            df_processed[volume_columns] = df_processed[volume_columns].fillna(0)

    return df_processed


def calculate_returns(prices: pd.Series, periods: int = 1, log_returns: bool = False) -> pd.Series:
    """
    计算价格收益率

    参数:
        prices: 价格时间序列
        periods: 计算收益率的周期数
        log_returns: 是否计算对数收益率

    返回:
        收益率时间序列
    """
    if log_returns:
        returns = np.log(prices / prices.shift(periods))
    else:
        returns = prices.pct_change(periods=periods)

    return returns


def add_technical_indicators(df: pd.DataFrame, price_column: str = "close") -> pd.DataFrame:
    """
    添加常用技术指标

    参数:
        df: 价格数据DataFrame
        price_column: 用于计算指标的价格列名

    返回:
        添加了技术指标的DataFrame
    """
    # 确保价格列存在
    if price_column not in df.columns:
        print(f"警告: 列 '{price_column}' 不存在于DataFrame中")
        return df

    # 复制DataFrame以避免修改原始数据
    df_with_indicators = df.copy()

    # 提取价格数据
    prices = df_with_indicators[price_column]

    # 计算移动平均线
    for window in [5, 10, 20, 50, 200]:
        df_with_indicators[f"MA_{window}"] = prices.rolling(window=window).mean()

    # 计算指数移动平均线
    for window in [5, 10, 20, 50, 200]:
        df_with_indicators[f"EMA_{window}"] = prices.ewm(span=window).mean()

    # 计算相对强弱指数 (RSI)
    window = 14
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    # 避免除以零
    avg_loss = avg_loss.replace(0, 0.000001)

    rs = avg_gain / avg_loss
    df_with_indicators["RSI_14"] = 100 - (100 / (1 + rs))

    # 计算布林带
    window = 20
    std_dev = 2

    rolling_mean = prices.rolling(window=window).mean()
    rolling_std = prices.rolling(window=window).std()

    df_with_indicators["BB_middle"] = rolling_mean
    df_with_indicators["BB_upper"] = rolling_mean + (rolling_std * std_dev)
    df_with_indicators["BB_lower"] = rolling_mean - (rolling_std * std_dev)

    # 计算MACD (移动平均收敛/发散)
    ema_12 = prices.ewm(span=12).mean()
    ema_26 = prices.ewm(span=26).mean()

    df_with_indicators["MACD_line"] = ema_12 - ema_26
    df_with_indicators["MACD_signal"] = df_with_indicators["MACD_line"].ewm(span=9).mean()
    df_with_indicators["MACD_histogram"] = df_with_indicators["MACD_line"] - df_with_indicators["MACD_signal"]

    return df_with_indicators


def calculate_volatility(prices: pd.Series, window: int = 20, trading_days: int = 252) -> pd.Series:
    """
    计算历史波动率

    参数:
        prices: 价格时间序列
        window: 计算窗口大小
        trading_days: 一年中的交易日数量

    返回:
        波动率时间序列
    """
    # 计算对数收益率
    log_returns = np.log(prices / prices.shift(1))

    # 计算滚动标准差
    rolling_std = log_returns.rolling(window=window).std()

    # 年化波动率
    annualized_vol = rolling_std * np.sqrt(trading_days)

    return annualized_vol


def normalize_data(
    data: Union[pd.DataFrame, pd.Series], feature_range: Tuple[int, int] = (0, 1)
) -> Union[pd.DataFrame, pd.Series]:
    """
    将数据规范化到指定范围

    参数:
        data: 要规范化的数据
        feature_range: 规范化范围元组 (min, max)

    返回:
        规范化后的数据
    """
    scaler = MinMaxScaler(feature_range=feature_range)

    if isinstance(data, pd.DataFrame):
        normalized_data = pd.DataFrame(scaler.fit_transform(data), columns=data.columns, index=data.index)
    else:  # pd.Series
        normalized_data = pd.Series(
            scaler.fit_transform(data.values.reshape(-1, 1)).flatten(),
            index=data.index,
        )

    return normalized_data


def create_train_test_split(
    df: pd.DataFrame, test_size: float = 0.2, shuffle: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    创建训练集和测试集

    参数:
        df: 要拆分的DataFrame
        test_size: 测试集大小比例
        shuffle: 是否打乱数据

    返回:
        (训练集DataFrame, 测试集DataFrame)
    """
    if shuffle:
        # 打乱索引
        shuffled_df = df.sample(frac=1).reset_index(drop=True)
    else:
        shuffled_df = df.copy()

    # 计算拆分点
    split_idx = int(len(shuffled_df) * (1 - test_size))

    # 拆分数据
    train_df = shuffled_df.iloc[:split_idx]
    test_df = shuffled_df.iloc[split_idx:]

    return train_df, test_df


def create_sequences(data: np.ndarray, seq_length: int, pred_length: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    """
    为时间序列预测创建序列数据

    参数:
        data: 输入数据数组
        seq_length: 每个序列的长度（滑动窗口大小）
        pred_length: 预测长度

    返回:
        (X序列, Y目标值)
    """
    X, y = [], []

    for i in range(len(data) - seq_length - pred_length + 1):
        X.append(data[i : (i + seq_length)])
        y.append(data[i + seq_length : (i + seq_length + pred_length)])

    return np.array(X), np.array(y)


def save_processed_data(df: pd.DataFrame, output_path: str, file_format: str = "csv") -> bool:
    """
    保存处理后的数据

    参数:
        df: 要保存的DataFrame
        output_path: 输出文件路径
        file_format: 文件格式 ('csv' 或 'pickle')

    返回:
        保存是否成功
    """
    try:
        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 根据文件格式保存数据
        if file_format.lower() == "csv":
            df.to_csv(output_path)
        elif file_format.lower() == "pickle":
            df.to_pickle(output_path)
        else:
            print(f"不支持的文件格式: {file_format}")
            return False

        print(f"数据已成功保存到 {output_path}")
        return True
    except Exception as e:
        print(f"保存数据时出错: {str(e)}")
        return False


def resample_data(data, period):
    """重采样数据

    Args:
        data: 原始数据
        period: 重采样周期

    Returns:
        重采样后的数据
    """
    if period == "1d":
        return data.resample("1D").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
    else:
        return data.resample(period).agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )


if __name__ == "__main__":
    # 示例用法
    # 加载数据
    df = load_data("btc_eth.csv")

    if not df.empty:
        # 处理OHLCV数据
        df_processed = process_ohlcv_data(df)

        # 添加技术指标
        df_with_indicators = add_technical_indicators(df_processed)

        # 计算波动率
        df_with_indicators["volatility_20"] = calculate_volatility(df_with_indicators["close"])

        # 保存处理后的数据
        save_processed_data(df_with_indicators, "output/processed_data.csv", "csv")

        print("数据处理完成!")
    else:
        print("无法加载数据，请检查输入文件.")
