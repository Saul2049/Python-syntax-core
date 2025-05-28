"""
数据分割模块 (Data Splitters Module)

提供数据集分割功能
"""

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


class DataSplitter:
    """数据分割器类"""

    @staticmethod
    def train_test_split(
        df: pd.DataFrame,
        test_size: float = 0.2,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        将数据分为训练集和测试集

        参数:
            df: 输入数据框
            test_size: 测试集比例
            shuffle: 是否随机打乱
            random_state: 随机种子

        返回:
            (训练集, 测试集)
        """
        if shuffle:
            if random_state is not None:
                np.random.seed(random_state)
            df = df.sample(frac=1).reset_index(drop=True)

        split_idx = int(len(df) * (1 - test_size))
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        return train_df, test_df

    @staticmethod
    def train_val_test_split(
        df: pd.DataFrame,
        train_size: float = 0.7,
        val_size: float = 0.15,
        test_size: float = 0.15,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        将数据分为训练集、验证集和测试集

        参数:
            df: 输入数据框
            train_size: 训练集比例
            val_size: 验证集比例
            test_size: 测试集比例
            shuffle: 是否随机打乱
            random_state: 随机种子

        返回:
            (训练集, 验证集, 测试集)
        """
        # 验证比例总和
        total_size = train_size + val_size + test_size
        if abs(total_size - 1.0) > 1e-6:
            raise ValueError(f"分割比例总和必须为1.0，当前为{total_size}")

        if shuffle:
            if random_state is not None:
                np.random.seed(random_state)
            df = df.sample(frac=1).reset_index(drop=True)

        # 计算分割点
        train_end = int(len(df) * train_size)
        val_end = train_end + int(len(df) * val_size)

        # 分割数据
        train_df = df.iloc[:train_end].copy()
        val_df = df.iloc[train_end:val_end].copy()
        test_df = df.iloc[val_end:].copy()

        return train_df, val_df, test_df

    @staticmethod
    def time_series_split(
        df: pd.DataFrame, n_splits: int = 5, test_size: Optional[int] = None
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        时间序列交叉验证分割

        参数:
            df: 输入数据框（应按时间排序）
            n_splits: 分割数量
            test_size: 测试集大小（如果为None，自动计算）

        返回:
            分割列表[(训练集, 测试集), ...]
        """
        if test_size is None:
            test_size = len(df) // (n_splits + 1)

        splits = []

        for i in range(n_splits):
            # 计算当前分割的训练集和测试集索引
            train_end = len(df) - (n_splits - i) * test_size
            test_start = train_end
            test_end = test_start + test_size

            # 确保不超出数据范围
            if test_end > len(df):
                test_end = len(df)

            if train_end <= 0 or test_start >= len(df):
                continue

            train_df = df.iloc[:train_end].copy()
            test_df = df.iloc[test_start:test_end].copy()

            splits.append((train_df, test_df))

        return splits

    @staticmethod
    def stratified_split(
        df: pd.DataFrame,
        target_column: str,
        test_size: float = 0.2,
        random_state: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        分层抽样分割（保持目标变量分布）

        参数:
            df: 输入数据框
            target_column: 目标列名
            test_size: 测试集比例
            random_state: 随机种子

        返回:
            (训练集, 测试集)
        """
        if target_column not in df.columns:
            raise ValueError(f"目标列 '{target_column}' 不存在")

        if random_state is not None:
            np.random.seed(random_state)

        train_dfs = []
        test_dfs = []

        # 按目标变量的唯一值分层采样
        for value in df[target_column].unique():
            value_df = df[df[target_column] == value]
            value_train, value_test = DataSplitter.train_test_split(
                value_df, test_size=test_size, shuffle=True, random_state=random_state
            )
            train_dfs.append(value_train)
            test_dfs.append(value_test)

        # 合并所有分层的结果
        train_df = pd.concat(train_dfs, ignore_index=True)
        test_df = pd.concat(test_dfs, ignore_index=True)

        # 重新打乱顺序
        train_df = train_df.sample(frac=1, random_state=random_state).reset_index(drop=True)
        test_df = test_df.sample(frac=1, random_state=random_state).reset_index(drop=True)

        return train_df, test_df

    @staticmethod
    def rolling_window_split(
        df: pd.DataFrame, window_size: int, step_size: int = 1
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        滚动窗口分割（用于时间序列回测）

        参数:
            df: 输入数据框
            window_size: 训练窗口大小
            step_size: 滚动步长

        返回:
            分割列表[(训练集, 测试集), ...]
        """
        splits = []

        for i in range(0, len(df) - window_size, step_size):
            train_start = i
            train_end = i + window_size
            test_start = train_end
            test_end = min(test_start + step_size, len(df))

            if test_start >= len(df):
                break

            train_df = df.iloc[train_start:train_end].copy()
            test_df = df.iloc[test_start:test_end].copy()

            splits.append((train_df, test_df))

        return splits


def create_train_test_split(
    df: pd.DataFrame, test_size: float = 0.2, shuffle: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    创建训练测试分割的便捷函数

    参数:
        df: 输入数据框
        test_size: 测试集比例
        shuffle: 是否打乱

    返回:
        (训练集, 测试集)
    """
    return DataSplitter.train_test_split(df, test_size, shuffle)
