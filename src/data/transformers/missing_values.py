"""
缺失值处理模块 (Missing Value Handlers Module)

提供缺失值检测和处理功能
"""

from typing import List, Optional

import numpy as np
import pandas as pd


class MissingValueHandler:
    """缺失值处理器类"""

    @staticmethod
    def fill_missing_values(
        df: pd.DataFrame, method: str = "forward", columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        填充缺失值

        参数:
            df: 输入数据框
            method: 填充方法 ('forward', 'backward', 'mean', 'median', 'mode', 'zero')
            columns: 要处理的列名列表（None表示所有列）

        返回:
            填充后的数据框
        """
        result_df = df.copy()

        if columns is None:
            columns = df.columns.tolist()

        for col in columns:
            if col not in df.columns:
                continue

            MissingValueHandler._apply_fill_method(result_df, col, method)

        return result_df

    @staticmethod
    def _apply_fill_method(result_df: pd.DataFrame, col: str, method: str):
        """应用填充方法到指定列"""
        # 定义填充方法映射表
        fill_methods = {
            "forward": lambda df, col: df[col].ffill(),
            "backward": lambda df, col: df[col].bfill(),
            "zero": lambda df, col: df[col].fillna(0),
        }

        # 需要数值类型检查的方法
        numeric_methods = {
            "mean": lambda df, col: df[col].fillna(df[col].mean()),
            "median": lambda df, col: df[col].fillna(df[col].median()),
        }

        if method in fill_methods:
            result_df[col] = fill_methods[method](result_df, col)
        elif method in numeric_methods and result_df[col].dtype in ["int64", "float64"]:
            result_df[col] = numeric_methods[method](result_df, col)
        elif method == "mode":
            MissingValueHandler._apply_mode_fill(result_df, col)
        else:
            raise ValueError(f"不支持的填充方法: {method}")

    @staticmethod
    def _apply_mode_fill(result_df: pd.DataFrame, col: str):
        """应用众数填充"""
        mode_value = result_df[col].mode()
        if len(mode_value) > 0:
            result_df[col] = result_df[col].fillna(mode_value[0])

    @staticmethod
    def interpolate_missing_values(
        df: pd.DataFrame, method: str = "linear", columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        插值填充缺失值

        参数:
            df: 输入数据框
            method: 插值方法 ('linear', 'time', 'spline', 'polynomial')
            columns: 要处理的列名列表（None表示所有数值列）

        返回:
            插值后的数据框
        """
        result_df = df.copy()

        if columns is None:
            # 只对数值列进行插值
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if col not in df.columns:
                continue

            if result_df[col].dtype not in ["int64", "float64"]:
                continue

            MissingValueHandler._apply_interpolation_method(result_df, col, method)

        return result_df

    @staticmethod
    def _apply_interpolation_method(result_df: pd.DataFrame, col: str, method: str):
        """应用插值方法到指定列"""
        interpolation_methods = {
            "linear": lambda df, col: df[col].interpolate(method="linear"),
            "time": lambda df, col: MissingValueHandler._time_interpolate(df, col),
            "spline": lambda df, col: MissingValueHandler._safe_interpolate(
                df, col, "spline", order=3
            ),
            "polynomial": lambda df, col: MissingValueHandler._safe_interpolate(
                df, col, "polynomial", order=2
            ),
        }

        if method in interpolation_methods:
            result_df[col] = interpolation_methods[method](result_df, col)
        else:
            raise ValueError(f"不支持的插值方法: {method}")

    @staticmethod
    def _time_interpolate(result_df: pd.DataFrame, col: str):
        """执行时间插值"""
        if isinstance(result_df.index, pd.DatetimeIndex):
            return result_df[col].interpolate(method="time")
        else:
            return result_df[col].interpolate(method="linear")

    @staticmethod
    def _safe_interpolate(result_df: pd.DataFrame, col: str, method: str, **kwargs):
        """安全执行插值，失败时回退到线性插值"""
        try:
            return result_df[col].interpolate(method=method, **kwargs)
        except ValueError:
            # 如果插值失败，回退到线性插值
            return result_df[col].interpolate(method="linear")

    @staticmethod
    def detect_missing_patterns(df: pd.DataFrame) -> pd.DataFrame:
        """
        检测缺失值模式

        参数:
            df: 输入数据框

        返回:
            缺失值统计信息
        """
        # 处理空DataFrame情况
        if df.empty or len(df.columns) == 0:
            return pd.DataFrame(columns=["column", "missing_count", "missing_percent", "data_type"])

        missing_info = []

        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_percent = (missing_count / len(df)) * 100 if len(df) > 0 else 0.0

            missing_info.append(
                {
                    "column": col,
                    "missing_count": missing_count,
                    "missing_percent": missing_percent,
                    "data_type": str(df[col].dtype),
                }
            )

        result_df = pd.DataFrame(missing_info)
        if not result_df.empty:
            result_df = result_df.sort_values("missing_percent", ascending=False)
        return result_df

    @staticmethod
    def remove_missing_rows(
        df: pd.DataFrame, threshold: float = 0.5, columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        移除包含过多缺失值的行

        参数:
            df: 输入数据框
            threshold: 缺失值比例阈值（0-1）
            columns: 要考虑的列名列表（None表示所有列）

        返回:
            清理后的数据框
        """
        if columns is None:
            columns = df.columns.tolist()

        # 计算每行在指定列中的缺失值比例
        subset_df = df[columns]
        missing_ratio = subset_df.isnull().sum(axis=1) / len(columns)

        # 保留缺失值比例低于阈值的行
        keep_mask = missing_ratio < threshold

        return df[keep_mask].copy()

    @staticmethod
    def remove_missing_columns(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
        """
        移除包含过多缺失值的列

        参数:
            df: 输入数据框
            threshold: 缺失值比例阈值（0-1）

        返回:
            清理后的数据框
        """
        # 计算每列的缺失值比例
        missing_ratio = df.isnull().sum() / len(df)

        # 保留缺失值比例低于阈值的列
        keep_columns = missing_ratio[missing_ratio < threshold].index.tolist()

        return df[keep_columns].copy()

    @staticmethod
    def fill_with_groups(
        df: pd.DataFrame, group_columns: List[str], target_columns: List[str], method: str = "mean"
    ) -> pd.DataFrame:
        """
        按组填充缺失值

        参数:
            df: 输入数据框
            group_columns: 分组列
            target_columns: 要填充的目标列
            method: 填充方法 ('mean', 'median', 'mode')

        返回:
            填充后的数据框
        """
        result_df = df.copy()

        for target_col in target_columns:
            if target_col not in df.columns:
                continue

            if method == "mean" and result_df[target_col].dtype in ["int64", "float64"]:
                fill_values = result_df.groupby(group_columns)[target_col].transform("mean")
            elif method == "median" and result_df[target_col].dtype in ["int64", "float64"]:
                fill_values = result_df.groupby(group_columns)[target_col].transform("median")
            elif method == "mode":
                fill_values = result_df.groupby(group_columns)[target_col].transform(
                    lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
                )
            else:
                continue

            # 填充缺失值
            mask = result_df[target_col].isnull()
            result_df.loc[mask, target_col] = fill_values[mask]

        return result_df

    @staticmethod
    def get_missing_summary(df: pd.DataFrame) -> dict:
        """
        获取数据框的缺失值摘要

        参数:
            df: 输入数据框

        返回:
            缺失值摘要字典
        """
        total_cells = df.shape[0] * df.shape[1]
        total_missing = df.isnull().sum().sum()

        # 处理空DataFrame的情况
        if total_cells == 0:
            missing_percentage = 0.0
        else:
            missing_percentage = (total_missing / total_cells) * 100

        # 找出包含缺失值的列名列表
        columns_with_missing = df.columns[df.isnull().any()].tolist()

        return {
            "total_rows": df.shape[0],
            "total_columns": df.shape[1],
            "total_cells": total_cells,
            "total_missing": int(total_missing),  # 确保返回int类型
            "missing_percentage": float(missing_percentage),  # 确保返回float类型
            "complete_rows": df.dropna().shape[0],
            "columns_with_missing": columns_with_missing,  # 返回列名列表而不是计数
            "columns_all_missing": int((df.isnull().all()).sum()),  # 确保返回int类型
        }
