"""
时间序列处理模块 (Time Series Processing Module)

提供时间序列数据预处理功能
"""

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


class TimeSeriesProcessor:
    """时间序列处理器类"""

    @staticmethod
    def create_sequences(
        data: np.ndarray, seq_length: int, pred_length: int = 1, step: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        为时间序列预测创建序列数据

        参数:
            data: 输入数据数组
            seq_length: 每个序列的长度（滑动窗口大小）
            pred_length: 预测长度
            step: 滑动步长

        返回:
            (X序列, Y目标值)
        """
        X, y = [], []

        for i in range(0, len(data) - seq_length - pred_length + 1, step):
            X.append(data[i : (i + seq_length)])
            y.append(data[i + seq_length : (i + seq_length + pred_length)])

        return np.array(X), np.array(y)

    @staticmethod
    def create_lagged_features(
        df: pd.DataFrame, columns: List[str], lags: List[int]
    ) -> pd.DataFrame:
        """
        创建滞后特征

        参数:
            df: 原始数据框
            columns: 要创建滞后特征的列名
            lags: 滞后期数列表

        返回:
            包含滞后特征的数据框
        """
        result_df = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            for lag in lags:
                result_df[f"{col}_lag_{lag}"] = df[col].shift(lag)

        return result_df

    @staticmethod
    def create_rolling_features(
        df: pd.DataFrame,
        columns: List[str],
        windows: List[int],
        functions: List[str] = ["mean", "std", "min", "max"],
    ) -> pd.DataFrame:
        """
        创建滚动窗口特征

        参数:
            df: 原始数据框
            columns: 要创建滚动特征的列名
            windows: 滚动窗口大小列表
            functions: 滚动函数列表

        返回:
            包含滚动特征的数据框
        """
        result_df = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            TimeSeriesProcessor._create_column_rolling_features(
                result_df, df, col, windows, functions
            )

        return result_df

    @staticmethod
    def _create_column_rolling_features(
        result_df: pd.DataFrame,
        source_df: pd.DataFrame,
        col: str,
        windows: List[int],
        functions: List[str],
    ):
        """为单个列创建滚动特征"""
        for window in windows:
            rolling = source_df[col].rolling(window=window)
            TimeSeriesProcessor._apply_rolling_functions(result_df, rolling, col, window, functions)

    @staticmethod
    def _apply_rolling_functions(
        result_df: pd.DataFrame, rolling, col: str, window: int, functions: List[str]
    ):
        """应用滚动函数"""
        # 定义函数映射表
        function_map = {
            "mean": rolling.mean,
            "std": rolling.std,
            "min": rolling.min,
            "max": rolling.max,
            "sum": rolling.sum,
            "median": rolling.median,
        }

        for func in functions:
            if func in function_map:
                feature_name = f"{col}_rolling_{window}_{func}"
                result_df[feature_name] = function_map[func]()

    @staticmethod
    def resample_data(
        df: pd.DataFrame, period: str, agg_methods: Optional[dict] = None
    ) -> pd.DataFrame:
        """
        重新采样时间序列数据

        参数:
            df: 输入数据框（需要有时间索引）
            period: 重采样周期 ('1H', '1D', '1W', '1M' 等)
            agg_methods: 聚合方法字典，键为列名，值为聚合函数

        返回:
            重新采样后的数据框
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("数据框必须有DatetimeIndex才能进行重采样")

        if agg_methods is None:
            # 默认聚合方法
            agg_methods = {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }

            # 对于其他数值列，使用mean
            for col in df.select_dtypes(include=[np.number]).columns:
                if col not in agg_methods:
                    agg_methods[col] = "mean"

        # 执行重采样
        resampled = df.resample(period).agg(agg_methods)

        # 去除空行
        resampled = resampled.dropna()

        return resampled

    @staticmethod
    def detect_outliers_iqr(data: pd.Series, multiplier: float = 1.5) -> pd.Series:
        """
        使用IQR方法检测异常值

        参数:
            data: 输入数据序列
            multiplier: IQR倍数阈值

        返回:
            布尔序列，True表示异常值
        """
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR

        return (data < lower_bound) | (data > upper_bound)

    @staticmethod
    def remove_outliers(
        df: pd.DataFrame, columns: List[str], method: str = "iqr", **kwargs
    ) -> pd.DataFrame:
        """
        移除异常值

        参数:
            df: 输入数据框
            columns: 要检测异常值的列名列表
            method: 异常值检测方法 ('iqr', 'zscore')
            **kwargs: 额外参数

        返回:
            移除异常值后的数据框
        """
        result_df = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            if method == "iqr":
                multiplier = kwargs.get("multiplier", 1.5)
                outliers = TimeSeriesProcessor.detect_outliers_iqr(df[col], multiplier=multiplier)
            elif method == "zscore":
                threshold = kwargs.get("threshold", 3.0)
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outliers = z_scores > threshold
            else:
                raise ValueError(f"不支持的异常值检测方法: {method}")

            # 移除异常值
            result_df = result_df[~outliers]

        return result_df


def create_sequences(
    data: np.ndarray, seq_length: int, pred_length: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    创建时间序列的便捷函数

    参数:
        data: 输入数据数组
        seq_length: 序列长度
        pred_length: 预测长度

    返回:
        (X序列, Y目标值)
    """
    return TimeSeriesProcessor.create_sequences(data, seq_length, pred_length)
