"""
数据归一化模块 (Data Normalizers Module)

提供数据归一化和标准化功能
"""

from typing import Tuple, Union

import pandas as pd

# 可选导入sklearn
try:
    from sklearn.preprocessing import MinMaxScaler, StandardScaler

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class DataNormalizer:
    """数据归一化器类"""

    def __init__(self, method: str = "minmax", feature_range: Tuple[float, float] = (0, 1)):
        """
        初始化数据归一化器

        参数:
            method: 归一化方法 ('minmax', 'standard', 'robust')
            feature_range: MinMax归一化的范围
        """
        self.method = method.lower()
        self.feature_range = feature_range
        self.scaler = None
        self._initialize_scaler()

    def _initialize_scaler(self):
        """初始化归一化器"""
        if not HAS_SKLEARN:
            print("⚠️ 警告: sklearn未安装，使用简化实现")
            self.scaler = None
            return

        if self.method == "minmax":
            self.scaler = MinMaxScaler(feature_range=self.feature_range)
        elif self.method == "standard":
            self.scaler = StandardScaler()
        elif self.method == "robust":
            from sklearn.preprocessing import RobustScaler

            self.scaler = RobustScaler()
        else:
            raise ValueError(f"不支持的归一化方法: {self.method}")

    def fit_transform(self, data: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
        """
        训练并转换数据

        参数:
            data: 要归一化的数据

        返回:
            归一化后的数据
        """
        if not HAS_SKLEARN:
            return self._simple_normalize(data)

        if isinstance(data, pd.DataFrame):
            normalized_data = pd.DataFrame(
                self.scaler.fit_transform(data), columns=data.columns, index=data.index
            )
        else:  # pd.Series
            normalized_data = pd.Series(
                self.scaler.fit_transform(data.values.reshape(-1, 1)).flatten(),
                index=data.index,
                name=data.name,
            )

        return normalized_data

    def _simple_normalize(
        self, data: Union[pd.DataFrame, pd.Series]
    ) -> Union[pd.DataFrame, pd.Series]:
        """简化的归一化实现（不使用sklearn）"""
        if self.method == "minmax":
            min_val = data.min()
            max_val = data.max()
            normalized = (data - min_val) / (max_val - min_val)
            # 缩放到指定范围
            return (
                normalized * (self.feature_range[1] - self.feature_range[0]) + self.feature_range[0]
            )
        elif self.method == "standard":
            return (data - data.mean()) / data.std()
        else:
            raise ValueError(f"简化实现不支持方法: {self.method}")

    def transform(self, data: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
        """
        使用已训练的归一化器转换数据

        参数:
            data: 要转换的数据

        返回:
            转换后的数据
        """
        if not HAS_SKLEARN:
            return self._simple_normalize(data)

        if self.scaler is None:
            raise ValueError("归一化器未训练，请先调用fit_transform方法")

        if isinstance(data, pd.DataFrame):
            normalized_data = pd.DataFrame(
                self.scaler.transform(data), columns=data.columns, index=data.index
            )
        else:  # pd.Series
            normalized_data = pd.Series(
                self.scaler.transform(data.values.reshape(-1, 1)).flatten(),
                index=data.index,
                name=data.name,
            )

        return normalized_data

    def inverse_transform(
        self, data: Union[pd.DataFrame, pd.Series]
    ) -> Union[pd.DataFrame, pd.Series]:
        """
        反向转换数据

        参数:
            data: 已归一化的数据

        返回:
            原始尺度的数据
        """
        if not HAS_SKLEARN:
            print("⚠️ 警告: 简化实现不支持inverse_transform")
            return data

        if self.scaler is None:
            raise ValueError("归一化器未训练")

        if isinstance(data, pd.DataFrame):
            original_data = pd.DataFrame(
                self.scaler.inverse_transform(data), columns=data.columns, index=data.index
            )
        else:  # pd.Series
            original_data = pd.Series(
                self.scaler.inverse_transform(data.values.reshape(-1, 1)).flatten(),
                index=data.index,
                name=data.name,
            )

        return original_data


def normalize_data(
    data: Union[pd.DataFrame, pd.Series],
    method: str = "minmax",
    feature_range: Tuple[float, float] = (0, 1),
) -> Union[pd.DataFrame, pd.Series]:
    """
    快速归一化数据的便捷函数

    参数:
        data: 要归一化的数据
        method: 归一化方法
        feature_range: 特征范围

    返回:
        归一化后的数据
    """
    normalizer = DataNormalizer(method=method, feature_range=feature_range)
    return normalizer.fit_transform(data)
